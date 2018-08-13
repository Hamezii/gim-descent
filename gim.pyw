'''
GIM Descent 4

James Lecomte

To do:
- Make enemies do different things when attacking ie. goblins explode when attacking

- Maybe implement an event system, where Systems emit events which other Systems recieve
 - This one might be a bad idea though

- Fix the grid cache system
 - I think this is done


'''

# VV Do this to profile VV
# py -m cProfile -s tottime gim.pyw

import pickle
import random

import pygame

import animations
import audio
import constants
import renderer
import ui
from ecs import World
from systems import *

FULLSCREEN_MODE = True

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()

pygame.mixer.set_num_channels(8)

audio.init_cache()

#random.seed(1)


# CLASSES

class DynamicPos:
    """A vector value which linearly interpolates to a position."""

    def __init__(self, pos, speed):
        self.current = pos
        self.goal = pos
        self.speed = speed

    def move(self, pos, instant=False):
        """Set a target position. Instant moves it there instantly."""
        self.goal = pos
        if instant:
            self.current = pos

    def update(self, delta):
        """Linearly interpolate to target position."""
        x = (self.goal[0] - self.current[0])*min(1, delta*self.speed*0.001)
        y = (self.goal[1] - self.current[1])*min(1, delta*self.speed*0.001)
        self.current = (self.current[0]+x, self.current[1] + y)

    @property
    def x(self):
        """Get x value of vector."""
        return self.current[0]

    @property
    def y(self):
        """Get y value of vector."""
        return self.current[1]


class Camera:
    """The game camera.

    Can follow a point and shake.
    """

    def __init__(self, speed):
        self._ppt = round(constants.MENU_SCALE*1.5)*20
        self._shake = 0
        self._shake_x = 0
        self._shake_y = 0
        self._pos = DynamicPos((0, 0), speed=speed)

        self._t_lastshake = 0
        self.start = True

    def get_rect(self):
        """Return the rect in which the camera can see.

        Rect position and size is in pixels.
        """
        x = (self._pos.x + random.uniform(-self._shake_x, self._shake_x)) * self._ppt / constants.TILE_SIZE
        y = (self._pos.y + random.uniform(-self._shake_y, self._shake_y)) * self._ppt / constants.TILE_SIZE
        rect = pygame.Rect(0, 0, constants.WIDTH, constants.HEIGHT)
        rect.center = (x, y)
        return rect

    def get_scale(self):
        """Return scale of camera. Larger number means more zoomed in."""
        return self._ppt / constants.TILE_SIZE

    def get_zoom(self):
        """Get pixels per tile of camera. Larger number means larger tiles."""
        return self._ppt

    def zoom(self, zoom):
        """Change the pixels per tile of the camera. Positive zoom means zooming in."""
        self._ppt += zoom

    def shake(self, amount):
        """Shake the camera."""
        self._shake += amount

    def set(self, pos, direct=False):
        """Set target position of the camera."""
        self._pos.move(pos, direct)

    def tile_to_pixel_pos(self, x, y):
        """Including zoom, return the position of the center of a tile relative to the top-left of the map."""
        return ((x+0.5)*self._ppt, (y+0.5)*self._ppt)

    def tile_to_camera_pos(self, x, y):
        """Excluding zoom, return the position of the center of a tile relative to the top-left of the map."""
        return ((x+0.5)*constants.TILE_SIZE, (y+0.5)*constants.TILE_SIZE)

    def tile_to_screen_pos(self, x, y):
        """Return the position of the center of a tile relative to the top-left of the screen."""
        pixelpos = self.tile_to_pixel_pos(x, y)
        rect = self.get_rect()
        return (pixelpos[0] - rect.x, pixelpos[1] - rect.y)

    def update(self, t_frame, pos):
        """Update shake amount and move towards target position."""
        if self.start:
            self.start = False
            self.set(pos, direct=True)
        else:
            self.set(pos)

        self._pos.update(t_frame)

        self._t_lastshake += t_frame
        while self._t_lastshake >= 1000/30:
            self._t_lastshake -= 1000/30
            self._shake_x = random.uniform(-self._shake, self._shake)
            self._shake_y = random.uniform(-self._shake, self._shake)

            self._shake *= 0.75
            if self._shake < 0.1:
                self._shake = 0


