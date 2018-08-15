"""Stores templates for entity components."""

from random import choice

import animations
import components as c


def item_template(**args):
    """Item template."""
    return [
        c.Render(args["render"]),
        c.TilePosition(args["x"], args["y"]),
        c.Item(consumable=args["consumable"]),
    ]

def creature(**args):
    """Creature components."""
    return [
        c.Render(args["image"]),
        c.TilePosition(args["x"], args["y"]),
        c.AI(),
        c.Movement(diagonal=args["diagonal"]),
        c.Initiative(args["speed"]),
        c.Blocker(),
        c.Health(args["health"]),
        c.Attack(args["attack"]),
    ]

def animated_creature(**args):
    """Animated creature components."""
    return [
        *creature(
            image=None,
            **args
        ),
        c.Animation(
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
    components.append(c.UseEffect(effect))
    return components

def bomb(x, y):
    """Bomb components."""
    components = item_template(
        x=x, y=y,
        render="bomb",
        consumable=False
    )
    components.append(c.Explosive(3))
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
        c.Split((slime_small, slime_small))
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
        c.Split((slime_medium, slime_medium))
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
        c.Regen(1)
    ]

def fly(x, y):
    """Fly components."""
    return [
        *animated_creature(
            x=x, y=y,
            anim_idle=animations.FLY_FLYING,
            anim_ready=animations.FLY_FLYING,
            diagonal=False,
            speed=1,
            health=10,
            attack=2
        )
    ]

def player(x, y):
    """Player components."""
    return [
        c.Render("magnum"),
        c.TilePosition(x, y),
        c.PlayerInput(),
        c.Movement(),
        c.Initiative(1),
        c.Blocker(),
        c.Health(50),
        c.Inventory(10),
        c.Attack(5),
        c.Level(1),
        c.GameStats(),
        c.FreeTurn(1),      # TEMPORARY: stops player from getting hit at the beginning of the level.
    ]

def wall(x, y):
    """Wall components."""
    return [
        c.Render(choice(("wall1", "wall2"))),
        c.TilePosition(x, y),
        c.Blocker(),
        c.Destructible(),
    ]

def stairs(x, y, direction="down"):
    """Stairs components."""
    return [
        c.Render("stairs-"+str(direction)),
        c.TilePosition(x, y),
        c.Stairs(direction=direction),
    ]
