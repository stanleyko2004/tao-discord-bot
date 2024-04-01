
from typing import List
import discord
from discord.ext import commands
from discord import app_commands
from pymongo import database
from pymongo.results import InsertOneResult

from tao_types import Family, Mission, MysteryBox
from utils import is_admin, update_points, weeks_since_start


class MysteryBoxesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: database.Database = bot.get_cog("DBCog").db
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("FamilyCog is ready.")

    @app_commands.command(name="add_mystery_box")
    @app_commands.describe(name="name of mystery box", description="description of mystery box", type="type of mystery box (steal or multiplier)", points="number of points", fam="family name")
    async def add_mystery_box(self, interaction: discord.Interaction, name: str, description: str, type: str, points: str, fam: str):
        try:
            if not is_admin(interaction.user):
                await interaction.response.send_message(f"You are not an admin!")
                return
            # TODO: add repeat times
            family = self.db.families.find_one({"name": fam})
            if family is None:
                await interaction.response.send_message(f"Family {fam} does not exist!")
                return
            
            # TODO: check types
            mystery_box: MysteryBox = {
                "name": name,
                "description": description,
                "type": type,
                "points": int(points),
            }
            
            self.db.families.update_one({'name': fam}, {'$addToSet': {'inventory': mystery_box}})
            await interaction.response.send_message(f"{name} has been added to {fam}'s inventory!")
        except Exception as e:
            print(f"Error: {e}")


    @app_commands.command(name="use_mystery_box")
    @app_commands.describe(name="name of mystery box", fam="family to use on (can leave blank if not a steal)")
    async def use_mystery_box(self, interaction: discord.Interaction, name: str, fam: str = None):
        try:
            user_fam: Family = self.db.families.find_one({"members": {"$in": [str(interaction.user.id)]}})
            if user_fam is None:
                await interaction.response.send_message("You are not in a family!")
                return
            mystery_box: MysteryBox = next((m for m in user_fam['inventory'] if m['name'] == name), None)
            if mystery_box is None:
                await interaction.response.send_message(f"You do not have {name} in your inventory!")
                return
            # has family and has mystery box
            
            # use it
            # modularize these
            if mystery_box['type'] == 'steal':
                if fam is None:
                    await interaction.response.send_message("You must specify a family to steal from!")
                    return
                target_fam: Family = self.db.families.find_one({"name": fam})
                if target_fam is None:
                    await interaction.response.send_message(f"Family {fam} does not exist!")
                    return
                # steal points
                stolen_mission: Mission = {
                    "mission_type": "mystery_box",
                    "week": weeks_since_start(self.db),
                    "name": "steal",
                    "points": mystery_box['points'],
                    "operator": "-",
                    "description": f"{mystery_box['points']} points stolen by {user_fam['name']}!"
                }
                resp: InsertOneResult = self.db.missions.insert_one(stolen_mission)
                self.db.families.update_one({'name': target_fam['name']}, {'$addToSet': {'completed_missions': resp.inserted_id}})
                update_points(target_fam['name'], self.db)
                
                stealer_mission: Mission = {
                    "mission_type": "mystery_box",
                    "week": weeks_since_start(self.db),
                    "name": "steal",
                    "points": mystery_box['points'],
                    "operator": "+",
                    "description": f"{mystery_box['points']} points stolen from {fam}!"
                }
                resp: InsertOneResult = self.db.missions.insert_one(stealer_mission) 
                self.db.families.update_one({'name': user_fam["name"]}, {'$addToSet': {'completed_missions': resp.inserted_id}})
                update_points(user_fam['name'], self.db)

                await interaction.response.send_message(f"{mystery_box['points']} points have been stolen from {fam}!")
            elif mystery_box['type'] == 'multiplier':
                multiplier_mission: Mission = {
                    "mission_type": "mystery_box",
                    "week": weeks_since_start(self.db),
                    "name": "multiplier",
                    "points": mystery_box['points'],
                    "operator": "x",
                    "description": f"Mystery Box x{mystery_box['points']} points multiplier!"
                }
                resp: InsertOneResult = self.db.missions.insert_one(multiplier_mission)
                self.db.families.update_one({'name': user_fam["name"]}, {'$addToSet': {'completed_missions': resp.inserted_id}})
                update_points(user_fam['name'], self.db)
                await interaction.response.send_message(f"Used {name} to multiply points by {mystery_box['points']}!")
            else:
                raise NotImplementedError
            
            # remove the mystery box from the user's inventory
            self.db.families.update_one({'name': user_fam['name']}, {'$pull': {'inventory': mystery_box}})
            
        except Exception as e:
            print(f"Error: {e}")


    @app_commands.command(name="check_inventory")
    async def check_inventory(self, interaction: discord.Interaction):
        try:
            user_fam: Family = self.db.families.find_one({"members": {"$in": [str(interaction.user.id)]}})
            if user_fam is None:
                await interaction.response.send_message("You are not in a family!")
                return
            inventory: List[MysteryBox] = user_fam['inventory']
            if len(inventory) == 0:
                await interaction.response.send_message("You do not have any mystery boxes in your inventory!")
                return
            embed = discord.Embed(title=f"{user_fam['name']}'s Inventory", color=0xf8d980)
            for mystery_box in inventory:
                embed.add_field(name=mystery_box['name'], value=f"Type: {mystery_box['type']}\nPoints: {mystery_box['points']}\n{mystery_box['description']}", inline=False)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(f"Error: {e}") 


# When adding the cog to the bot, call the setup_commands method
async def setup(bot):
    await bot.add_cog(MysteryBoxesCog(bot))