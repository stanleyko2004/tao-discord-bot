import os
import re
from typing import List
import discord
from discord.ext import commands
from discord import app_commands
from pymongo.server_api import ServerApi
from pymongo import MongoClient, database

from views import PaginatorView
from tao_types import Mission
from utils import await_and_raise_error, get_global_mission, has_family, is_admin, weeks_since_start


class MissionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        uri = os.getenv("MONGO_URI")
        client = MongoClient(uri, server_api=ServerApi('1'))
        db_name = os.getenv("DB_NAME")
        self.db: database.Database = client[db_name]
    
    @app_commands.command(name="fam_missions")
    async def fam_missions_slash(self, interaction: discord.Interaction):
        try:
            response: List[Mission] = list(self.db.missions.find({"mission_type": "global", "week": weeks_since_start()}))

            # Put all missions into their own embed
            embeds: List[discord.Embed] = []

            for i in range(len(response)):
                if (i%10 == 0):
                    embeds.append(discord.Embed(title="Missions", color=0xf8d980))
                mission: Mission = response[i]
                embeds[-1].add_field(name=mission['name'], value=f"Points: {mission['points']}\n{mission['description']}", inline=False)
                
            # Place mission embeds into paginator and display the initial page
            missions: discord.ui.view = PaginatorView(embeds)
            await interaction.response.send_message(embed=await missions.initial, view=missions)

        except Exception as e:
            print(f"Error: {e}")

    @app_commands.command(name="add_mission")
    @app_commands.describe(name="name of mission", description="description of mission", points="can be +2, x2, -1, etc...")
    async def add_mission_slash(self, interaction: discord.Interaction, name: str, description: str, points: str):
        try:
            if not is_admin(interaction.user):
                await interaction.response.send_message(f"You are not an admin!")
                return
            
            mission: Mission = {
                "name": name,
                "mission_type": "global",
                "week": 0,
                "description": description,
                "operator": points[0],
                "points": int(points[1:])
            }
            self.db.missions.insert_one(mission)
            await interaction.response.send_message(f"{name} has been added!")
        except Exception as e:
            print(f"Error: {e}")


    @app_commands.command(name="submit_mission")
    @app_commands.describe(name="mission name")
    async def submit_mission(self, interaction: discord.Interaction, name: str):
        try:
            response: Mission = self.db.missions.find_one({name: name})
            if (response is None):
                await_and_raise_error(interaction, f"{name} is not a mission")
            
            if not has_family(str(interaction.user.id), self.db):
                await_and_raise_error(interaction, f"You are not in a family!")
            
            family = self.db.families.find_one({'members': {'$in': [str(interaction.user.id)]}})
            await interaction.response.send_message(f"Mission submitted! Waiting for verification for {name} mission for week {weeks_since_start()} for family {family['name']}!")
        except Exception as e:
            print(f"Error: {e}")

    # for admins verifying missions
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        try:
            print("reaction added")
            pattern = r"^Mission submitted! Waiting for verification for (\w+) mission for week (\d+) for family (\w+)!$" 
            message: discord.Message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            guild: discord.Guild = self.bot.get_guild(payload.guild_id)
            member: discord.Member = guild.get_member(payload.user_id)
            if not is_admin(member):
                print("not admin")
                return
            
            match = re.search(pattern, message.content)
            if not match:
                return
            
            name = match.group(1)
            week = int(match.group(2))
            family = match.group(3)
            print(name, week, family)
            mission: Mission = get_global_mission(name, week, self.db)
            if (mission is None):
                print(f"could not find mission {name}")
                return
            self.db.families.update_one({'name': family}, {'$addToSet': {'completed_missions': mission['_id']}})
        except Exception as e:
            print(f"Error: {e}")

# When adding the cog to the bot, call the setup_commands method
async def setup(bot):
    await bot.add_cog(MissionsCog(bot))