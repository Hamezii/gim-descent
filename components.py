"""Contains all the ECS Components."""

from random import randint

class LevelC:
    """Stores what level the entity is on."""
    def __init__(self, level_num):
        self.level_num = level_num

class GameStatsC:
    """Stores stats about the game."""
    def __init__(self):
        self.kills = 0

class StairsC:
    """Stores the direction the stairs go in."""
    def __init__(self, direction="down"):
        self.direction = direction

class TilePositionC:
    """Stores position of an entity."""
    def __init__(self, x, y):
        self.x = x
        self.y = y

class HealthC:
    """Stores health of an entity."""
    def __init__(self, health=None):
        self.max = health
        self.current = health


class InitiativeC:
    """Makes an entity able to take turns."""
    def __init__(self, speed=None):
        self.speed = speed
        self.nextturn = randint(1, speed)


class AIC:
    """Tags an entity as controlled by the computer. Stores id of entity to attack."""
    def __init__(self):
        self.target = 0


class RegenC:
    """Tags an entity as able to passively regenerate."""
    def __init__(self, amount=1):
        self.amount = amount


class ExplosiveC:
    """Tags an entity as an explosive. Stores whether it is primed and how close it is to exploding."""
    def __init__(self, fuse):
        self.fuse = fuse
        self.primed = False


class ExplodeC:
    """An explode event put on the entity which is to explode."""
    def __init__(self):
        self.radius = 1
        self.damage = 10


class DestructibleC:
    """Tags an entity with no Health component as able to be destroyed by explosives."""
    def __init__(self):
        pass


class PlayerInputC:
    """Tags an entity as controlled by the player."""
    def __init__(self):
        pass


class MyTurnC:
    """Tags an entity as ready to take a turn."""
    def __init__(self):
        pass


class BumpC:
    """A bump event which is put on the entity which is bumping."""
    def __init__(self, x, y):
        self.x = x
        self.y = y


class DamageC:
    """A damage message which is put on a message entity.

    Stores target id of damage, the amount of damage to inflict and any elemental properties.
    """
    def __init__(self, target, amount, burn=False, freeze=False):
        self.target = target
        self.amount = amount
        self.burn = burn
        self.freeze = freeze


class BlockerC:
    """Tags an entity as solid and can't pass through other solid entities."""
    def __init__(self):
        pass


class ItemC:
    """Tags that an entity can be carried/stored and whether it is a consumable."""
    def __init__(self, consumable):
        self.consumable = consumable


class InventoryC:
    """Gives an entity an inventory. Stores current entities carried and maximum capacity."""
    def __init__(self, capacity):
        self.capacity = capacity
        self.contents = []


class StoredC:
    """Stores what entity is currently carrying/storing this entity."""
    def __init__(self, carrier):
        self.carrier = carrier


class MovementC:
    """Tags that an entity can move and stores whether it can move diagonally."""
    def __init__(self, diagonal=False):
        self.diagonal = diagonal


class AttackC:
    """Tags that an entity can attack and stores for how much damage."""
    def __init__(self, damage):
        self.damage = damage

class SplitC:
    """Stores the components of the entities to spawn when this entity dies."""
    def __init__(self, entities):
        self.entities = entities

class DeadC:
    """Tags an entity as dead."""
    def __init__(self):
        pass

class IceElementC:
    """Tags an entity as an ice elemental.

    Applies frozen when attacking and is immune to freezing.
    """
    def __init__(self):
        pass

class FrozenC:
    """Tags an entity as frozen in ice.

    It requires a one-turn action to break free of the ice.
    """
    def __init__(self):
        pass

class FireElementC:
    """Tags an entity as a fire elemental.

    Applies burning when attacking and is immune to burning.
    """
    def __init__(self):
        pass

class BurningC:
    """Tags an entity as burning, stores how many turns left."""
    def __init__(self, life):
        self.life = life

class FreeTurnC:
    """Lets an entity get initiative and move for free for a limited time."""
    def __init__(self, life):
        self.life = life

class UseEffectC:
    """Stores names of methods that are called when this entity is 'used'"""
    def __init__(self, *effects):
        self.effects = effects

class RenderC:
    """Stores imagename of image to render."""
    def __init__(self, imagename=None):
        self.imagename = imagename

class AnimationC:
    """Stores entity animations."""
    def __init__(self, **args):
        self.animations = args
        self.current_animation = None
        self.pos = 0
