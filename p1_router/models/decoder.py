from dataclasses import dataclass
from typing import List

@dataclass
class EntityState:
    id: int
    r: int
    g: int
    b: int

@dataclass
class ParsedMessage:
    universe: int
    entities: List[EntityState]