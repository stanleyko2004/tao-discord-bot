import discord
from discord.ext import commands

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_commands()

    def setup_commands(self):
        @self.bot.tree.command(name="greet", description="Greet the bot")
        async def greet(self, interaction: discord.Interaction):
            await interaction.response.send_message("Hello, how can I help you?")

# When adding the cog to the bot, call the setup_commands method
async def setup(bot):
    await bot.add_cog(MyCog(bot))