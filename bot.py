import os
import asyncio

from discord.ext import commands
import discord

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith("py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    async with bot:
        await load()
        await bot.start(BOT_TOKEN)

@bot.event
async def on_ready():
    try:
        # slash commands
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")

        # Confirming bot is running
        channel = bot.get_channel(CHANNEL_ID)
        await channel.send("TAO bot is ready!")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    asyncio.run(main())