class Game:
    """The game. Can perform functions on the ECS."""

    def __init__(self):
        self.camera = Camera(speed=5)
        self.world = World(self)

    def entity_image(self, entity, scale):
        """Return the current image of an entity referred to by its id."""
        args = {}

        # Name
        name = self.world.entity_component(entity, RenderC).imagename

        # Color
        color = [0, 0, 0]
        if self.world.has_component(entity, FireElementC) or self.world.has_component(entity, BurningC):
            color[0] += 100
        if self.world.has_component(entity, IceElementC):
            color[0] += 0
            color[1] += 50
            color[2] += 100
        if any(color):
            args["color"] = (color[0], color[1], color[2], pygame.BLEND_ADD)

        # Blinking
        if entity != self.world.tags.player:
            if self.world.has_component(entity, InitiativeC):
                entity_nextturn = self.world.entity_component(entity, InitiativeC).nextturn
                player_nextturn = self.world.entity_component(self.world.tags.player, InitiativeC).nextturn
                if entity_nextturn <= player_nextturn:
                    args["blinking"] = True

        # Getting image
        img = RENDERER.get_image(name=name, scale=scale, **args)
        return img

    def draw_centered_entity(self, surface, entity, scale, pos):
        """Draw an entity, including icons etc."""
        entity_surface = self.entity_image(entity, scale)

        RENDERER.draw_centered_image(surface, entity_surface, pos)

        if self.world.has_component(entity, FrozenC):
            RENDERER.draw_centered_image(surface, RENDERER.get_image(name="ice-cube", scale=scale), pos)

        # Icons
        icons = []

        if self.world.has_component(entity, FireElementC):
            icons.append(("elementFire", None))

        if self.world.has_component(entity, IceElementC):
            icons.append(("elementIce", None))

        if self.world.has_component(entity, ExplosiveC):
            explosive = self.world.entity_component(entity, ExplosiveC)
            if explosive.primed:
                icons.append(("explosive", explosive.fuse))

        if self.world.has_component(entity, FreeTurnC):
            freeturn = self.world.entity_component(entity, FreeTurnC)
            icons.append(("free-turn", freeturn.life))

        ppt = scale * constants.TILE_SIZE
        for i, icon in enumerate(icons):
            image_name = icon[0]
            value = icon[1]

            icon_pos = (pos[0] + ppt*(-0.25 + i*0.2), pos[1] + ppt*0.2)
            RENDERER.draw_centered_image(surface, RENDERER.get_image(name=image_name, scale=scale), icon_pos)
            if value is not None:
                text_pos = (icon_pos[0], icon_pos[1]-ppt*0.3)
                RENDERER.draw_text(surface, constants.WHITE, text_pos, str(value), 10 * scale, centered=True)


    def teleport_entity(self, entity, amount):
        """Teleport an entity to a random position in a specific radius."""
        pos = self.world.entity_component(entity, TilePositionC)
        while True:
            randpos = (pos.x+random.randint(-amount, amount),
                       pos.y+random.randint(-amount, amount))
            if self.world.get_system(GridSystem).on_grid(randpos):
                if self.world.get_system(GridSystem).get_blocker_at(randpos) == 0:
                    self.world.get_system(GridSystem).move_entity(entity, randpos)
                    return

    def speed_entity(self, entity, amount):
        """Give an entity free turns."""
        if self.world.has_component(entity, FreeTurnC):
            self.world.entity_component(entity, FreeTurnC).life += amount
        else:
            self.world.add_component(entity, FreeTurnC(amount))

    def heal_entity(self, entity, amount):
        """Heal an entity for a certain amount of health."""
        if self.world.has_component(entity, HealthC):
            health = self.world.entity_component(entity, HealthC)
            health.current = min(health.max, health.current+amount)

    def spawn_player(self):
        """Spawn the player entity into the level."""
        components = (
            RenderC("magnum"),
            PlayerInputC(),
            MovementC(),
            InitiativeC(1),
            BlockerC(),
            HealthC(50),
            InventoryC(10),
            AttackC(5),
            LevelC(1),
            FreeTurnC(1),      # TEMPORARY: stops player from getting hit at the beginning of the level.
            )

        self.world.tags.player = self.world.create_entity(*components)
        self.world.get_system(GridSystem).update()
        self.random_teleport_player()

        # Starting bombs
        pos = self.world.entity_component(self.world.tags.player, TilePositionC)
        for _ in range(3):
            self.world.create_entity(
                RenderC("bomb"),
                TilePositionC(pos.x, pos.y),
                ItemC(consumable=False),
                ExplosiveC(3)
            )

    def random_teleport_player(self):
        """Randomly teleports the player to somewhere on the level."""

        while True:
            randpos = (random.randrange(self.world.get_system(GridSystem).gridwidth),
                       random.randrange(self.world.get_system(GridSystem).gridheight))
            if self.world.get_system(GridSystem).on_grid(randpos):
                if self.world.get_system(GridSystem).get_blocker_at(randpos) == 0:
                    self.world.add_component(self.world.tags.player, TilePositionC(*randpos))
                    return

    def random_loot(self, x, y):
        """Spawn random loot at a certain position."""
        item = random.randint(1, 4)
        if item == 1:
            self.world.create_entity(
                RenderC("potion-red"),
                TilePositionC(x, y),
                ItemC(consumable=True),
                UseEffectC((self.heal_entity, 20))
            )
        if item == 2:
            self.world.create_entity(
                RenderC("potion-green"),
                TilePositionC(x, y),
                ItemC(consumable=True),
                UseEffectC((self.speed_entity, 8))
            )
        if item == 3:
            self.world.create_entity(
                RenderC("potion-blue"),
                TilePositionC(x, y),
                ItemC(consumable=True),
                UseEffectC((self.teleport_entity, 15))
            )
        if item == 4:
            self.world.create_entity(
                RenderC("bomb"),
                TilePositionC(x, y),
                ItemC(consumable=False),
                ExplosiveC(3)
            )

    def generate_level(self):
        """Initialise the entities in the ECS."""
        level_type = "normal"
        if random.random() < 0.5:
            level_type = random.choice(("ice", "fire"))

        if self.world.tags.player:
            level = self.world.entity_component(self.world.tags.player, LevelC).level_num
        else:
            level = 1

        grid = []
        gridwidth = self.world.get_system(GridSystem).gridwidth
        gridheight = self.world.get_system(GridSystem).gridheight

        for y in range(0, gridheight):  # Walls
            grid.append([])

            for x in range(0, gridwidth):
                grid[y].append(1)

        for roomy in range(0, gridheight):  # Rooms
            for roomx in range(0, gridwidth):
                roomheight = random.randint(2, 6)
                roomwidth = random.randint(2, 6)
                if roomx + roomwidth <= gridwidth and roomy + roomheight <= gridheight and random.randint(1, max(5, 20-level)) == 1:
                    for y in range(0, roomheight):
                        for x in range(0, roomwidth):
                            grid[roomy+y][roomx+x] = 0

        # Stairs down
        exit_x = random.randrange(gridwidth)
        exit_y = random.randrange(gridheight)
        while grid[exit_y][exit_x]:
            exit_x = random.randrange(gridwidth)
            exit_y = random.randrange(gridheight)

        self.world.create_entity(
            RenderC("stairs-down"),
            TilePositionC(exit_x, exit_y),
            StairsC(),
        )

        # Loot
        loot_x = random.randint(1, gridwidth-2)
        loot_y = random.randint(1, gridheight-2)
        while grid[loot_y][loot_x]:
            loot_x = random.randint(1, gridwidth-2)
            loot_y = random.randint(1, gridheight-2)
        for y in range(loot_y - 1, loot_y + 2):
            for x in range(loot_x - 1, loot_x + 2):
                if not grid[y][x]:
                    self.random_loot(x, y)

        for _ in range(random.randint(2, 5)):
            x = random.randrange(gridwidth)
            y = random.randrange(gridheight)
            while grid[loot_y][loot_x]:
                x = random.randrange(gridwidth)
                y = random.randrange(gridheight)
            self.random_loot(x, y)


        for y in range(0, gridheight):
            for x in range(0, gridwidth):
                if grid[y][x]:                  # Creating walls on positions which have been marked
                    wall = self.world.create_entity(
                        RenderC(random.choice(("wall1", "wall2"))),
                        TilePositionC(x, y),
                        BlockerC(),
                        DestructibleC(),
                    )
                    if random.randint(1, 3) == 1:
                        if level_type == "ice":
                            self.world.add_component(wall, IceElementC())
                        if level_type == "fire":
                            self.world.add_component(wall, FireElementC())
                else:
                    if random.randint(1, max(40-level*2, 10)) == 1:       # Creating enemies
                        choice = random.randint(1, 3)
                        if choice == 1:
                            entity = self.world.create_entity(
                                AnimationC(
                                    idle=animations.OGRE_IDLE,
                                    ready=animations.OGRE_READY
                                    ),
                                RenderC(),
                                TilePositionC(x, y),
                                AIC(),
                                MovementC(diagonal=False),
                                InitiativeC(3),
                                BlockerC(),
                                HealthC(10),
                                AttackC(10),
                            )
                        if choice == 2:
                            entity = self.world.create_entity(
                                AnimationC(
                                    idle=animations.SNAKE_IDLE,
                                    ready=animations.SNAKE_READY
                                    ),
                                RenderC(),
                                TilePositionC(x, y),
                                AIC(),
                                MovementC(diagonal=True),
                                InitiativeC(2),
                                BlockerC(),
                                HealthC(5),
                                AttackC(5),
                            )

                        if choice == 3:
                            entity = self.world.create_entity(
                                AnimationC(
                                    idle=animations.GOLEM_IDLE,
                                    ready=animations.GOLEM_READY
                                    ),
                                RenderC(),
                                TilePositionC(x, y),
                                AIC(),
                                MovementC(diagonal=False),
                                InitiativeC(3),
                                BlockerC(),
                                HealthC(30),
                                AttackC(10),
                            )

                        if random.randint(1, 2) == 1:
                            if level_type == "ice":
                                self.world.add_component(entity, IceElementC())
                            if level_type == "fire":
                                self.world.add_component(entity, FireElementC())

        self.world.get_system(GridSystem).update()

