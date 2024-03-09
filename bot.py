import discord
from discord.ext import commands
from discord import app_commands

class MyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.group = app_commands.Group(name="parent", description="This is a parent command group")
        self.bot.tree.add_command(self.group)

    @app_commands.command(name="top-command")
    async def my_top_command(self, interaction: discord.Interaction):
        """Top-level command outside the group"""
        await interaction.response.send_message("Hello from top-level command!", ephemeral=True)

    @self.group.command(name="sub-command")
    async def my_sub_command(self, interaction: discord.Interaction):
        """Sub-command within the group"""
        await interaction.response.send_message("Hello from the sub-command!", ephemeral=True)

class DiscBot(commands.Bot):
    async def on_ready(self):
        try:
            synced = await self.bot.tree.sync()
            print(f"Synced {len(synced)} command(s)")
            channel = self.bot.get_channel(self.CHANNEL_ID)
            await channel.send("TAO bot is ready!")
        except Exception as e:
            print(e)

bot = DiscBot()