from typing import List, TypedDict
from bson.objectid import ObjectId

class Item(TypedDict):
    _id: ObjectId
    name: str
    description: str

class Family(TypedDict):
    _id: ObjectId
    name: str
    points: int
    completed_missions: List[str]
    invited: List[str]
    inventory: List[Item]

class Mission(TypedDict):
    _id: ObjectId
    mission_type: str
    week: int
    name: str
    points: int
    operator: str
    description: str