# MAIN

def get_input():
    """Return the key that was just pressed."""
    keypress = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pass # You can make this quit if you want

        if event.type == pygame.KEYDOWN:
            keypress = event.key

            if event.key == pygame.K_w or event.key == pygame.K_UP:
                keypress = constants.UP

            if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                keypress = constants.LEFT

            if event.key == pygame.K_s or event.key == pygame.K_DOWN:
                keypress = constants.DOWN

            if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                keypress = constants.RIGHT

    return keypress


def main():
    """Run the game."""
    game = Game()

    game.world.add_system(GridSystem())
    game.world.add_system(InitiativeSystem())

    game.world.add_system(PlayerInputSystem())
    game.world.add_system(AISystem())
    game.world.add_system(FreezingSystem())
    game.world.add_system(BurningSystem())
    game.world.add_system(BumpSystem())

    game.world.add_system(ExplosionSystem())
    game.world.add_system(DamageSystem())
    game.world.add_system(RegenSystem())
    game.world.add_system(PickupSystem())
    game.world.add_system(IdleSystem())
    game.world.add_system(StairsSystem())
    game.world.add_system(DeadSystem())

    game.world.add_system(AnimationSystem())

    game.generate_level()

    game.spawn_player()

    RENDERER.camera = game.camera
    UI.add_menu(ui.MainMenu(game))

    debugging = False

    while True:

        delta = CLOCK.tick()
        fps = CLOCK.get_fps()
        if fps != 0:
            avgms = 1000/fps
        else:
            avgms = delta

        SCREEN.fill(constants.BLACK)

        keypress = get_input()

        if keypress == pygame.K_MINUS:  # Zooming out
            if game.camera.get_zoom() > 20:
                game.camera.zoom(-20)

        if keypress == pygame.K_EQUALS:  # Zooming in
            game.camera.zoom(20)

        if keypress == pygame.K_F12:
            debugging = not debugging

        if keypress == pygame.K_F10: # Save
            with open("save.save", "wb") as save_file:
                pickle.dump(game.world, save_file)
        if keypress == pygame.K_F11: # Load
            with open("save.save", "rb") as save_file:
                game.world = pickle.load(save_file)


        UI.send_event(("input", UI.get_focus(), keypress))

        done = False
        t_frame = delta
        while not done:
            game.world.update(playerinput=None, t_frame=t_frame)
            t_frame = 0
            if game.world.has_component(game.world.tags.player, MyTurnC):
                done = True

        RENDERER.t_elapsed += delta
        UI.send_event(("update", avgms))
        UI.draw_menus(SCREEN)

        if debugging:
            print_debug_info(game)

        pygame.display.update()

def print_debug_info(game):
    """Show debug info in the topleft corner."""
    fps = CLOCK.get_fps()
    info = (
        "FPS: " + str(int(fps)),
        "TOTAL IMAGES: " + str(RENDERER.total_images),
    )
    for i, line in enumerate(info):
        RENDERER.draw_text(SCREEN, (200, 50, 50), (0, 12*i), line, 10)


def init_screen():
    """Returns the screen surface, as well as WIDTH and HEIGHT constants."""
    if FULLSCREEN_MODE:
        info_object = pygame.display.Info()
        width = info_object.current_w
        height = info_object.current_h
        screen = pygame.display.set_mode(
            (width, height), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
    else:
        width = 1200
        height = 800
        screen = pygame.display.set_mode((width, height))

    return (screen, width, height)

if __name__ == "__main__":
    CLOCK = pygame.time.Clock()

    # VARIABLES
    SCREEN, constants.WIDTH, constants.HEIGHT = init_screen()

    constants.MENU_SCALE = round(constants.WIDTH/600)

    RENDERER = renderer.Renderer()
    UI = ui.MenuManager(RENDERER)

    # Playing music
    audio.play_music()

    main()
