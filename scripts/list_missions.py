import sys
import os
# for running from parent directory to import other modules
sys.path.append(os.path.abspath(os.pardir))

from dotenv import load_dotenv
from pymongo import MongoClient, database
from pymongo.server_api import ServerApi

from utils import weeks_since_start

load_dotenv()

uri = os.getenv("MONGO_URI")
client = MongoClient(uri, server_api=ServerApi('1'))
db_name = os.getenv("DB_NAME")
db: database.Database = client[db_name]

# weeks = weeks_since_start(db, db.data.find_one({"name": "end_week"})["date"])
weeks = weeks_since_start(db)
print(weeks)

missions = list(db.missions.find())
print(len(missions))
