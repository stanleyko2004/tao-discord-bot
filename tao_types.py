from typing import List, TypedDict

class Item(TypedDict):
    name: str
    description: str

class Family(TypedDict):
    name: str
    points: int
    completed_missions: List[str]
    invited: List[str]
    inventory: List[Item]

class Mission(TypedDict):
    name: str
    points: int
    multiplier: str
    description: str

