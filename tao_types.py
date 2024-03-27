from typing import List, TypedDict
from bson.objectid import ObjectId

class MysteryBox(TypedDict):
    _id: ObjectId
    name: str
    description: str
    type: str # can change to ENUM eventually
    points: int
    
class Family(TypedDict):
    _id: ObjectId
    name: str
    points: int
    completed_missions: List[str]
    invited: List[str]
    inventory: List[MysteryBox]

class Mission(TypedDict):
    _id: ObjectId
    mission_type: str
    week: int
    name: str
    repeat_times: int
    points: int
    operator: str
    description: str

