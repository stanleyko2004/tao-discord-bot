# Constants
DEV = True

# Imports
from collections import deque

# Discord Bot imports and constants

from discord.ext import commands
from discord import app_commands
import discord
from dotenv import load_dotenv
load_dotenv()
import os
from tao_types import Family, Item, Mission
from typing import List

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))


bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# Database Stuff
from pymongo import MongoClient

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
uri = os.getenv("MONGO_URI")
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db_name = os.getenv("DB_NAME")
db = client[db_name]
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e) 

def id_to_name(interaction: discord.Interaction, discord_id: str):
    # Converts discord id to server nickname(?)
    members = interaction.guild.members
    for member in members:
        if (str(member.id) == discord_id):
            return member.name
    return False

# Helper Functions
def is_admin(user: discord.User) -> bool:
    # Returns if user is an admin
    roles: List[discord.Role] = user.roles
    for role in roles:
        if (role.name == "admin"):
            return True
    return False

def has_family(discord_id: str):
    # Returns whether or not user has a family
    return not db.families.find_one({'members': {'$in': [discord_id]}}) is None

def in_family(discord_id: str, family_name: str):
    # Returns whether or not user is in specified family
    return not db.families.find_one({'name': family_name, 'members': {'$in': [discord_id]}}) is None

def get_families(discord_id: str):
    # Returns list of families that user is in in
    return list(db.families.find({"members": {'$in': [discord_id]}}))

def pull_invites(discord_id: str):
    # Pulls all invites that user has from families
    db.families.update_many({"invited": {"$in": [discord_id]}}, {"$pull": {"invited": discord_id}})

async def await_and_raise_error(interaction: discord.Interaction, message: str):
    # Awaits and sends error message to interaction and raises exception for backend
    await interaction.response.send_message(message)
    raise Exception(message)


# Discord bot commands

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


# Views
class PaginatorView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed]):
        super().__init__()

        self._embeds = embeds
        self._len = len(embeds)
        self._initial = embeds[0]
        self._queue = deque(embeds)
        self._current_page = 0
        self.children[0].disabled = True
        if len(embeds) == 1: self.children[1].disabled = True

        for i in range(self._len):
            self._embeds[i].set_footer(text=f"Page {i+1} of {self._len}")

    # Updates buttons to disable when at ends and enable otherwise
    async def update_view(self, interaction: discord.Interaction):

        if self._current_page == self._len - 1:
            self.children[1].disabled = True
        else:
            self.children[1].disabled = False

        if self._current_page == 0:
            self.children[0].disabled = True
        else:
            self.children[0].disabled = False

        await interaction.message.edit(view=self)

    @discord.ui.button(label="<", style=discord.ButtonStyle.blurple)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._queue.rotate(1)
        embed = self._queue[0]
        self._current_page -= 1
        await self.update_view(interaction)
        await interaction.response.edit_message(embed=embed)
        
    @discord.ui.button(label=">", style=discord.ButtonStyle.blurple)
    async def forward_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._queue.rotate(-1)
        embed = self._queue[0]
        self._current_page += 1
        await self.update_view(interaction)
        await interaction.response.edit_message(embed=embed)

    # Used to access and display inital page
    @property
    async def initial(self) -> discord.Embed:
        return self._embeds[0]

#### Slash Commands
@bot.tree.command(name="help")
@app_commands.describe(user="user")
async def help_slash(interaction: discord.Interaction, user: discord.member.Member):
    print(interaction.user)
    print(type(interaction.user))
    print(user.id)
    print(type(user))
    await interaction.response.send_message(f"TAO bot help: currently nothing")


#### Family
# Inviting # verified
@bot.tree.command(name="fam_invite")
@app_commands.describe(invitee="invitee id")
async def fam_invite_slash(interaction: discord.Interaction, invitee: discord.member.Member):
    try:
        author_id: str = str(interaction.user.id)
        author_name: str = interaction.user.name
        invitee_id: str = str(invitee.id)
        invitee_name: str = invitee.name
        
        # Check if author is inviting themselves
        if author_id == invitee_id:
            await await_and_raise_error(interaction, f"You cannot invite yourself to a family.")
        
        # Check if invitee already has a family
        if has_family(invitee_id):
            await await_and_raise_error(interaction, f"{invitee_name} is already in a family.")
        
        # Check if author is in family or not
        if not has_family(author_id):
            await await_and_raise_error(interaction, f"{author_name} is not currently in a family, {author_name} cannot invite someone else to a family")
        
        # Attempt to invite to family
        response: Family = db.families.find_one({'members': {'$in': [author_id]}})
        family_name: str = response['name']
        if invitee_id in response["invited"]:
            await await_and_raise_error(interaction, f"{invitee_name} has already been invited to {family_name}!")
        else:
            db.families.update_one({'name': family_name}, {'$addToSet': {'invited': invitee_id}})
            await interaction.response.send_message(f"{invitee_name} successfully invited to {family_name}!")

    except Exception as e:
        print(f"Error: {e}")


# Leaving # verified
@bot.tree.command(name="fam_leave")
async def fam_leave_slash(interaction: discord.Interaction):
    try:
        author_id: str= str(interaction.user.id)
        author_name: str = str(interaction.user.name)
        response: Family = db.families.find_one({'members': {'$in': [author_id]}})

        if response is None:
            await await_and_raise_error(interaction, f"You are not currently in a family.")
        else:
            update_response: Family = db.families.update_one({'name': response['name']}, {'$pull': {'members': author_id}})
            if (update_response.modified_count == 1):
                await interaction.response.send_message(f"{author_name} has left {response['name']}.")
                return
            else:
                await await_and_raise_error(interaction, "Something went wrong :(")

    except Exception as e:
        print(f"Error: {e}")


