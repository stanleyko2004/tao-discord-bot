from datetime import datetime, timedelta
from typing import List

import discord
from pymongo import database

from tao_types import Family, Mission

def update_points(family: str, db: database.Database) -> int:
    family_data: Family = db.families.find_one({'name': family})
    # week to mission
    missions = {}
    # want to calculate points week by week
    # TODO: eventually use batch get for efficiency
    for mission_id in family_data['completed_missions']:
        mission: Mission = db.missions.find_one({'_id': mission_id})
        if (mission['week'] not in missions):
            missions[mission['week']] = []
        missions[mission['week']].append(mission)
    
    points = 0
    for week in missions:
        week_points = 0
        # calculate points with (points * multipliers) - stolen points
        adding_missions = filter(lambda x: x['operator'] == '+', missions[week])
        subtracting_missions = filter(lambda x: x['operator'] == '-', missions[week])
        multiplier_missions = filter(lambda x: x['operator'] == 'x', missions[week])
        for mission in adding_missions:
            week_points += mission['points']
        for mission in multiplier_missions:
            week_points *= mission['points']
        for mission in subtracting_missions:
            week_points -= mission['points']
        points += week_points
        
    db.families.update_one({'name': family}, {'$set': {'points': points}})
    return points

def get_global_mission(name: str, week: int, db: database.Database) -> Mission:
    # gets global mission and lazily adds it if it's not there
    response: Mission = db.missions.find_one({"name": name, "week": week})
    if (response is None):
        # no mission with that week yet
        mission: Mission = db.missions.find_one({"name": name})
        
        if (mission is None):
            print(f"mission {name} does not exist")
            return
        
        to_add: Mission = mission.copy()
        to_add["week"] = week
        del to_add["_id"]
        db.missions.insert_one(to_add)
        return to_add
    return response 

def weeks_since_start(db: database.Database, date: datetime = datetime.now()) -> int:
    start_date: datetime = db.data.find_one({"name": "start_week"})["date"]
    difference: timedelta = date - start_date
    weeks: int = difference // timedelta(days=7)
    return weeks

def id_to_name(interaction: discord.Interaction, discord_id: str):
    # Converts discord id to server nickname(?)
    members = interaction.guild.members
    for member in members:
        if (str(member.id) == discord_id):
            return member.name
    return False

# Helper Functions
def is_admin(user: discord.User | discord.Member) -> bool:
    # Returns if user is an admin
    roles: List[discord.Role] = user.roles
    for role in roles:
        if (role.name == "admin"):
            return True
    return False

def has_family(discord_id: str, db: database.Database):
    # Returns whether or not user has a family
    return not db.families.find_one({'members': {'$in': [discord_id]}}) is None

def in_family(discord_id: str, family_name: str, db: database.Database):
    # Returns whether or not user is in specified family
    return not db.families.find_one({'name': family_name, 'members': {'$in': [discord_id]}}) is None

def get_families(discord_id: str, db: database.Database):
    # Returns list of families that user is in in
    return list(db.families.find({"members": {'$in': [discord_id]}}))

def pull_invites(discord_id: str, db: database.Database):
    # Pulls all invites that user has from families
    db.families.update_many({"invited": {"$in": [discord_id]}}, {"$pull": {"invited": discord_id}})

async def await_and_raise_error(interaction: discord.Interaction, message: str):
    # Awaits and sends error message to interaction and raises exception for backend
    await interaction.response.send_message(message)
    raise Exception(message)