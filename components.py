"""Contains all the ECS Components."""

from random import randint
from typing import List, Dict

from dataclasses import dataclass, field


@dataclass
class LevelC:
    """Stores what level the entity is on."""
    level_num: int

@dataclass
class GameStatsC:
    """Stores stats about the game."""
    kills: int = 0

@dataclass
class StairsC:
    """Stores the direction the stairs go in."""
    direction: str = "down"

@dataclass
class TilePositionC:
    """Stores position of an entity."""
    x: int
    y: int

@dataclass
class HealthC:
    """Stores health of an entity."""
    max: int = None
    current: int = None
    def __post_init__(self):
        if self.current is None:
            self.current = self.max

@dataclass
class InitiativeC:
    """Makes an entity able to take turns."""
    speed: int
    nextturn: int = field(init=False)
    def __post_init__(self):
        self.nextturn = randint(1, self.speed)

@dataclass
class AIC:
    """Tags an entity as controlled by the computer. Stores id of entity to attack."""
    target: int = 0

@dataclass
class RegenC:
    """Tags an entity as able to passively regenerate."""
    amount: int = 1

@dataclass
class ExplosiveC:
    """Tags an entity as an explosive. Stores whether it is primed and how close it is to exploding."""
    fuse: int
    primed: bool = False

@dataclass
class ExplodeC:
    """An explode event put on the entity which is to explode."""
    radius: int = 1
    damage: int = 10

@dataclass
class DestructibleC:
    """Tags an entity with no Health component as able to be destroyed by explosives."""
    pass

@dataclass
class PlayerInputC:
    """Tags an entity as controlled by the player."""
    pass

@dataclass
class MyTurnC:
    """Tags an entity as ready to take a turn."""
    pass

@dataclass
class BumpC:
    """A bump event put on the entity which is bumping."""
    x: int
    y: int

@dataclass
class DamageC:
    """A damage message which is put on a message entity.

    Stores target id of damage, the amount of damage to inflict and any elemental properties.
    """
    target: int
    amount: int
    burn: bool = False
    freeze: bool = False

@dataclass
class BlockerC:
    """Tags an entity as solid and can't pass through other solid entities."""
    pass

@dataclass
class ItemC:
    """Tags that an entity can be carried/stored and whether it is a consumable."""
    consumable: bool

@dataclass
class InventoryC:
    """Gives an entity an inventory. Stores current entities carried and maximum capacity."""
    capacity: int
    contents: List[int] = field(init=False, default_factory=list)

@dataclass
class StoredC:
    """Stores what entity is currently carrying/storing this entity."""
    carrier: int

@dataclass
class MovementC:
    """Tags that an entity can move and stores whether it can move diagonally."""
    diagonal: bool = False

@dataclass
class AttackC:
    """Tags that an entity can attack and stores for how much damage."""
    damage: int

@dataclass
class SplitC:
    """Stores the template functions of the entities to spawn when this entity dies."""
    entities: List

@dataclass
class DeadC:
    """Tags an entity as dead."""
    pass

@dataclass
class IceElementC:
    """Tags an entity as an ice elemental.

    Applies frozen when attacking and is immune to freezing.
    """
    pass

@dataclass
class FrozenC:
    """Tags an entity as frozen in ice.

    It requires a one-turn action to break free of the ice.
    """
    pass

@dataclass
class FireElementC:
    """Tags an entity as a fire elemental.

    Applies burning when attacking and is immune to burning.
    """
    pass

@dataclass
class BurningC:
    """Tags an entity as burning, stores how many turns left."""
    life: int

@dataclass
class FreeTurnC:
    """Lets an entity get initiative and move for free for a limited time."""
    life: int

@dataclass
class UseEffectC:
    """Stores names of methods that are called when this entity is 'used'"""
    effects: List
    def __init__(self, *effects):
        self.effects = effects

@dataclass
class RenderC:
    """Stores imagename of image to render."""
    imagename: str

@dataclass
class AnimationC:
    """Stores entity animations."""
    animations: Dict[str, List[str]]
    current_animation: List[str] = None
    pos: int = 0
    def __init__(self, **args):
        self.animations = args