# Joining # verified
@bot.tree.command(name="fam_join")
@app_commands.describe(family="family name")
async def fam_join_slash(interaction: discord.Interaction, family: str):
    try:
        author_id: str = str(interaction.user.id)
        author_name: str = interaction.user.name
        
        # Check if user is invited to family specified
        response: Family = db.families.find_one({'name': family, 'invited': {'$in': [author_id]}})
        if not response is None:
            # Add user to family, remove invite from all families
            db.families.update_one({'name': family}, {'$addToSet': {'members': author_id}})
            pull_invites(author_id)
            await interaction.response.send_message(f"{author_name} has joined {family}!")
        else:
            await await_and_raise_error(interaction, f"You have not been invited to {family}.")

    except Exception as e:
        print(f"Error: {e}")
            

# Creating # verified
@bot.tree.command(name="fam_create")
@app_commands.describe(family="family name")
async def create_fam(interaction: discord.Interaction, family: str):
    try:
        author_id: str = str(interaction.user.id)

        # Check if author already has a family
        if has_family(author_id):
            await await_and_raise_error(interaction, f"{id_to_name(interaction, author_id)} is already in a family, cannot create a new one.")

        # Check if family name already exists
        response = db.families.find_one({"name": family})
        if not response is None:
            await await_and_raise_error(interaction, f"Family {family} already exists!")

        # Create new family
        new_family: Family = {
            'name': family,
            'members': [author_id],
            'points': 0,
            'completed_missions': [],
            'inventory': [],
            'invited': [],
        }

        db.families.insert_one(new_family)

        pull_invites(author_id)

        await interaction.response.send_message(f"Family {family} created!")

    except Exception as e:
        print(f"Error: {e}")

# Info
# Have family info default to author's family 
@bot.tree.command(name="fam_info")
@app_commands.describe(family="family name")
async def fam_info_slash(interaction: discord.Interaction, family: str):
    try:
        response: Family = db.families.find_one({'name': family})
        if response is None:
            raise Exception(f"Family {family} does not exist.")
        else:
            name: str = response['name']
            points: int = response['points']
            member_names: List[str] = []
            for member_id in response['members']:
                name: str = id_to_name(interaction, member_id)
                if name != False:
                    member_names.append(name)
            members_str: str = ', '.join(member_names)
            embed: discord.Embed = discord.Embed(title=name, description='family description', color=0xf8d980)
            embed.add_field(name='Members', value=members_str, inline=False)
            embed.add_field(name='Points', value=points, inline=False)
            embed.set_footer(text='footer text')
            await interaction.response.send_message(embed=embed)

    except Exception as e:
        print(f"Error: {e}")

# Leaderboard # verified
@bot.tree.command(name="fam_leaderboard")
async def fam_leaderboard_slash(interaction: discord.Interaction):
    try:
        response = db.families.find().sort({'score': 1})

        families: List[Family] = list(response)
        embeds: List[discord.Embed] = []

        for f in range(len(families)):
            family: Family = families[f]

            # Create new page for more families
            if (f % 5 == 0):
                embeds.append(discord.Embed(title="Fam Leaderboard", color=0xf8d980))

            # Add family and their score as a row
            embeds[-1].add_field(name=f"{f+1}.{family['name']}: {family['points']}", value="", inline=False)

        pages: PaginatorView = PaginatorView(embeds)
        await interaction.response.send_message(embed=await pages.initial, view=pages)

    except Exception as e:
        print(f"Error: {e}")

# Score
# Default to author's family
@bot.tree.command(name="fam_score")
@app_commands.describe(family="family name")
async def fam_score_slash(interaction: discord.Interaction, family: str=""):
    try:
        response: Family = db.families.find_one({'name': family})
        if response is None:
            await await_and_raise_error(interaction, f"{family} does not exist!")
        else:
            await interaction.response.send_message(f"{family} currently has {response['points']} points!")

    except Exception as e:
        print(f"Error: {e}")


#### Missions

# TODO
# globals are multiple missions spread across weeks
# expiry dates
#   dont display missions past expiry
#   dont let people submit to expiry
# Verification

@bot.tree.command(name="fam_missions")
async def fam_missions_slash(interaction: discord.Interaction):
    try:
        response: List[Mission] = list(db.missions.find())

        # Put all missions into their own embed
        embeds: List[discord.Embed] = []

        for i in range(len(response)):
            if (i%10 == 0):
                embeds.append(discord.Embed(title="Missions", color=0xf8d980))
            mission: Mission = response[i]
            embeds[-1].add_field(name=mission['name'], value=f"Points: {mission['points']}\n{mission['description']}", inline=False)
            
        # Place mission embeds into paginator and display the initial page
        missions: discord.ui.view = PaginatorView(embeds)
        await interaction.response.send_message(embed=await missions.initial, view=missions)

    except Exception as e:
        print(f"Error: {e}")
        

@bot.tree.command(name="add_mission")
@app_commands.describe(name="name of mission", description="description of mission", points="can be +2, x2, -1, etc...")
async def add_mission_slash(interaction: discord.Interaction, name: str, description: str, points: str):
    try:
        if not is_admin(interaction.user):
            await interaction.response.send_message(f"You are not an admin!")
            return
        
        mission: Mission = {
            "name": name,
            "mission_type": "global",
            "description": description,
            "operator": points[0],
            "points": int(points[1:])
        }
        db.missions.insert_one(mission)
        await interaction.response.send_message(f"{name} has been added!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    bot.run(BOT_TOKEN)