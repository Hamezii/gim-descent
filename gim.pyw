'''
GIM Descent 4

James Lecomte

To do:
- Clean up ui code

- Maybe implement an event system, where Systems emit events which other Systems recieve
 - This one might be a bad idea though

- Fix the grid cache system
 - I think this is done
'''

# VV Do this to profile VV
# py -m cProfile -s tottime gim.pyw

import pickle
import random
#from functools import lru_cache

import pygame

import audio
import components as c
import constants
import entity_templates
import renderer
import systems as s
import ui
from ecs import World

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()

pygame.mixer.set_num_channels(8)

audio.load_audio()


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

    def update(self, t_frame, pos=None):
        """Update shake amount and move towards target position."""
        if pos is not None:
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
        self.world: World = None

    #@lru_cache()
    def entity_draw_data(self, entity):
        """Return a dictionary of draw data about an entity."""
        data = {}
        # Image name
        data["name"] = self.world.entity_component(entity, c.Render).imagename
        # Color modifier
        color = [0, 0, 0]
        if self.world.has_component(entity, c.FireElement) or self.world.has_component(entity, c.Burning):
            color[0] += 100
        if self.world.has_component(entity, c.IceElement):
            color[0] += 0
            color[1] += 50
            color[2] += 100
        if any(color):
            data["color"] = (color[0], color[1], color[2], pygame.BLEND_ADD)
        # Blinking tag
        if self.world.has_component(entity, c.Render):
            data["blinking"] = self.world.entity_component(entity, c.Render).blinking and RENDERER.is_blinking()

        # Icons
        icons = []
        if self.world.has_component(entity, c.FireElement):
            icons.append(("elementFire", None))

        if self.world.has_component(entity, c.IceElement):
            icons.append(("elementIce", None))

        if self.world.has_component(entity, c.Explosive):
            explosive = self.world.entity_component(entity, c.Explosive)
            if explosive.primed:
                icons.append(("explosive", explosive.fuse))

        if self.world.has_component(entity, c.FreeTurn):
            freeturn = self.world.entity_component(entity, c.FreeTurn)
            icons.append(("free-turn", freeturn.life))

        data["icons"] = tuple(icons)

        data["frozen"] = self.world.has_component(entity, c.Frozen)

        # Returning dictionary
        return data

    def draw_centered_entity(self, surface, entity, scale, pos):
        """Draw an entity, including icons etc."""
        entity_surface = RENDERER.entity_image(scale, **self.entity_draw_data(entity))
        RENDERER.draw_centered_image(surface, entity_surface, pos)

    def teleport_entity(self, entity, amount):
        """Teleport an entity to a random position in a specific radius."""
        pos = self.world.entity_component(entity, c.TilePosition)
        while True:
            randpos = (pos.x+random.randint(-amount, amount),
                       pos.y+random.randint(-amount, amount))
            if self.world.get_system(s.GridSystem).on_grid(randpos):
                if self.world.get_system(s.GridSystem).get_blocker_at(randpos) == 0:
                    self.world.get_system(s.GridSystem).move_entity(entity, randpos)
                    return

    def speed_entity(self, entity, amount):
        """Give an entity free turns."""
        if self.world.has_component(entity, c.FreeTurn):
            self.world.entity_component(entity, c.FreeTurn).life += amount
        else:
            self.world.add_component(entity, c.FreeTurn(amount))

    def heal_entity(self, entity, amount):
        """Heal an entity for a certain amount of health."""
        if self.world.has_component(entity, c.Health):
            health = self.world.entity_component(entity, c.Health)
            health.current = min(health.max, health.current+amount)

    def random_loot(self, x, y):
        """Spawn random loot at a certain position."""
        item = random.randint(1, 4)
        if item == 1:
            self.world.create_entity(*entity_templates.health_potion(x, y))

        if item == 2:
            self.world.create_entity(*entity_templates.speed_potion(x, y))

        if item == 3:
            self.world.create_entity(*entity_templates.teleport_potion(x, y))

        if item == 4:
            self.world.create_entity(*entity_templates.bomb(x, y))

    def generate_fly_wizard_level(self):
        """Make the fly wizard level."""
        grid = []
        gridwidth = self.world.get_system(s.GridSystem).gridwidth
        gridheight = self.world.get_system(s.GridSystem).gridheight

        main_room = pygame.Rect(5, 5, 20, 20)

        for y in range(0, gridheight):  # Walls
            grid.append([])

            for x in range(0, gridwidth):
                if main_room.collidepoint(x, y):
                    grid[y].append(0)
                else:
                    grid[y].append(1)

        for x in range(1, 5):
            for y in range(14, 17):
                grid[y][x] = 0

        for y in range(14, 17):
            grid[y][8] = 1

        self.world.create_entity(*entity_templates.fly(7, 15))
        self.world.create_entity(*entity_templates.fly_wizard(22, 15))

        for y in range(0, gridheight):
            for x in range(0, gridwidth):
                if grid[y][x] == 1:                  # Creating walls on positions which have been marked
                    self.world.create_entity(*entity_templates.wall(x, y))

        self.world.add_component(self.world.tags.player, c.TilePosition(2, 15))



    def generate_random_level(self, level):
        """Initialise the entities for a random level."""

        level_type = "normal"
        if random.random() < 0.5 and level > 1:
            level_type = random.choice(("ice", "fire"))

        grid = []
        gridwidth = self.world.get_system(s.GridSystem).gridwidth
        gridheight = self.world.get_system(s.GridSystem).gridheight

        for y in range(0, gridheight):  # Walls
            grid.append([])

            for x in range(0, gridwidth):
                grid[y].append(1)

        for roomy in range(0, gridheight):  # Rooms
            for roomx in range(0, gridwidth):
                roomheight = random.randint(2, 6)
                roomwidth = random.randint(2, 6)
                if roomx + roomwidth <= gridwidth and roomy + roomheight <= gridheight and random.randint(1, 15) == 1:
                    for y in range(0, roomheight):
                        for x in range(0, roomwidth):
                            grid[roomy+y][roomx+x] = 0

        # Stairs down
        exit_x = random.randrange(gridwidth)
        exit_y = random.randrange(gridheight)
        while grid[exit_y][exit_x]:
            exit_x = random.randrange(gridwidth)
            exit_y = random.randrange(gridheight)

        grid[exit_y][exit_x] = 2
        self.world.create_entity(*entity_templates.stairs(exit_x, exit_y))

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

        #Spawn pool
        spawn_pool = [*["snake"]*4]
        if 1 <= level <= 6:
            spawn_pool.extend(["ogre"]*3)
        if 1 <= level <= 6:
            spawn_pool.extend(["snake"]*4)
        else:
            spawn_pool.extend(["snake"]*2)

        if 1 <= level <= 5:
            spawn_pool.extend(["slime_medium"]*1)
        else:
            spawn_pool.extend(["slime_large"]*1)

        if level >= 7:
            spawn_pool.extend(["bomb_goblin"]*1)
        if level >= 7:
            spawn_pool.extend(["caterkiller"]*1)
        if level >= 10:
            spawn_pool.extend(["golem"]*1)


        for y in range(0, gridheight):
            for x in range(0, gridwidth):
                if grid[y][x] == 1:                  # Creating walls on positions which have been marked
                    wall = self.world.create_entity(*entity_templates.wall(x, y))
                    if random.randint(1, 3) == 1:
                        if level_type == "ice":
                            self.world.add_component(wall, c.IceElement())
                        if level_type == "fire":
                            self.world.add_component(wall, c.FireElement())

                elif grid[y][x] == 0:
                    if random.randint(1, max(45-level*2, 10)) == 1:       # Creating enemies
                        choice = random.choice(spawn_pool)
                        entity = self.world.create_entity(*getattr(entity_templates, choice)(x, y))

                        if random.randint(1, 2) == 1:
                            if level_type == "ice":
                                self.world.add_component(entity, c.IceElement())
                            if level_type == "fire":
                                self.world.add_component(entity, c.FireElement())

        self.world.get_system(s.GridSystem).process()
        x, y = self.world.get_system(s.GridSystem).random_free_pos()
        self.world.add_component(self.world.tags.player, c.TilePosition(x, y))


    def generate_level(self):
        """Generate a level depending on how far the player got."""

        if not self.world.tags.player:
            self.world.tags.player = self.world.create_entity(*entity_templates.player(0, 0))

        level = self.world.entity_component(self.world.tags.player, c.Level).level_num

        if level == 12:
            self.generate_fly_wizard_level()
        else:
            self.generate_random_level(level)

        if level == 1:
            pos = self.world.entity_component(self.world.tags.player, c.TilePosition)
            for _ in range(3):
                self.world.create_entity(*entity_templates.bomb(pos.x, pos.y))

    def get_debug_info(self):
        """Return a tuple of text for debug info."""
        fps = CLOCK.get_fps()
        info = (
            "FPS: " + str(int(fps)),
            "TOTAL IMAGES: " + str(RENDERER.total_images),
            "OBJECTS: " + str(len([*self.world.get_component(c.TilePosition)]))
        )
        return info

    def save_game(self):
        """Save the game state."""
        with open("save.save", "wb") as save_file:
            pickle.dump(self.world, save_file)

    def load_game(self):
        """Load the game from where it was last saved."""
        with open("save.save", "rb") as save_file:
            self.world = pickle.load(save_file)
            self.world.set_game_reference(self)

    def new_game(self):
        """Initialise for a new game."""
        self.world = World(self)

        self.world.add_system(s.GameStatsSystem())

        self.world.add_system(s.GridSystem())
        self.world.add_system(s.InitiativeSystem())

        self.world.add_system(s.PlayerInputSystem())
        self.world.add_system(s.AIFlyWizardSystem())
        self.world.add_system(s.AISystem())
        self.world.add_system(s.FreezingSystem())
        self.world.add_system(s.BurningSystem())
        self.world.add_system(s.AIDodgeSystem())
        self.world.add_system(s.BumpSystem())

        self.world.add_system(s.ExplosionSystem())
        self.world.add_system(s.DamageSystem())
        self.world.add_system(s.RegenSystem())
        self.world.add_system(s.PickupSystem())
        self.world.add_system(s.IdleSystem())
        self.world.add_system(s.SplitSystem())
        self.world.add_system(s.StairsSystem())

        self.world.add_system(s.AnimationSystem())

        self.world.add_system(s.DeadSystem())
        self.world.add_system(s.DeleteSystem())

        if constants.SEED is not None:
            random.seed(constants.SEED)

        self.generate_level()

