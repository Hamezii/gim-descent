"""Stores templates for entity components."""

from random import choice

import animations
from components import *


def item_template(**args):
    """Item template."""
    return [
        RenderC(args["render"]),
        TilePositionC(args["x"], args["y"]),
        ItemC(consumable=args["consumable"]),
    ]

def creature(**args):
    """Creature components."""
    return [
        RenderC(args["image"]),
        TilePositionC(args["x"], args["y"]),
        AIC(),
        MovementC(diagonal=args["diagonal"]),
        InitiativeC(args["speed"]),
        BlockerC(),
        HealthC(args["health"]),
        AttackC(args["attack"]),
    ]

def animated_creature(**args):
    """Animated creature components."""
    return [
        *creature(
            image=None,
            **args
        ),
        AnimationC(
            idle=args["anim_idle"],
            ready=args["anim_ready"]
        )
    ]

def potion(x, y, color, effect):
    """Potion components."""
    components = item_template(
        x=x,
        y=y,
        render="potion-"+color,
        consumable=True
    )
    components.append(UseEffectC(effect))
    return components

def bomb(x, y):
    """Bomb components."""
    components = item_template(
        x=x, y=y,
        render="bomb",
        consumable=False
    )
    components.append(ExplosiveC(3))
    return components


def ogre(x, y):
    """Ogre components."""
    return animated_creature(
        x=x,
        y=y,
        anim_idle=animations.OGRE_IDLE,
        anim_ready=animations.OGRE_READY,
        diagonal=False,
        speed=3,
        health=10,
        attack=10
    )

def snake(x, y):
    """Snake components."""
    return animated_creature(
        x=x,
        y=y,
        anim_idle=animations.SNAKE_IDLE,
        anim_ready=animations.SNAKE_READY,
        diagonal=True,
        speed=2,
        health=5,
        attack=5
    )

def golem(x, y):
    """Golem components."""
    return animated_creature(
        x=x,
        y=y,
        anim_idle=animations.GOLEM_IDLE,
        anim_ready=animations.GOLEM_READY,
        diagonal=False,
        speed=3,
        health=30,
        attack=10
    )

def slime_small(x, y):
    """Small slime components."""
    return creature(
        x=x, y=y,
        image="slime-s-i",
        diagonal=False,
        speed=3,
        health=5,
        attack=5
    )

def slime_medium(x, y):
    """Medium slime components."""
    return [
        *creature(
            x=x, y=y,
            image="slime-m-i",
            diagonal=False,
            speed=3,
            health=10,
            attack=5
        ),
        SplitC((slime_small, slime_small))
    ]

def slime_large(x, y):
    """Large slime components."""
    return [
        *animated_creature(
            x=x, y=y,
            anim_idle=animations.SLIME_LARGE_IDLE,
            anim_ready=animations.SLIME_LARGE_READY,
            diagonal=False,
            speed=4,
            health=20,
            attack=5
        ),
        SplitC((slime_medium, slime_medium))
    ]

def caterkiller(x, y):
    """Caterkiller components."""
    return [
        *animated_creature(
            x=x, y=y,
            anim_idle=animations.CATERKILLER_IDLE,
            anim_ready=animations.CATERKILLER_READY,
            diagonal=False,
            speed=2,
            health=10,
            attack=5
        ),
        RegenC(1)
    ]

def player(x, y):
    """Player components."""
    return [
        RenderC("magnum"),
        TilePositionC(x, y),
        PlayerInputC(),
        MovementC(),
        InitiativeC(1),
        BlockerC(),
        HealthC(50),
        InventoryC(10),
        AttackC(5),
        LevelC(1),
        GameStatsC(),
        FreeTurnC(1),      # TEMPORARY: stops player from getting hit at the beginning of the level.
    ]

def wall(x, y):
    """Wall components."""
    return [
        RenderC(choice(("wall1", "wall2"))),
        TilePositionC(x, y),
        BlockerC(),
        DestructibleC(),
    ]

def stairs(x, y, direction="down"):
    """Stairs components."""
    return [
        RenderC("stairs-"+str(direction)),
        TilePositionC(x, y),
        StairsC(direction=direction),
    ]
