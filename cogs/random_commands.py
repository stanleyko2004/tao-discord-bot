from datetime import datetime
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
    
async def setup(bot):
    await bot.add_cog(RandomCog(bot))