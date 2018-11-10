"""Stores templates for entity components."""

from random import choice

import animations
import components as c


def item(**args):
    """Item components."""
    return [
        c.Describable(args["name"], args["desc"]),
        c.Render(args["image"]),
        c.TilePosition(args["x"], args["y"]),
        c.Item(consumable=args["consumable"]),
    ]

def creature(**args):
    """Creature components."""
    if "image" not in args:
        args["image"] = None

    components = [
        c.Render(args["image"]),
        c.TilePosition(args["x"], args["y"]),
        c.Movement(diagonal=args["diagonal"]),
        c.Blocker(),
        c.Health(args["health"]),
        c.Attack(args["attack"]),
    ]
    if "anim_idle" in args:
        components.append(
            c.Animation(
                idle=args["anim_idle"],
                ready=args["anim_ready"]
            )
        )
    if "speed" in args:
        components.append(
            c.Initiative(args["speed"])
        )

    return components

def normal_ai_creature(**args):
    """Normal AI creature components."""
    return [
        *creature(**args),
        c.AI()
    ]

def potion(**args):
    """Potion components."""
    return [
        *item(
            **args,
            consumable=True,
            image="potion-"+args["color"]
        ),
        c.UseEffect(args["effect"])
    ]

def health_potion(x, y):
    """Health potion components."""
    return potion(
        x=x, y=y,
        name="Health potion",
        desc="Heals target for 20 HP",
        color="red",
        effect=("heal_entity", 20)
    )

def teleport_potion(x, y):
    """Teleport potion components."""
    return potion(
        x=x, y=y,
        name="Teleport potion",
        desc="Teleports target in a radius of 10 tiles",
        color="blue",
        effect=("teleport_entity", 10)
    )

def speed_potion(x, y):
    """Teleport potion components."""
    return potion(
        x=x, y=y,
        name="Speed potion",
        desc="Gives target 8 free turns",
        color="green",
        effect=("speed_entity", 8)
    )

def bomb(x, y):
    """Bomb components."""
    components = item(
        x=x, y=y,
        name="Bomb",
        desc="Explodes after a cooldown",
        image="bomb",
        consumable=False,
    )
    components.append(c.Explosive(3))
    return components


def ogre(x, y):
    """Ogre components."""
    return normal_ai_creature(
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
    return normal_ai_creature(
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
    return normal_ai_creature(
        x=x,
        y=y,
        anim_idle=animations.GOLEM_IDLE,
        anim_ready=animations.GOLEM_READY,
        diagonal=False,
        speed=3,
        health=30,
        attack=10
    )

def bomb_goblin(x, y):
    """Bomb goblin components."""
    return [
        *normal_ai_creature(
            x=x, y=y,
            image="goblin-bomb-i",
            diagonal=False,
            speed=2,
            health=5,
            attack=0
        ),
        c.Bomber(),
        c.Explosive(2)
    ]


def slime_small(x, y):
    """Small slime components."""
    return normal_ai_creature(
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
        *normal_ai_creature(
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
        *normal_ai_creature(
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
        *normal_ai_creature(
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
        *normal_ai_creature(
            x=x, y=y,
            anim_idle=animations.FLY_FLYING,
            anim_ready=animations.FLY_FLYING,
            diagonal=False,
            speed=1,
            health=5,
            attack=2
        ),
        c.AIDodge()
    ]

def fly_wizard(x, y):
    """Fly wizard components."""
    return [
        *normal_ai_creature(
            x=x, y=y,
            image="fly-wizard-i",
            diagonal=False,
            health=60,
            attack=10
        ),
        c.AIFlyWizard(),
        c.Boss(),
        c.AIDodge()
    ]

def player(x, y, image, health):
    """Player components."""
    return [
        *creature(
            x=x, y=y,
            image=image,
            diagonal=False,
            speed=1,
            health=health,
            attack=5
        ),
        c.PlayerInput(),
        c.Inventory(10),
    ]

def magnum(x, y):
    """Magnum components."""
    return [
        *player(
            x=x, y=y,
            image="magnum",
            health=50
        ),
    ]

def mecha(x, y):
    """Mecha components."""
    return [
        *player(
            x=x, y=y,
            image="mecha",
            health=100
        ),
        c.WeakPotions()
    ]

def edward(x, y):
    """Edward components."""
    return [
        *player(
            x=x, y=y,
            image="edward",
            health=30
        ),
        c.SpeedOnKill()
    ]

def wall(x, y):
    """Wall components."""
    return [
        c.Render(choice(("wall1", "wall2"))),
        c.TilePosition(x, y),
        c.Blocker(),
        c.Destructible(),
        # For alive walls
        #c.Health(15),
        #c.Initiative(4),
        #c.AI(),
        #c.Movement(False),
        #   c.Attack(5),
    ]

def stairs(x, y, direction="down"):
    """Stairs components."""
    return [
        c.Render("stairs-"+str(direction)),
        c.TilePosition(x, y),
        c.Stairs(direction=direction),
    ]
