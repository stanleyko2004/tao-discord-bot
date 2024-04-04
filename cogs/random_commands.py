from datetime import datetime
import re
from typing import List
import discord
from discord.ext import commands
from discord import app_commands
from pymongo import database

from utils import is_admin


class RandomCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: database.Database = bot.get_cog("DBCog").db
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("RandomCog is ready.")
    
    @app_commands.command(name="set_start")
    @app_commands.describe(start_date="Set the start of the competition in the format YYYY-MM-DD")
    async def set_start_slash(self, interaction: discord.Interaction, start_date: str):
        try:
            date = datetime.strptime(start_date, "%Y-%m-%d")
            if not is_admin(interaction.user):
                await interaction.response.send_message(f"You are not an admin!")
                return
            
            self.db.data.update_one({"name": "start_week"}, {"$set": {"date": date}}, upsert=True)
            await interaction.response.send_message(f"Start week set to {start_date}!")
        except Exception as e:
            print(f"Error: {e}")
    
    
    @app_commands.command(name="set_end")
    @app_commands.describe(end_date="Set the end of the competition in the format YYYY-MM-DD")
    async def set_start_slash(self, interaction: discord.Interaction, end_date: str):
        try:
            date = datetime.strptime(end_date, "%Y-%m-%d")
            if not is_admin(interaction.user):
                await interaction.response.send_message(f"You are not an admin!")
                return
            
            self.db.data.update_one({"name": "end_week"}, {"$set": {"date": date}}, upsert=True)
            await interaction.response.send_message(f"End week set to {end_date}!")
        except Exception as e:
            print(f"Error: {e}")
            
    @app_commands.command(name="help")
    @app_commands.describe(members="members")
    async def help(self, interaction: discord.Interaction, members: str = None):    
        try:
            help_embed = discord.Embed(title="Help Page", color=0xf8d980)
            help_embed.add_field(name="Family Commands", value=f"""
            `/fam_create` creates a family
            `/fam_invite` invites a user to a family
            `/fam_leave` leaves a family
            `/fam_join` joins a family (if invited)
            `/fam_info` displays information about a family
            `/fam_leaderboard` displays the leaderboard
            `/fam_score` displays the score of a family""", inline=False)
            help_embed.add_field(name="Mission Commands", value=f"""
            `/list_missions` lists all missions
            `/submit_mission` submits a mission for verification
            """, inline=False)
            help_embed.add_field(name="Mystery Box Commands", value=f"""
            `/use_mystery_box` uses a mystery box
            `/check_inventory` checks your inventory
            """, inline=False)
            help_embed.add_field(name="Other Commands", value=f"""
            `/help` displays this message
            """, inline=False)

            await interaction.response.send_message(embed=help_embed)
        except Exception as e:
            print(f"Error: {e}")
    
async def setup(bot):
    await bot.add_cog(RandomCog(bot))
