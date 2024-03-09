from dotenv import load_dotenv
load_dotenv()
import os

# Database Stuff
from pymongo import MongoClient

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
uri = os.getenv("MONGO_URI")
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db_name = os.getenv("DB_NAME")
db = client[db_name]

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e) 
    
def is_admin(discordID: str):
    # Returns if user is an admin
    return db.users.find_one({"discordID": discordID, "admin": True})
     
# print(db.user.find_one({discordID"}))
print(is_admin("_happiness_"))