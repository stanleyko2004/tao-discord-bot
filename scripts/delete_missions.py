import os

from dotenv import load_dotenv
from pymongo import MongoClient, database
from pymongo.server_api import ServerApi

load_dotenv()

uri = os.getenv("MONGO_URI")
client = MongoClient(uri, server_api=ServerApi('1'))
db_name = os.getenv("DB_NAME")
db: database.Database = client[db_name]

# delete all missions
db.missions.delete_many({})

# delete all missions in families
db.families.update_many({}, {"$set": {"completed_missions": []}})