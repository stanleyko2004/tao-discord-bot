import os
from typing import List
import discord
from discord.ext import commands
from discord import app_commands
from pymongo.server_api import ServerApi
from pymongo import MongoClient, database

from views import PaginatorView
from tao_types import Family
from utils import await_and_raise_error, has_family, id_to_name, pull_invites


class FamilyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: database.Database = bot.get_cog("DBCog").db
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("FamilyCog is ready.")

    @app_commands.command(name="slash", description="test slash command")
    async def ping(self, interaction: discord.Interaction):
        print("ping")
        await interaction.response.send_message(f"Pong!")

    @app_commands.command(name="fam_create")
    @app_commands.describe(family="family name")
    async def create_fam(self, interaction: discord.Interaction, family: str):
        try:
            author_id: str = str(interaction.user.id)

            # Check if author already has a family
            if has_family(author_id, self.db):
                await await_and_raise_error(interaction, f"{id_to_name(interaction, author_id)} is already in a family, cannot create a new one.")

            
            # Check if family name already exists
            response = self.db.families.find_one({"name": family})
            if not response is None:
                await await_and_raise_error(interaction, f"Family {family} already exists!")

            # Create new family
            new_family: Family = {
                'name': family,
                'members': [author_id],
                'points': 0,
                'completed_missions': [],
                'inventory': [],
                'invited': [],
            }

            self.db.families.insert_one(new_family)

            pull_invites(author_id, self.db)

            await interaction.response.send_message(f"Family {family} created!")

        except Exception as e:
            print(f"Error: {e}")
            
    # Inviting # verified
    @app_commands.command(name="fam_invite")
    @app_commands.describe(invitee="invitee id")
    async def fam_invite_slash(self, interaction: discord.Interaction, invitee: discord.member.Member):
        try:
            author_id: str = str(interaction.user.id)
            author_name: str = interaction.user.name
            invitee_id: str = str(invitee.id)
            invitee_name: str = invitee.name
            
            # Check if author is inviting themselves
            if author_id == invitee_id:
                await await_and_raise_error(interaction, f"You cannot invite yourself to a family.")
            
            # Check if invitee already has a family
            if has_family(invitee_id, self.db):
                await await_and_raise_error(interaction, f"{invitee_name} is already in a family.")
            
            # Check if author is in family or not
            if not has_family(author_id, self.db):
                await await_and_raise_error(interaction, f"{author_name} is not currently in a family, {author_name} cannot invite someone else to a family")
            
            # Attempt to invite to family
            response: Family = self.db.families.find_one({'members': {'$in': [author_id]}})
            family_name: str = response['name']
            if invitee_id in response["invited"]:
                await await_and_raise_error(interaction, f"{invitee_name} has already been invited to {family_name}!")
            else:
                self.db.families.update_one({'name': family_name}, {'$addToSet': {'invited': invitee_id}})
                await interaction.response.send_message(f"{invitee_name} successfully invited to {family_name}!")

        except Exception as e:
            print(f"Error: {e}")


    # Leaving # verified
    @app_commands.command(name="fam_leave")
    async def fam_leave_slash(self, interaction: discord.Interaction):
        try:
            author_id: str= str(interaction.user.id)
            author_name: str = str(interaction.user.name)
            response: Family = self.db.families.find_one({'members': {'$in': [author_id]}})

            if response is None:
                await await_and_raise_error(interaction, f"You are not currently in a family.")
            else:
                update_response: Family = self.db.families.update_one({'name': response['name']}, {'$pull': {'members': author_id}})
                if (update_response.modified_count == 1):
                    await interaction.response.send_message(f"{author_name} has left {response['name']}.")
                    return
                else:
                    await await_and_raise_error(interaction, "Something went wrong :(")

        except Exception as e:
            print(f"Error: {e}")


    # Joining # verified
    @app_commands.command(name="fam_join")
    @app_commands.describe(family="family name")
    async def fam_join_slash(self, interaction: discord.Interaction, family: str):
        try:
            author_id: str = str(interaction.user.id)
            author_name: str = interaction.user.name
            
            # Check if user is invited to family specified
            response: Family = self.db.families.find_one({'name': family, 'invited': {'$in': [author_id]}})
            if not response is None:
                # Add user to family, remove invite from all families
                self.db.families.update_one({'name': family}, {'$addToSet': {'members': author_id}})
                pull_invites(author_id, self.db)
                await interaction.response.send_message(f"{author_name} has joined {family}!")
            else:
                await await_and_raise_error(interaction, f"You have not been invited to {family}.")

        except Exception as e:
            print(f"Error: {e}")
            
    @app_commands.command(name="fam_info")
    @app_commands.describe(family="family name")
    async def fam_info_slash(self, interaction: discord.Interaction, family: str):
        try:
            response: Family = self.db.families.find_one({'name': family})
            if response is None:
                raise Exception(f"Family {family} does not exist.")
            else:
                name: str = response['name']
                points: int = response['points']
                member_names: List[str] = []
                for member_id in response['members']:
                    name: str = id_to_name(interaction, member_id)
                    if name != False:
                        member_names.append(name)
                members_str: str = ', '.join(member_names)
                embed: discord.Embed = discord.Embed(title=name, description='family description', color=0xf8d980)
                embed.add_field(name='Members', value=members_str, inline=False)
                embed.add_field(name='Points', value=points, inline=False)
                embed.set_footer(text='footer text')
                await interaction.response.send_message(embed=embed)

        except Exception as e:
            print(f"Error: {e}")
            
    @app_commands.command(name="fam_leaderboard")
    async def fam_leaderboard_slash(self, interaction: discord.Interaction):
        try:
            response = self.db.families.find().sort({'score': 1})

            families: List[Family] = list(response)
            embeds: List[discord.Embed] = []

            for f in range(len(families)):
                family: Family = families[f]

                # Create new page for more families
                if (f % 5 == 0):
                    embeds.append(discord.Embed(title="Fam Leaderboard", color=0xf8d980))

                # Add family and their score as a row
                embeds[-1].add_field(name=f"{f+1}.{family['name']}: {family['points']}", value="", inline=False)

            pages: PaginatorView = PaginatorView(embeds)
            await interaction.response.send_message(embed=await pages.initial, view=pages)

        except Exception as e:
            print(f"Error: {e}")
            
    @app_commands.command(name="fam_score")
    @app_commands.describe(family="family name")
    async def fam_score_slash(self, interaction: discord.Interaction, family: str=""):
        try:
            response: Family = self.db.families.find_one({'name': family})
            if response is None:
                await await_and_raise_error(interaction, f"{family} does not exist!")
            else:
                await interaction.response.send_message(f"{family} currently has {response['points']} points!")

        except Exception as e:
            print(f"Error: {e}")

# When adding the cog to the bot, call the setup_commands method
async def setup(bot):
    await bot.add_cog(FamilyCog(bot))