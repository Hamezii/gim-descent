"""Contains all the ECS Components."""

from random import randint
from typing import List, Dict

from dataclasses import dataclass, field

@dataclass
class Boss:
    """Tags an entity as a boss, and contains a list of minions to kill if it dies."""
    minions: List[int] = field(default_factory=list)

@dataclass
class Describable:
    """Stores the name and description of an entity."""
    name: str
    desc: str

@dataclass
class Bomber:
    """Tags an entity that drops a bomb on death and attacks by exploding."""
    pass

@dataclass
class Level:
    """Stores what level the entity is on."""
    level_num: int

@dataclass
class GameStats:
    """Stores stats about the game."""
    kills: int = 0
    time: float = 0

@dataclass
class Stairs:
    """Stores the direction the stairs go in."""
    direction: str = "down"

@dataclass
class TilePosition:
    """Stores position of an entity."""
    x: int
    y: int

@dataclass
class Health:
    """Stores health of an entity."""
    max: int = None
    current: int = None
    def __post_init__(self):
        if self.current is None:
            self.current = self.max

@dataclass
class Initiative:
    """Makes an entity able to take turns."""
    speed: int
    nextturn: int = field(init=False)
    def __post_init__(self):
        self.nextturn = randint(2, self.speed+1)

@dataclass
class AI:
    """Tags an entity as controlled by the computer. Stores id of entity to target."""
    target: int = 0

@dataclass
class AIFlyWizard:
    """Tag for fly wizard AI."""
    state: str = "asleep"

@dataclass
class AIDodge:
    """Tags an entity as able to dodge attacks."""
    pass

@dataclass
class Regen:
    """Tags an entity as able to passively regenerate."""
    amount: int = 1

@dataclass
class Explosive:
    """Tags an entity as an explosive. Stores whether it is primed and how close it is to exploding."""
    fuse: int
    primed: bool = False

@dataclass
class Explode:
    """An explode event put on the entity which is to explode."""
    radius: int = 1
    damage: int = 10

@dataclass
class Destructible:
    """Tags an entity with no Health component as able to be destroyed by explosives."""
    pass

@dataclass
class PlayerInput:
    """Tags an entity as controlled by the player."""
    pass

@dataclass
class MyTurn:
    """Tags an entity as ready to take a turn."""
    pass

@dataclass
class Bump:
    """A bump event put on the entity which is bumping."""
    x: int
    y: int

@dataclass
class Damage:
    """A damage message which is put on a message entity.

    Stores target id of damage, the amount of damage to inflict and any elemental properties.
    """
    target: int
    amount: int
    burn: bool = False
    freeze: bool = False

@dataclass
class Blocker:
    """Tags an entity as solid and can't pass through other solid entities."""
    pass

@dataclass
class Item:
    """Tags that an entity can be carried/stored and whether it is a consumable."""
    consumable: bool

@dataclass
class Inventory:
    """Gives an entity an inventory. Stores current entities carried and maximum capacity."""
    capacity: int
    contents: List[int] = field(init=False, default_factory=list)

@dataclass
class Stored:
    """Stores what entity is currently carrying/storing this entity."""
    carrier: int

@dataclass
class Movement:
    """Tags that an entity can move and stores whether it can move diagonally."""
    diagonal: bool = False

@dataclass
class Attack:
    """Tags that an entity can attack and stores for how much damage."""
    damage: int

@dataclass
class Split:
    """Stores the template functions of the entities to spawn when this entity dies."""
    entities: List

@dataclass
class Dead:
    """Tags an entity as dead."""
    pass

@dataclass
class Delete:
    """Tags an entity to be safely removed from the ECS."""
    pass

@dataclass
class IceElement:
    """Tags an entity as an ice elemental.

    Applies frozen when attacking and is immune to freezing.
    """
    pass

@dataclass
class Frozen:
    """Tags an entity as frozen in ice.

    It requires a one-turn action to break free of the ice.
    """
    pass

@dataclass
class FireElement:
    """Tags an entity as a fire elemental.

    Applies burning when attacking and is immune to burning.
    """
    pass

@dataclass
class Burning:
    """Tags an entity as burning, stores how many turns left."""
    life: int

@dataclass
class FreeTurn:
    """Lets an entity get initiative and move for free for a limited time."""
    life: int

@dataclass
class UseEffect:
    """Stores names of methods that are called when this entity is 'used'"""
    effects: List
    def __init__(self, *effects):
        self.effects = effects

@dataclass
class Render:
    """Stores imagename of image to render."""
    imagename: str
    blinking: bool = False

@dataclass
class Animation:
    """Stores entity animations."""
    animations: Dict[str, List[str]]
    current_animation: List[str] = None
    pos: int = 0
    def __init__(self, **args):
        self.animations = args
