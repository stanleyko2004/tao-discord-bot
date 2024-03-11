import os
import asyncio

from discord.ext import commands
import discord

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith("py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    async with bot:
        await load()
        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())