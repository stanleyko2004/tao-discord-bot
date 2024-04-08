import sys
import os
# for running from parent directory to import other modules
sys.path.append(os.path.abspath(os.pardir))

from dotenv import load_dotenv
from pymongo import MongoClient, database
from pymongo.server_api import ServerApi

from tao_types import Mission
from utils import weeks_since_start

load_dotenv()

mission_list = [
    Mission(
        mission_type="global",
        week=0,
        name="Eat a meal together",
        active=True,
        repeat_times=2,
        points=5,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Bake a dessert together",
        active=True,
        repeat_times=1,
        points=8,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Bike ride",
        active=True,
        repeat_times=1,
        points=5,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Boba run",
        active=True,
        repeat_times=2,
        points=3,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Attend TAO weekend event",
        active=True,
        repeat_times=1,
        points=25,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Attend TAO fundraiser",
        active=True,
        repeat_times=1,
        points=25,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Take a photo studying together",
        active=True,
        repeat_times=1,
        points=5,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Take a photo w Gunrock/ gary may",
        active=True,
        repeat_times=1,
        points=20,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Matching fits",
        active=True,
        repeat_times=1,
        points=3,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Fam farmar",
        active=True,
        repeat_times=1,
        points=8,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Walk around arb",
        active=True,
        repeat_times=1,
        points=10,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Study together",
        active=True,
        repeat_times=1,
        points=10,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Go to the games area together and bowl",
        active=True,
        repeat_times=1,
        points=15,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Take a photo of an unsuspecting board member",
        active=True,
        repeat_times=1,
        points=5,
        operator="+",
        description="If they are in your family, they are not an acceptable target!",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Take a photo with Cheetoh",
        active=True,
        repeat_times=1,
        points=5,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Prank other fam",
        active=True,
        repeat_times=1,
        points=20,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Workout with fam",
        active=True,
        repeat_times=1,
        points=10,
        operator="+",
        description="",
    ),
    Mission(
        mission_type="global",
        week=0,
        name="Extended family",
        active=True,
        repeat_times=1,
        points=25,
        operator="+",
        description="Take photo of your fam and another fam together, cannot be taken at GM",
    ),
]

uri = os.getenv("MONGO_URI")
client = MongoClient(uri, server_api=ServerApi('1'))
db_name = os.getenv("DB_NAME")
db: database.Database = client[db_name]

end_date_obj = db.data.find_one({"name": "end_week"}) 
end_date = end_date_obj["date"]

for mission in mission_list:
    missions = []
    for week in range(weeks_since_start(db, end_date)):
        mission_copy = mission.copy()
        mission_copy["week"] = week
        missions.append(mission_copy)
    print(missions)
    db.missions.insert_many(missions)