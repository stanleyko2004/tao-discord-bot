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

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = 1215883267191083111


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


# Helper Functions
def is_admin(discordID: str):
    # Returns if user is an admin
    return db.users.find_one({"discordID": discordID, "admin": True})

def certify_admin(discordID: str):
    if is_admin(discordID) is None:
        raise Exception(f"User {discordID} cannot run this command.")

def has_family(discord_id: str):
    # Returns whether or not user has a family
    return not db.families.find_one({'members': {'$in': [discord_id]}}) is None

def in_family(discord_id: str, family_name: str):
    # Returns whether or not user is in specified family
    return not db.families.find_one({'name': family_name, 'members': {'$in': [discord_id]}}) is None

def get_families(discordID: str):
    # Returns list of families that user is in in
    return list(db.families.find({"members": {'$in': [discordID]}}))


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
class TestView(discord.ui.View):
    def __init__(self, s: str, timeout: float=10):
        super().__init__(timeout=timeout)
        self.s = s

        # This button is separate, its a less powerful(?) button that doesn't have access to interactions and things like that, it can open links though
        self.add_item(discord.ui.Button(label="Test button simple"))

    @discord.ui.button(label="Test Button more complex", style=discord.ButtonStyle.blurple)
    async def test_button(self, interaction: discord.Interaction):
        await interaction.response.send_message(self.s, ephemeral=True)
        
    @discord.ui.button(label="Test Button more complex 2", style=discord.ButtonStyle.blurple)
    async def test_button_2(self, interaction: discord.Interaction):
        await interaction.response.send_message(self.s + "2", ephemeral=False)


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
    async def back_button(self, interaction: discord.Interaction):
        self._queue.rotate(1)
        embed = self._queue[0]
        self._current_page -= 1
        await self.update_view(interaction)
        await interaction.response.edit_message(embed=embed)
        
    @discord.ui.button(label=">", style=discord.ButtonStyle.blurple)
    async def forward_button(self, interaction: discord.Interaction):
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
# Inviting
@bot.tree.command(name="fam_invite")
@app_commands.describe(invitee="invitee id")
async def fam_invite_slash(interaction: discord.Interaction, invitee: discord.member.Member):
    try:
        print(type(invitee))
        author_id = str(interaction.user.id)
        invitee_id = str(invitee.id)
        invitee_name = invitee.name
        
        print(author_id, invitee_id, invitee_name)
        if author_id == invitee_id:
            await interaction.response.send_message(f"You cannot invite yourself to a family.")
            raise Exception(f"User cannot invite themselves")
        
        response = db.families.find_one({'members': {'$in': [author_id]}})
        print(f"response {response}")
        if response is None:
            await interaction.response.send_message(f"You are not currently in a family, you cannot invite someone else to a family")
            raise Exception(f"User {author_id} is not in a family.")
        
        family_name = response['name']
        if invitee_id in response["invited"]:
            await interaction.response.send_message(f"{invitee_name} has already been invited to {family_name}!")
        elif invitee_id in response["members"]:
            await interaction.response.send_message(f"{invitee_name} is already a part of {family_name}!")
        else:
            db.families.update_one({'name': family_name}, {'$addToSet': {'invited': invitee_id}})
            await interaction.response.send_message(f"{invitee_name} successfully invited to {family_name}!")

    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")


# Leaving
@bot.tree.command(name="fam_leave")
@app_commands.describe(family="family name")
async def fam_leave_slash(interaction: discord.Interaction, family: str):
    try:
        author = str(interaction.user)

        response = db.families.find_one({'name': family})

        if not response is None:

            # Remove author from family
            family = response['name']
            response = db.families.update_one({'name': family}, {'$pull': {'members': author}})

            # Print/return response whether or not author was in family
            if response.modified_count == 1:
                await interaction.response.send_message(f"{author} has left {family}.")
            else:
                raise Exception(f"You are not currently a member of {family}.")
        else:
            raise Exception(f"{family} does not exist.")

    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")