# MAIN

def get_input():
    """Return the key that was just pressed."""
    keypress = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            ui.leave()

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

    RENDERER.camera = game.camera
    UI.game = game

    #game.new_game()

    UI.add_menu(ui.MainMenu)

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

        if keypress == pygame.K_F10: # Save
            game.save_game()
        if keypress == pygame.K_F11: # Load
            game.load_game()

        UI.send_event(("input", UI.get_focus(), keypress))

        if game.world:    # Processing ecs
            game.world.process(playerinput=None, d_t=delta)

            while not game.world.has_component(game.world.tags.player, c.MyTurn): # Waiting for input
                game.world.process(playerinput=None, d_t=0)

        RENDERER.t_elapsed += delta
        UI.send_event(("update", avgms))
        UI.draw_menus(SCREEN)

        pygame.display.update()


def init_screen():
    """Returns the screen surface, as well as WIDTH and HEIGHT constants."""

    pygame.display.set_caption("Gim 4")

    if constants.FULLSCREEN_MODE:
        info_object = pygame.display.Info()
        width = info_object.current_w
        height = info_object.current_h
        screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
    else:
        width = 1200
        height = 800
        screen = pygame.display.set_mode((width, height))

    pygame.display.set_icon(RENDERER.get_image(name="logo"))

    return (screen, width, height)


if __name__ == "__main__":
    CLOCK = pygame.time.Clock()

    # VARIABLES
    RENDERER = renderer.Renderer()

    SCREEN, constants.WIDTH, constants.HEIGHT = init_screen()

    constants.MENU_SCALE = round(constants.WIDTH/600)

    UI = ui.MenuManager(RENDERER)

    # Playing music
    audio.play_music()

    main()
