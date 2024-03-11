import os
from discord.ext import commands
from pymongo.server_api import ServerApi
from pymongo import MongoClient, database

class DBCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        uri = os.getenv("MONGO_URI")
        client = MongoClient(uri, server_api=ServerApi('1'))
        db_name = os.getenv("DB_NAME")
        db: database.Database = client[db_name]
        self.db = db
        self.ping_mongo()

    @commands.Cog.listener()
    async def on_ready(self):
        print("DBCog is ready.")

    def ping_mongo(self):
        try:
            self.db.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)

# When adding the cog to the bot, call the setup_commands method
async def setup(bot):
    await bot.add_cog(DBCog(bot))