import asyncio
from datetime import datetime, timedelta
import re
from typing import List
import discord
from discord.ext import tasks, commands
from discord import app_commands
from pymongo import database
import pytz

from views import PaginatorView
from tao_types import Mission, Family
from utils import await_and_raise_error, get_global_mission, has_family, is_admin, update_points, weeks_since_start

# 11:45 PM PST
check_time_pst = datetime.now().astimezone(pytz.timezone('America/Los_Angeles')).replace(hour=23, minute=45, second=0, microsecond=0)
# UTC time
check_time_utc = check_time_pst.astimezone(pytz.utc)
# tasks loop takes datetime.time object only in utc
global_time = datetime.time(check_time_utc)

class MissionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: database.Database = bot.get_cog("DBCog").db
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("MissionsCog is ready.")
    
    @app_commands.command(name="list_missions")
    async def list_missions_slash(self, interaction: discord.Interaction):
        try:
            global_missions: List[Mission] = list(self.db.missions.find({"mission_type": "global", "week": weeks_since_start(self.db), "active": True}))
            weekly_missions: List[Mission] = list(self.db.missions.find({"mission_type": "weekly", "week": weeks_since_start(self.db), "active": True}))
            all_missions: List[Mission] = global_missions + weekly_missions

            if len(all_missions) == 0:
                await await_and_raise_error(interaction, "No missions found!")

            # Put all missions into their own embed
            embeds: List[discord.Embed] = []

            for i in range(len(all_missions)):
                if (i%10 == 0):
                    embeds.append(discord.Embed(title="Missions", color=0xf8d980))
                mission: Mission = all_missions[i]
                embeds[-1].add_field(name=mission['name'], value=f"Points: {mission['points']}\n{mission['description']}", inline=False)
                
            # Place mission embeds into paginator and display the initial page
            missions: discord.ui.view = PaginatorView(embeds)
            await interaction.response.send_message(embed=await missions.initial, view=missions)

        except Exception as e:
            print(f"Error: {e}")

    @app_commands.command(name="add_mission")
    @app_commands.describe(name="name of mission", description="description of mission", points="can be +2, x2, -1, etc...")
    async def add_mission_slash(self, interaction: discord.Interaction, name: str, description: str, points: str):
        try:
            if not is_admin(interaction.user):
                await interaction.response.send_message(f"You are not an admin!")
                return
            # TODO: add repeat times
            start_date_obj = self.db.data.find_one({"name": "start_week"}) 
            end_date_obj = self.db.data.find_one({"name": "end_week"}) 

            if start_date_obj is None or end_date_obj is None:
                await await_and_raise_error(interaction, "Start or end date not set!")
            
            end_date = end_date_obj["date"]
            
            missions = []
            for week in range(weeks_since_start(self.db, end_date)):
                mission: Mission = {
                    "name": name,
                    "mission_type": "global",
                    "week": week,
                    "description": description,
                    "active": True,
                    "repeat_times": 1,
                    "operator": points[0],
                    "points": int(points[1:])
                }
                missions.append(mission)
            self.db.missions.insert_many(missions)
            await interaction.response.send_message(f"{name} has been added!")
        except Exception as e:
            print(f"Error: {e}")
    
    @app_commands.command(name="add_weekly_mission")
    @app_commands.describe(name="name of mission", description="description of mission", points="can be +2, x2, -1, etc...")
    async def add_weekly_mission_slash(self, interaction: discord.Interaction, name: str, description: str, points: str):
        try:
            if not is_admin(interaction.user):
                await interaction.response.send_message(f"You are not an admin!")
                return
            # TODO: add repeat times
            mission: Mission = {
                "name": name,
                "mission_type": "weekly",
                "week": weeks_since_start(self.db),
                "active": True,
                "description": description,
                "repeat_times": 1,
                "operator": points[0],
                "points": int(points[1:])
            }
            self.db.missions.insert_one(mission)
            await interaction.response.send_message(f"{name} has been added!")
        except Exception as e:
            print(f"Error: {e}")
    

    @app_commands.command(name="activate_mission")
    @app_commands.describe(name="name of mission")
    async def activate_mission(self, interaction: discord.Interaction, name: str):
        """Activates a mission from current week to end week"""
        try:
            if not is_admin(interaction.user):
                await interaction.response.send_message(f"You are not an admin!")
                return
            # TODO: add repeat times
            mission = self.db.missions.find_one({"name": name, "week": weeks_since_start(self.db)})
            if mission is None:
                await await_and_raise_error("Mission does not exist!")
                
            end_week_obj = self.db.data.find_one({"name": "end_week"})
            if end_week_obj is None:
                await await_and_raise_error("End week not set!")
            
            for week in range(weeks_since_start(self.db), weeks_since_start(self.db, end_week_obj["date"])):
                self.db.missions.update_one({"name": name, "week": week}, {"$set": {"active": True}})

            await interaction.response.send_message(f"{mission['name']} has been activated!")

        except Exception as e:
            print(f"Error: {e}")

            
    @app_commands.command(name="deactivate_mission")
    @app_commands.describe(name="name of mission")
    async def deactivate_mission_slash(self, interaction: discord.Interaction, name: str):
        """Deactivates a mission from current week to end week"""
        try:
            if not is_admin(interaction.user):
                await interaction.response.send_message(f"You are not an admin!")
                return
            # TODO: add repeat times
            mission = self.db.missions.find_one({"name": name, "week": weeks_since_start(self.db)})
            if mission is None:
                await await_and_raise_error("Mission does not exist!")
                
            end_week_obj = self.db.data.find_one({"name": "end_week"})
            if end_week_obj is None:
                await await_and_raise_error("End week not set!")
            
            for week in range(weeks_since_start(self.db), weeks_since_start(self.db, end_week_obj["date"])):
                self.db.missions.update_one({"name": name, "week": week}, {"$set": {"active": False}})

            await interaction.response.send_message(f"{mission['name']} has been deactivated!")

        except Exception as e:
            print(f"Error: {e}")


    @app_commands.command(name="submit_mission")
    @app_commands.describe(name="mission name")
    async def submit_mission(self, interaction: discord.Interaction, name: str):
        try:
            response: Mission = self.db.missions.find_one({"name": name, "week": weeks_since_start(self.db), "active": True})
            if (response is None):
                await await_and_raise_error(interaction, f"{name} is not a mission")
            
            if not has_family(str(interaction.user.id), self.db):
                await await_and_raise_error(interaction, f"You are not in a family!")
            
            family: Family = self.db.families.find_one({'members': {'$in': [str(interaction.user.id)]}})
            
            # create a channel to let members submit proof
            # TODO: still need to add error checking for this
            guild: discord.Guild = interaction.guild
            admin_role: discord.Role = discord.utils.get(guild.roles, name="admin")
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                admin_role: discord.PermissionOverwrite(read_messages=True)
            }
            for member in family['members']:
                member_obj: discord.Member = guild.get_member(int(member))
                if (member_obj is not None):
                    overwrites[member_obj] = discord.PermissionOverwrite(read_messages=True)
            
            category: discord.CategoryChannel = discord.utils.get(guild.categories, name='Verification')
            if category is None:
                category = await guild.create_category('Verification')

            channel: discord.TextChannel = await guild.create_text_channel(f'{family["name"]} - {name}', overwrites=overwrites, category=category)
            await channel.send(f"Mission submitted! Waiting for verification for {name} mission for week {weeks_since_start(self.db)} for family {family['name']}! Please submit proof for {name} mission here!")
            await interaction.response.send_message(f"Mission submitted! Please check {channel.mention} for verification!")
        except Exception as e:
            print(f"Error: {e}")

    async def delete_channel_after(self, channel: discord.TextChannel, time_in_seconds: int):
        await asyncio.sleep(time_in_seconds)
        await channel.delete()

    # for admins verifying missions
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        try:
            channel: discord.TextChannel = self.bot.get_channel(payload.channel_id)
            if (channel.category is None or channel.category.name != "Verification"):
                return
            print("reaction added")
            message: discord.Message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            guild: discord.Guild = self.bot.get_guild(payload.guild_id)
            member: discord.Member = guild.get_member(payload.user_id)
            if not is_admin(member):
                print("not admin")
                return
            
            pattern = r"Mission submitted! Waiting for verification for (.*?) mission for week (\d+) for family (.*?)! Please submit proof for \1 mission here!"
            match = re.search(pattern, message.content)
            if not match:
                print('no regex match')
                return
            
            name = match.group(1)
            week = int(match.group(2))
            family = match.group(3)
            print(name, week, family)
            mission: Mission = get_global_mission(name, week, self.db)
            if (mission is None):
                print(f"could not find mission {name}")
                return
            print(self.db.missions.find_one({"name": name, "week": week}))
            repeat_times: int = self.db.missions.find_one({"name": name, "week": week})["repeat_times"]
            completed = self.db.families.find({'name': family, 'completed_missions': {'$in': [mission['_id']]} })
            if (len(list(completed)) >= repeat_times):
                print("mission quote already reached")
                return
            self.db.families.update_one({'name': family}, {'$addToSet': {'completed_missions': mission['_id']}})
            points = update_points(family, self.db)
            channel: discord.TextChannel = self.bot.get_channel(payload.channel_id)
            await channel.send(f"Mission {name} for week {week} for family {family} has been verified! {family} now has {points} points! This channel will be deleted in 1 hour to prevent clutter.")
            asyncio.ensure_future(self.delete_channel_after(channel, 3600))
            
        except Exception as e:
            print(f"Error: {e}")
            
    @tasks.loop(time=global_time)
    async def generate_globals(self):
        current_week = weeks_since_start(self.db)
        week_in_two_hours = weeks_since_start(self.db, datetime.now() + timedelta(hours=2)) 
        if (week_in_two_hours > current_week):
            print(f"Generating global missions for week ${week_in_two_hours}")
            # generate missions for next week
            previous_week_missions = list(self.db.missions.find({"mission_type": "global", "week": current_week}))
            for mission in previous_week_missions:
                to_add = mission.copy()
                to_add["week"] = week_in_two_hours
                self.db.missions.insert_one(to_add)
            print("Generated global missions for next week")

# When adding the cog to the bot, call the setup_commands method
async def setup(bot):
    await bot.add_cog(MissionsCog(bot))