# Joining
@bot.tree.command(name="fam_join")
@app_commands.describe(family="family name")
async def fam_join_slash(interaction: discord.Interaction, family: str):
    try:
        author = str(interaction.user)
        
        # Check if user is invited to family specified
        response = db.families.find_one({'name': family, 'invited': {'$in': [author]}})
        print(response)
        print(author)
        if not response is None:
            db.families.update_one({'name': family}, {'$addToSet': {'members': author}, '$pull': {'invited': author}})
            await interaction.response.send_message(f"{author} has joined {family}!")
        else:
            raise Exception(f"You have not been invited to {family}.")

    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")
            
# Info
@bot.tree.command(name="fam_info")
@app_commands.describe()
async def fam_info_slash(interaction: discord.Interaction):
    try:
        author = str(interaction.user)

        response = db.families.find_one({'members': {'$in': [author]}})

        if response is None:
            raise Exception(f"{author} is not currently in a family.")
        else:
            name = response['name']
            points = response['points']
            members = ', '.join(response['members'])
            embed=discord.Embed(title=name, description='family description', color=0xf8d980)
            embed.add_field(name='Members', value=members, inline=False)
            embed.add_field(name='Points', value=points, inline=False)
            embed.set_footer(text='footer text')
            await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")


# Creating
@bot.tree.command(name="create_fam")
@app_commands.describe(family="family name")
async def create_fam(interaction: discord.Interaction, family: str):
    try:
        author = str(interaction.user.id)

        db.families.insert_one({
            "name": family,
            "members": [author],
            "points": 0,
            "completed_missions": [],
            "inventory": [],
            "invited": [],
        })

        await interaction.response.send_message(f"Family {family} created!")

    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")

@bot.tree.command(name="fam_leaderboard")
async def fam_leaderboard_slash(interaction: discord.Interaction):
    try:
        response = db.families.find().sort({'score': 1})

        families = list(response)
        embeds = []

        for f in range(len(families)):
            family = families[f]

            # Create new page for more families
            if (f % 5 == 0):
                embeds.append(discord.Embed(title="Fam Leaderboard", color=0xf8d980))

            # Add family and their score as a row
            embeds[-1].add_field(name=f"{family['name']}: {family['points']}", value="", inline=False)

        pages = PaginatorView(embeds)
        await interaction.response.send_message(embed=await pages.initial, view=pages)

    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")


@bot.tree.command(name="fam_score")
@app_commands.describe(family="family name")
async def fam_score_slash(interaction: discord.Interaction, family: str=""):
    try:
        author = interaction.user.name
        families = db.families.find()
        family_names = [f['name'] for f in families]

        if not has_family(author) and family == "":
            raise Exception(f"You do not have a family!")
        elif family == "":
            # Get default family if not specified
            f = get_families(author)[0]
            await interaction.response.send_message(f"{f['name']} currently has {f['points']} points!")
        elif not family in family_names:
            # Check if specified family exists
            raise Exception(f"{family} does not exist!")
        else:
            # Print score of specified family is exists
            f = db.families.find_one({'name': family})
            await interaction.response.send_message(f"{f['name']} currently has {f['points']} points!")

    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")


#### Missions

@bot.tree.command(name="fam_missions")
async def fam_missions_slash(interaction: discord.Interaction):
    try:
        response = db.missions.find()
        output = []

        # Put all missions into their own embed
        embeds = []

        for mission in response:
            embed=discord.Embed(title="Mission", color=0xf8d980)
            embed.add_field(name=mission['title'], value=f"Points: {mission['points']}\n{mission['description']}", inline=False)
            embeds.append(embed)

        # Place mission embeds into paginator and display the initial page
        missions = PaginatorView(embeds)
        await interaction.response.send_message(embed=await missions.initial, view=missions)

    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")

if __name__ == "__main__":
    bot.run(BOT_TOKEN)