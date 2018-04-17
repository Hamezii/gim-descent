'''
GIM Descent
4.4 :

- Moved bumping code into the ECS in order to organise code
- Took more code out of the main game class and put it into the ECS. Much better!

James Lecomte
Started : 13/04/18
Last edit: 14/04/18
'''

FULLSCREEN_MODE = True
MUSIC_VOLUME = 1

'''
To Do:
- Stop enemies hitting each other.

- Stop enemies walking on the same tile.
  This is because the blockerGrid does not get updated when something moves.

- Add fire damage back into the game.

'''
import cProfile as profile
import glob
import random
import sys
import time
from math import floor, hypot

import pygame

import ECS

pygame.mixer.pre_init(44100, -16, 8, 2048)
pygame.init()
pygame.mixer.init()

# random.seed(1)

# CONSTANTS

TILE_SIZE = 40
ANIMATION_RATE = 1000/4
BLINK_RATE = 250

FOLDER = "gimstuff/"
IMAGES = FOLDER + "images/"
AUDIO = FOLDER + "audio/"
MUSIC = AUDIO + "music/"
DEFAULT_IMAGES = FOLDER + "images/"

LIBRARY = FOLDER + "lib/"
sys.path.insert(0, './'+LIBRARY)  # So the program can import from lib folder

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (122, 122, 122)
DARK_RED = (150, 0, 0)
DARK_GREEN = (0, 150, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
ORANGE = (255, 170, 50)

BORDER_COLOR = BLACK
BG_COLOR = (50, 50, 50)


LEFT = (-1, 0)
RIGHT = (1, 0)
UP = (0, -1)
DOWN = (0, 1)
DIRECTIONS = (UP, DOWN, LEFT, RIGHT)

# FUCTIONS


def dist(pos1, pos2):
    """Return the distance between 2 points using Pythagoras."""
    return hypot(abs(pos1.x-pos2.x), abs(pos1.y-pos2.y))


def clamp(minimum, value, maximum):
    """Return the value clamped between a range."""
    return min(max(minimum, value), maximum)


def leave():
    """Close the game."""
    sys.exit(0)


# CLASSES

class DynamicPos:
    """A vector value which linearly interpolates to a position."""

    def __init__(self, pos, speed):
        self.current = pos
        self.goal = pos
        self.speed = speed

    def move(self, pos, instant=False):
        self.goal = pos
        if instant:
            self.current = pos

    def update(self, ms):
        x = (self.goal[0] - self.current[0])*min(1, ms*self.speed*0.001)
        y = (self.goal[1] - self.current[1])*min(1, ms*self.speed*0.001)
        self.current = (self.current[0]+x, self.current[1] + y)

    @property
    def x(self):
        return self.current[0]

    @property
    def y(self):
        return self.current[1]


class Camera:
    """The game camera.

    Can follow a point and shake.
    """

    def __init__(self, speed):
        self._ppt = MENU_SCALE*30
        self._shake = 0
        self._shake_x = 0
        self._shake_y = 0
        self._pos = DynamicPos((0, 0), speed=speed)

        self._t_lastshake = 0
        self.start = True

    def get_rect(self):
        x = (self._pos.x + random.uniform(-self._shake_x,
                                          self._shake_x)) * self._ppt / TILE_SIZE
        y = (self._pos.y + random.uniform(-self._shake_y,
                                          self._shake_y)) * self._ppt / TILE_SIZE
        rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        rect.center = (x, y)
        return rect

    def get_scale(self):
        return self._ppt / TILE_SIZE

    def get_zoom(self):
        return self._ppt

    def zoom(self, zoom):
        self._ppt += zoom

    def shake(self, amount):
        self._shake += amount

    def set(self, pos, direct=False):
        self._pos.move(pos, direct)

    def tile_to_pixel_pos(self, x, y):
        return ((x+0.5)*self._ppt, (y+0.5)*self._ppt)

    def tile_to_camera_pos(self, x, y):
        return ((x+0.5)*TILE_SIZE, (y+0.5)*TILE_SIZE)

    def tile_to_screen_pos(self, x, y):
        pixelpos = self.tile_to_pixel_pos(x, y)
        rect = self.get_rect()
        return (pixelpos[0] - rect.x, pixelpos[1] - rect.y)

    def update(self, t_frame, pos):
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
        self.camera = Camera(speed=10)
        self.world = ECS.World(self)

    def on_grid(self, pos):
        """Return True if a position is on the grid."""
        if clamp(0, pos[0], self.world.get_system(GridSystem).gridwidth-1) == pos[0]:
            if clamp(0, pos[1], self.world.get_system(GridSystem).gridheight-1) == pos[1]:
                return True
        return False

    def teleport_entity(self, entity, amount):
        """Teleport an entity to a random position in a specific radius."""
        pos = self.world.entity_component(entity, TilePositionC)
        while True:
            randpos = (pos.x+random.randint(-amount, amount),
                       pos.y+random.randint(-amount, amount))
            if self.on_grid(randpos):
                if self.world.get_system(GridSystem).get_blocker_at(randpos) == 0:
                    self.world.get_system(
                        GridSystem).move_entity(entity, randpos)
                    return

    def speed_entity(self, entity, amount):
        """Give an entity free turns."""
        for target, initiative in self.world.get_component(InitiativeC):
            if target != entity:
                initiative.nextturn += amount

    def heal_entity(self, entity, amount):
        """Heal an entity for a certain amount of health."""
        if self.world.has_component(entity, HealthC):
            health = self.world.entity_component(entity, HealthC)
            health.current = min(health.max, health.current+amount)

    def generate_level(self):
        """Initialise the entities in the ECS."""
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
                if roomx + roomwidth <= gridwidth and roomy + roomheight <= gridheight and random.randint(1, 15) == 1:
                    for y in range(0, roomheight):
                        for x in range(0, roomwidth):
                            grid[roomy+y][roomx+x] = 0

        for y in range(0, gridheight):
            for x in range(0, gridwidth):
                if grid[y][x]:                  # Creating walls on positions which have been marked
                    self.world.create_entity(
                        RenderC(random.choice(("wall1", "wall2"))),
                        TilePositionC(x, y),
                        BlockerC(),
                    )
                else:
                    if random.randint(1, 45) == 1:      # Creating potions
                        potion = random.randint(1, 3)
                        if potion == 1:
                            self.world.create_entity(
                                RenderC("potion-red"),
                                TilePositionC(x, y),
                                PickupC(consumable=True),
                                UseEffectC((self.heal_entity, 20))
                            )
                        if potion == 2:
                            self.world.create_entity(
                                RenderC("potion-green"),
                                TilePositionC(x, y),
                                PickupC(consumable=True),
                                UseEffectC((self.speed_entity, 8))
                            )
                        if potion == 3:
                            self.world.create_entity(
                                RenderC("potion-blue"),
                                TilePositionC(x, y),
                                PickupC(consumable=True),
                                UseEffectC((self.teleport_entity, 15))
                            )
                    if random.randint(1, 30) == 1:       # Creating enemies
                        choice = random.randint(1, 3)
                        if choice == 1:
                            entity = self.world.create_entity(
                                AnimationC(idle=["ogre-i", "ogre-i", "ogre-i", "ogre-i2", "ogre-i3", "ogre-i3",
                                                 "ogre-i3", "ogre-i4"], ready=["ogre-r", "ogre-r", "ogre-i", "ogre-i"]),
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
                                AnimationC(idle=["snake-i", "snake-i", "snake-i2", "snake-i2"], ready=[
                                           "snake-r", "snake-r", "snake-r2", "snake-r2"]),
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
                                AnimationC(idle=["golem-stone-i", "golem-stone-i", "golem-stone-i", "golem-stone-r", "golem-stone-r",
                                                 "golem-stone-r"], ready=["golem-stone-i", "golem-stone-i", "golem-stone-r", "golem-stone-r"]),
                                RenderC(),
                                TilePositionC(x, y),
                                AIC(),
                                MovementC(diagonal=False),
                                InitiativeC(3),
                                BlockerC(),
                                HealthC(30),
                                AttackC(10),
                            )

                        if random.randint(1, 5) == 1:
                            self.world.add_component(entity, FireElementC())
                        if random.randint(1, 5) == 1:
                            self.world.add_component(entity, IceElementC())


class UI:
    """Stores all the menu instances.

    Used to update, draw and send messages to the menus.
    """

    def __init__(self):
        self.menus = []
        self.focuses = []

    def send_event(self, event):
        """Send an event to all menus."""
        for menu in self.menus:
            menu.get_event(event)

    def draw_menus(self):
        """Draw all the menus."""
        for menu in self.menus:
            menu.draw()

    def add_menu(self, menu, focus=False):
        """Add a menu instance.

        If focus is True, focus will change to the new menu.
        """
        self.menus.append(menu)
        if focus:
            self.focuses.append(menu)

    def remove_menu(self, menu):
        """Remove a menu instance."""
        self.menus.remove(menu)

    def unfocus_menu(self, menu):
        """Remove a menu from the focuses."""
        self.focuses.remove(menu)

    def get_focus(self):
        """Return which menu is currently being focused on."""
        return self.focuses[-1]


class Menu:
    def __init__(self, game):
        self.game = game

    def get_event(self, event):
        return NotImplementedError


class MainMenuTitle:
    def __init__(self):
        self.pos = DynamicPos((WIDTH//2, -200), 0)
        self.y_goal = HEIGHT/2 - 50*MENU_SCALE
        self.speed = 0
        self.shake_x = 0
        self.shake_y = 0
        self.shake = 0
        self.lastshake = 1000/60

    def update(self, ms):
        if self.pos.y < self.y_goal:
            self.speed += ms*0.001
            self.pos.move(
                (self.pos.x, min(self.pos.y+self.speed*ms, self.y_goal)), instant=True)
            if self.pos.y == self.y_goal:
                self.shake = 15*MENU_SCALE
        else:
            if self.shake > 0:
                self.lastshake += ms
                while self.lastshake > 1000/60:
                    self.lastshake -= 1000/60
                    self.shake_x = random.uniform(-self.shake, self.shake)
                    self.shake_y = random.uniform(-self.shake, self.shake)
                    self.shake *= 0.9
                    if self.shake < 1:
                        self.shake = 0

    def draw(self):
        renderer.draw_centered_image(screen, renderer.get_image(
            name="title", scale=MENU_SCALE/2), (self.pos.x+self.shake_x, self.pos.y+self.shake_y))


class MainMenu(Menu):
    def __init__(self, game):
        super().__init__(game)
        self.title = MainMenuTitle()
        self.active = False
        if WIDTH/1920 > HEIGHT/1080:  # Logic to get title image to scale on differently sized monitors
            self.title_background = pygame.transform.scale(renderer.get_image(
                name="title_background"), (WIDTH, int(WIDTH/1920*1080)))
        else:
            self.title_background = pygame.transform.scale(renderer.get_image(
                name="title_background"), (int(HEIGHT/1080*1920), HEIGHT))

    def get_event(self, event):
        if event[0] == "update":
            ms = event[1]
            self.title.update(ms)

            if not self.active:
                if self.title.pos.y == self.title.y_goal:
                    self.active = True
        if event[0] == "input" and event[1] == self:
            keypress = event[2]
            if self.active:
                if keypress:
                    ui.add_menu(GameMenu(game), focus=True)
                    ui.remove_menu(self)

    def draw(self):
        # Logic to get title image to show in the right place
        renderer.draw_image(screen, self.title_background,
                            (0, HEIGHT-self.title_background.get_height()))
        # for different sized sceens
        if self.active:
            renderer.draw_text(screen, (random.randint(0, 5)*50, 122, 0), (WIDTH //
                                                                           2, HEIGHT//2), "Press any key to begin", MENU_SCALE*5, centered=True)
        self.title.draw()


class GameMenu(Menu):
    def __init__(self, game):
        super().__init__(game)

    def get_event(self, event):
        if event[0] == "update":
            ms = event[1]
            cameragoal = self.game.world.entity_component(
                self.game.world.tags.focus, TilePositionC)
            cameragoal = self.game.camera.tile_to_camera_pos(
                cameragoal.x, cameragoal.y)
            self.game.camera.update(ms, cameragoal)
        if event[0] == "input" and event[1] is self:
            keypress = event[2]
            if keypress == pygame.K_z:
                ui.add_menu(Inventory(self.game), focus=True)
            if keypress in DIRECTIONS:
                self.game.world.update(playerinput=keypress, t_frame=0)

    def draw(self):
        camerarect = self.game.camera.get_rect()
        camerazoom = self.game.camera.get_zoom()
        camerascale = camerazoom/TILE_SIZE

        if renderer._zoom_cache != camerazoom:
            renderer._zoom_cache = camerazoom

            gridwidth = self.game.world.get_system(GridSystem).gridwidth
            gridheight = self.game.world.get_system(GridSystem).gridheight

            renderer._floor_cache = pygame.Surface(
                (gridwidth*camerazoom, gridheight*camerazoom))
            for x in range(0, gridwidth):
                for y in range(0, gridheight):
                    renderer._floor_cache.blit(renderer.get_image(
                        name="floor", scale=camerascale), (x*camerazoom, y*camerazoom))

        screen.blit(renderer._floor_cache, (0, 0), (camerarect.x,
                                                    camerarect.y, camerarect.width, camerarect.height))

        for entity, comps in self.game.world.get_components(RenderC, TilePositionC):
            Render = comps[0]
            Pos = comps[1]

            pixelpos = self.game.camera.tile_to_pixel_pos(Pos.x, Pos.y)
            Rect = pygame.Rect(0, 0, camerazoom*2, camerazoom*2)
            Rect.center = pixelpos

            drawing = Rect.colliderect(camerarect)

            if drawing:
                image = renderer.entity_image(entity, scale=camerascale)
                Rect = image.get_rect()
                pixelpos = (pixelpos[0] - camerarect.x,
                            pixelpos[1] - camerarect.y)
                Rect.center = pixelpos
                screen.blit(image, Rect)

                if self.game.world.has_component(entity, FireElementC):
                    screen.blit(renderer.get_image(
                        name="elementFire", scale=camerascale), Rect)
                if self.game.world.has_component(entity, IceElementC):
                    screen.blit(renderer.get_image(
                        name="elementIce", scale=camerascale), Rect)
                if self.game.world.has_component(entity, FrozenC):
                    renderer.draw_centered_image(screen, renderer.get_image(
                        name="ice-cube", scale=camerascale), pixelpos)

                if self.game.world.has_component(entity, HealthC):    # Healthbar
                    Health = self.game.world.entity_component(entity, HealthC)
                    barx = pixelpos[0] - camerazoom*0.4
                    bary = pixelpos[1] + camerazoom*0.4
                    barwidth = camerazoom*0.8
                    barheight = camerazoom*0.1
                    pygame.draw.rect(screen, DARK_RED,
                                     (barx, bary, barwidth, barheight))
                    try:
                        pygame.draw.rect(
                            screen, DARK_GREEN, (barx, bary, barwidth*(Health.current / Health.max), barheight))
                    except ZeroDivisionError:
                        pass


class Inventory(Menu):
    def __init__(self, game):
        super().__init__(game)
        self.cursorpos = [0, 0]
        self.size = [2, 5]
        self.pos = DynamicPos(
            (-TILE_SIZE*MENU_SCALE*2-21, HEIGHT/2-TILE_SIZE*MENU_SCALE*3), speed=10)
        self.show()

    def show(self):
        self.pos.move((40, self.pos.y))

    def hide(self):
        self.pos.move((-TILE_SIZE*MENU_SCALE*2-21, self.pos.y))

    def get_event(self, event):

        if event[0] == "update":
            ms = event[1]
            self.pos.update(ms)
            if self.pos.x < -TILE_SIZE*MENU_SCALE*2-20:
                ui.remove_menu(self)

        if event[0] == "input" and event[1] is self:
            keypress = event[2]
            if keypress == pygame.K_x:
                ui.unfocus_menu(self)
                self.hide()

            if keypress == UP:
                self.cursorpos[1] = max(self.cursorpos[1] - 1, 0)
            if keypress == DOWN:
                self.cursorpos[1] = min(self.cursorpos[1] + 1, self.size[1]-1)

            if keypress == LEFT:
                self.cursorpos[0] = max(self.cursorpos[0] - 1, 0)
            if keypress == RIGHT:
                self.cursorpos[0] = min(self.cursorpos[0] + 1, self.size[0]-1)

            if keypress == pygame.K_z:
                itempos = self.cursorpos[0]*self.size[1]+self.cursorpos[1]
                items = self.game.world.entity_component(
                    self.game.world.tags.player, CarrierC).entities
                if itempos < len(items):
                    ui.add_menu(InventoryOptions(
                        self.game, items[itempos]), focus=True)

    def draw(self):
        drawposx = round(self.pos.x)
        drawposy = round(self.pos.y)

        pygame.draw.rect(screen, BLACK, (drawposx-5*MENU_SCALE, drawposy-5*MENU_SCALE, TILE_SIZE *
                                         self.size[0]*MENU_SCALE+10*MENU_SCALE, TILE_SIZE*self.size[1]*MENU_SCALE+10*MENU_SCALE))

        Carrier = self.game.world.entity_component(
            self.game.world.tags.player, CarrierC)

        for x in range(self.size[0]):
            for y in range(self.size[1]):
                screen.blit(renderer.get_image(name="inventory-slot", scale=MENU_SCALE),
                            (drawposx+TILE_SIZE*MENU_SCALE*x, drawposy+TILE_SIZE*MENU_SCALE*y))

        for i, entity in enumerate(Carrier.entities):
            renderer.draw_centered_image(screen, renderer.entity_image(entity, scale=MENU_SCALE), (
                drawposx+TILE_SIZE*MENU_SCALE*(i//self.size[1]+0.5), drawposy+TILE_SIZE*MENU_SCALE*(i % self.size[1]+0.5)))

        screen.blit(renderer.get_image(name="inventory-cursor-box", scale=MENU_SCALE), (drawposx +
                                                                                        TILE_SIZE*MENU_SCALE*self.cursorpos[0], drawposy+TILE_SIZE*MENU_SCALE*self.cursorpos[1]))

        renderer.draw_text(screen, WHITE, (drawposx, drawposy -
                                           19*MENU_SCALE), "Z to select", 5*MENU_SCALE)
        renderer.draw_text(screen, WHITE, (drawposx, drawposy -
                                           12*MENU_SCALE), "X to return", 5*MENU_SCALE)


class InventoryOptions(Menu):
    def __init__(self, game, item):
        super().__init__(game)
        self.item = item
        self.options = []
        if self.game.world.has_component(item, UseEffectC):
            self.options.append("use")
        self.options.append("throw")
        self.options.append("drop")
        self.size = len(self.options)
        self.pos = (40+TILE_SIZE*MENU_SCALE*2+12*MENU_SCALE,
                    HEIGHT/2-TILE_SIZE*MENU_SCALE*3)
        self.options_pos = [DynamicPos((self.pos[0], self.pos[1]+i*12*MENU_SCALE+(
            TILE_SIZE*1.5+10)*MENU_SCALE), speed=20) for i in range(self.size)]
        self.cursorpos = 0

    def get_event(self, event):
        if event[0] == "update":
            ms = event[1]
            for pos in self.options_pos:
                pos.update(ms)
        if event[0] == "input" and event[1] is self:
            keypress = event[2]
            if keypress == DOWN:
                self.cursorpos = min(self.cursorpos + 1, self.size-1)
            if keypress == UP:
                self.cursorpos = max(self.cursorpos - 1, 0)
            if keypress == pygame.K_x:
                ui.unfocus_menu(self)
                ui.remove_menu(self)
            if keypress == pygame.K_z:
                ui.unfocus_menu(self)
                ui.remove_menu(self)

                selection = self.options[self.cursorpos]
                if selection == "use":
                    use = self.game.world.entity_component(
                        self.item, UseEffectC)
                    for effect in use.effects:
                        effect[0](self.game.world.tags.player, *effect[1:])
                    if self.game.world.entity_component(self.item, PickupC).consumable:
                        self.game.world.entity_component(
                            self.game.world.tags.player, CarrierC).entities.remove(self.item)
                        self.game.world.delete_entity(self.item)
                if selection == "throw":
                    ui.add_menu(ThrowOptions(self.game, self.item), focus=True)

                if selection == "drop":
                    self.game.world.entity_component(
                        self.game.world.tags.player, CarrierC).entities.remove(self.item)
                    pos = self.game.world.entity_component(
                        self.game.world.tags.player, TilePositionC)
                    self.game.world.add_component(
                        self.item, TilePositionC(pos.x, pos.y))

    def draw(self):
        for i, pos in enumerate(self.options_pos):
            if i == self.cursorpos:
                pos.move((self.pos[0]+24*MENU_SCALE, pos.y))
            else:
                pos.move((self.pos[0]+12*MENU_SCALE, pos.y))
            pygame.draw.rect(screen, (0, 0, 0), (pos.x, pos.y,
                                                 60*MENU_SCALE, 12*MENU_SCALE), 0)
            renderer.draw_text(screen, (255, 255, 255), (pos.x+30*MENU_SCALE, pos.y +
                                                         6*MENU_SCALE), self.options[i], size=5 * MENU_SCALE, centered=True)

        renderer.draw_centered_image(screen, renderer.get_image(name="cursor", color=(255, 255, 255, pygame.BLEND_ADD),
                                                                scale=MENU_SCALE), (self.pos[0], self.pos[1]+12*MENU_SCALE*(self.cursorpos+0.5)+(TILE_SIZE*1.5+10)*MENU_SCALE))
        renderer.draw_centered_image(screen, renderer.get_image(name="inventory-slot", scale=MENU_SCALE*1.5),
                                     (self.pos[0]+TILE_SIZE*MENU_SCALE*0.75, self.pos[1]+TILE_SIZE*MENU_SCALE*0.75))
        renderer.draw_centered_image(screen, renderer.entity_image(
            self.item, MENU_SCALE*1.5), (self.pos[0]+TILE_SIZE*MENU_SCALE*0.75, self.pos[1]+TILE_SIZE*MENU_SCALE*0.75))


class ThrowOptions(Menu):
    def __init__(self, game, item):
        super().__init__(game)
        self.item = item
        self.dir = (0, 0)
        self.targettile = None

        self.help_pos = DynamicPos((WIDTH//2, HEIGHT+MENU_SCALE*2.5), speed=10)
        self.help_pos.move((self.help_pos.x, HEIGHT/2+TILE_SIZE*MENU_SCALE))

    def get_event(self, event):
        if event[0] == "update":
            ms = event[1]
            self.help_pos.update(ms)
            if self.help_pos.y > HEIGHT+MENU_SCALE*2.5:
                ui.remove_menu(self)
        if event[0] == "input" and event[1] is self:
            keypress = event[2]
            if keypress == pygame.K_x:
                ui.unfocus_menu(self)
                ui.remove_menu(self)
                ui.add_menu(InventoryOptions(self.game, self.item), focus=True)

            if keypress in DIRECTIONS:
                self.dir = keypress
                playerpos = self.game.world.entity_component(
                    self.game.world.tags.player, TilePositionC)
                self.targettile = [playerpos.x, playerpos.y]
                hitblocker = False
                distance = 0
                while not hitblocker:
                    distance += 1
                    self.targettile[0] += self.dir[0]
                    self.targettile[1] += self.dir[1]
                    if not self.game.on_grid(self.targettile):
                        self.targettile[0] -= self.dir[0]
                        self.targettile[1] -= self.dir[1]
                        hitblocker = True
                    if self.game.world.get_system(GridSystem).get_blocker_at(self.targettile) != 0:
                        hitblocker = True
                    if distance == 5:
                        hitblocker = True

            if keypress == pygame.K_z:
                if self.targettile is not None:
                    self.game.world.entity_component(
                        self.game.world.tags.player, CarrierC).entities.remove(self.item)
                    self.game.world.add_component(
                        self.item, TilePositionC(*self.targettile))

                    target = self.game.world.get_system(
                        GridSystem).get_blocker_at(self.targettile)
                    if target:
                        use = self.game.world.entity_component(
                            self.item, UseEffectC)
                        for effect in use.effects:
                            effect[0](target, *effect[1:])
                        if self.game.world.entity_component(self.item, PickupC).consumable:
                            self.game.world.delete_entity(self.item)

                    ui.unfocus_menu(self)
                    ui.remove_menu(self)

    def draw(self):
        if ui.get_focus() == self:
            renderer.draw_centered_image(screen, renderer.entity_image(self.item, scale=self.game.camera.get_scale(
            )), (WIDTH//2+self.dir[0]*self.game.camera.get_zoom()/2, HEIGHT//2+self.dir[1]*self.game.camera.get_zoom()/2))
            if self.targettile is not None:
                renderer.draw_centered_image(screen, renderer.get_image(
                    name="crosshair", scale=self.game.camera.get_scale()), self.game.camera.tile_to_screen_pos(*self.targettile))
        renderer.draw_text(screen, (170, 170, 170), (self.help_pos.x,
                                                     self.help_pos.y), "Pick a direction", 5*MENU_SCALE, centered=True)
        renderer.draw_text(screen, (255, 255, 255), (self.help_pos.x,
                                                     self.help_pos.y+7*MENU_SCALE), "Z to throw", 5*MENU_SCALE, centered=True)
        renderer.draw_text(screen, (255, 255, 255), (self.help_pos.x, self.help_pos.y +
                                                     14*MENU_SCALE), "X to cancel", 5*MENU_SCALE, centered=True)


class Renderer:
    def __init__(self, game):

        self.SPECIAL_CHARS = {":": "col", "-": "dash", ".": "dot",
                              "!": "exc", "/": "fwdslash", "?": "que", " ": "space"}

        self.images = {}
        self.imported_images = {}
        self.total_images = 0
        self.t = 0
        self._zoom_cache = 0
        self._floor_cache = None
        self.game = game

    def get_image(self, **args):
        if not "scale" in args:
            args["scale"] = 1

        key = str(args)

        if not key in self.images:
            self.total_images += 1
            self.images[key] = self._import_image(args["name"])
            if "scale" in args:
                self.images[key] = pygame.transform.scale(self.images[key], (int(
                    self.images[key].get_width()*args["scale"]), int(self.images[key].get_height()*args["scale"])))

            if "color" in args:
                self.images[key].fill(args["color"][0:3],
                                      special_flags=args["color"][3])

        return self.images[key]

    def _import_image(self, name):
        if not name in self.imported_images:
            try:
                image = pygame.image.load(IMAGES+name+".png").convert_alpha()
            except:
                image = pygame.image.load(
                    DEFAULT_IMAGES+name+".png").convert_alpha()
            self.imported_images[name] = image

        return self.imported_images[name].copy()

    def entity_image(self, entity, scale):
        color = [0, 0, 0]
        if self.game.world.has_component(entity, FireElementC) or self.game.world.has_component(entity, BurningC):
            color[0] += 100
        if self.game.world.has_component(entity, IceElementC) or self.game.world.has_component(entity, FrozenC):
            color[0] += 0
            color[1] += 50
            color[2] += 100

        ready = False
        if self.t % BLINK_RATE < BLINK_RATE/2 and entity != self.game.world.tags.player:
            if self.game.world.has_component(entity, MyTurnC):
                ready = True
            if self.game.world.has_component(entity, InitiativeC):
                if self.game.world.entity_component(entity, InitiativeC).nextturn <= self.game.world.entity_component(self.game.world.tags.player, InitiativeC).nextturn:
                    ready = True

        if ready:
            color[0] += 50
            color[1] += 50
            color[2] += 50

        if any(color):
            img = self.get_image(name=self.game.world.entity_component(
                entity, RenderC).imagename, scale=scale, color=(color[0], color[1], color[2], pygame.BLEND_ADD))
        else:
            img = self.get_image(name=self.game.world.entity_component(
                entity, RenderC).imagename, scale=scale)
        return img

    def draw_text(self, surface, color, pos, text, size, centered=False):
        color = (color[0], color[1], color[2], pygame.BLEND_ADD)

        if centered:
            pos = (pos[0] - (len(text)/2)*size, pos[1] - size*0.5)

        for i in range(len(text)):
            if text[i] in self.SPECIAL_CHARS:
                surface.blit(self.get_image(
                    name="txt_"+self.SPECIAL_CHARS[text[i]], scale=size*0.2, color=color), (pos[0] + i*size, pos[1]))
            else:
                surface.blit(self.get_image(
                    name="txt-"+text[i], scale=size*0.2, color=color), (pos[0] + i*size, pos[1]))

    def draw_image(self, surface, image, pos):
        surface.blit(image, pos)

    def draw_centered_image(self, surface, image, centerpos):
        surface.blit(
            image, (centerpos[0] - image.get_width()//2, centerpos[1] - image.get_height()//2))


# COMPONENTS
class TilePositionC:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class HealthC:
    def __init__(self, health=None):
        self.max = health
        self.current = health


class InitiativeC:
    def __init__(self, speed=None):
        self.speed = speed
        self.nextturn = random.randint(1, speed)


class AIC:
    def __init__(self):
        self.target = None  # An entity id


class PlayerInputC:
    def __init__(self):
        pass


class MyTurnC:
    def __init__(self):
        pass


class BumpC:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class AttackingC:  # Not used yet
    def __init__(self, target):
        self.target = target  # An entity id


class BlockerC:
    def __init__(self):
        pass


class PickupC:
    def __init__(self, consumable):
        self.consumable = consumable


class CarrierC:
    def __init__(self, capacity):
        self.capacity = capacity
        self.entities = []


class MovementC:
    def __init__(self, diagonal=False):
        self.diagonal = diagonal


class AttackC:
    def __init__(self, damage):
        self.damage = damage


class IceElementC:
    def __init__(self):
        pass


class FrozenC:
    def __init__(self):
        pass


class FireElementC:
    def __init__(self):
        pass


class BurningC:
    def __init__(self, life):
        self.life = life


class UseEffectC:
    def __init__(self, *effects):
        self.effects = effects


class RenderC:
    def __init__(self, imagename="shadow"):
        self.imagename = imagename


class AnimationC:
    def __init__(self, **args):
        self.animations = args
        self.current_animation = None
        self.pos = 0


# SYSTEMS
class GridSystem(ECS.System):
    def __init__(self):
        super().__init__()
        self.gridwidth = 40
        self.gridheight = 40
        self.BlockerGrid = None

    def get_blocker_at(self, pos):
        return self.BlockerGrid[pos[0]][pos[1]]

    def move_entity(self, entity, pos):
        Pos = self.world.entity_component(entity, TilePositionC)

        if self.BlockerGrid[Pos.x][Pos.y] == entity:
            if self.BlockerGrid[pos[0]][pos[1]] == 0:
                self.BlockerGrid[Pos.x][Pos.y] = 0
                self.BlockerGrid[pos[0]][pos[1]] = entity
            else:
                raise IndexError("Entity moving to an occupied tile")

        Pos.x, Pos.y = pos

    def update(self, **args):
        self.BlockerGrid = [
            [0 for y in range(self.gridheight)] for x in range(self.gridwidth)]
        for entity, comp in self.world.get_components(TilePositionC, BlockerC):
            self.BlockerGrid[comp[0].x][comp[0].y] = entity


class InitiativeSystem(ECS.System):
    def __init__(self):
        super().__init__()

    def update(self, **args):

        try:
            if self.world.has_component(self.world.tags.player, MyTurnC):
                return
        except:
            pass

        # Only run if not player's turn

        #self.game.turns += 1
        for entity, initiative in self.world.get_component(InitiativeC):
            if not self.world.has_component(entity, MyTurnC):
                initiative.nextturn -= 1
            if initiative.nextturn <= 0:
                initiative.nextturn += initiative.speed
                self.world.add_component(entity, MyTurnC())

            '''
            if self.world.has_component(entity,BurningC):
                self.world.entity_component(entity,BurningC).life -= 1
                if self.world.has_component(entity,HealthC):
                    self.game.hurt_entity(entity,1)
                    
                if self.world.entity_component(entity,BurningC).life <= 0:
                    self.world.remove_component(entity,BurningC)
            '''


class PlayerInputSystem(ECS.System):
    def __init__(self):
        super().__init__()

    def update(self, **args):
        playerinput = args["playerinput"]
        if playerinput in DIRECTIONS:
            for entity, comps in self.world.get_components(TilePositionC, PlayerInputC, MyTurnC):
                tilepos = comps[0]
                bumppos = (tilepos.x+playerinput[0], tilepos.y+playerinput[1])
                self.world.add_component(entity, BumpC(*bumppos))


class AISystem(ECS.System):
    def __init__(self):
        super().__init__()

    def update(self, **args):
        Grid = self.world.get_system(GridSystem)

        for entity, comps in self.world.get_components(MovementC, TilePositionC, AIC, MyTurnC):
            movement = comps[0]
            pos = comps[1]
            ai = comps[2]

            playerpos = self.world.entity_component(
                self.world.tags.player, TilePositionC)
            if dist(pos, playerpos) <= 15:
                ai.target = self.world.tags.player
            else:
                ai.target = 0

            if ai.target:
                targetpos = self.world.entity_component(
                    ai.target, TilePositionC)

                movex = 0
                movey = 0
                moved = False
                if movement.diagonal:
                    if pos.x < targetpos.x:
                        movex = 1
                    if pos.x > targetpos.x:
                        movex = -1
                    if pos.y < targetpos.y:
                        movey = 1
                    if pos.y > targetpos.y:
                        movey = -1
                    if Grid.get_blocker_at((pos.x+movex, pos.y+movey)) in (0, ai.target):
                        moved = True
                        self.world.add_component(
                            entity, BumpC(pos.x+movex, pos.y+movey))

                if not moved:
                    movex = targetpos.x - pos.x
                    movey = targetpos.y - pos.y
                    if abs(movex) < abs(movey):
                        movex = 0
                        if movey < 0:
                            movey = -1
                        if movey > 0:
                            movey = 1
                    else:
                        movey = 0
                        if movex < 0:
                            movex = -1
                        if movex > 0:
                            movex = 1

                    if Grid.get_blocker_at((pos.x+movex, pos.y+movey)) in (0, ai.target):
                        moved = True
                        self.world.add_component(
                            entity, BumpC(pos.x+movex, pos.y+movey))

                if not moved:
                    if movex != 0:
                        movex = 0
                        movey = targetpos.y - pos.y
                        if movey < 0:
                            movey = -1
                        if movey > 0:
                            movey = 1
                    elif movey != 0:
                        movey = 0
                        movex = targetpos.x - pos.x
                        if movex < 0:
                            movex = -1
                        if movex > 0:
                            movex = 1
                    if Grid.get_blocker_at((pos.x+movex, pos.y+movey)) in (0, ai.target):
                        moved = True
                        self.world.add_component(
                            entity, BumpC(pos.x+movex, pos.y+movey))


class FreezingSystem(ECS.System):
    def __init__(self):
        super().__init__()

    def update(self, **args):

        try:
            for entity, _ in self.world.get_components(FrozenC, MyTurnC, BumpC):
                self.world.remove_component(entity, FrozenC)
                self.world.remove_component(entity, MyTurnC)
                self.world.entity_component(entity, InitiativeC).nextturn = 1
        except ValueError:
            pass


class BumpSystem(ECS.System):
    def __init__(self):
        super().__init__()

    def update(self, **args):
        for entity, comps in self.world.get_components(TilePositionC, BumpC, MyTurnC):
            pos = comps[0]
            bump = comps[1]
            bumppos = (bump.x, bump.y)

            targetent = self.world.get_system(GridSystem).get_blocker_at(bumppos)
            if targetent == entity:
                return

            if targetent == 0:
                if self.world.has_component(entity, BlockerC):
                    self.world.get_system(
                        GridSystem).BlockerGrid[pos.x][pos.y] = 0
                    self.world.get_system(
                        GridSystem).BlockerGrid[bump.x][bump.y] = entity
                pos.x = bump.x
                pos.y = bump.y
                self.world.remove_component(entity, MyTurnC)

            else:
                if self.world.has_component(targetent, HealthC) and self.world.has_component(entity, AttackC):
                    attack = self.world.entity_component(entity, AttackC)
                    targethealth = self.world.entity_component(targetent, HealthC)
                    targethealth.current -= attack.damage
                    if targetent == self.world.tags.player:
                        game.camera.shake(attack.damage*3)
                    if targethealth.current <= 0:
                        self.world.delete_entity(targetent)

                    if entity == self.world.tags.player:
                        self.game.camera.shake(5)

                    if self.world.has_component(entity, FireElementC) and not self.world.has_component(targetent, FireElementC):
                        self.world.add_component(targetent, BurningC(5))

                    if self.world.has_component(entity, IceElementC) and not self.world.has_component(targetent, IceElementC):
                        self.world.add_component(targetent, FrozenC())

                    self.world.remove_component(entity, MyTurnC)

        for entity, comps in self.world.get_components(BumpC):
            self.world.remove_component(entity, BumpC)


class PickupSystem(ECS.System):
    def __init__(self):
        super().__init__()

    def update(self, **args):
        for entity, comps in self.world.get_components(TilePositionC, CarrierC):
            if not self.world.has_component(entity, MyTurnC):
                ePos = comps[0]
                eInv = comps[1]
                for item, comps in self.world.get_components(TilePositionC, PickupC):
                    if len(eInv.entities) < eInv.capacity:
                        iPos = comps[0]
                        if (iPos.x, iPos.y) == (ePos.x, ePos.y):
                            self.world.remove_component(item, TilePositionC)

                            eInv.entities.append(item)


class AnimationSystem(ECS.System):
    def __init__(self):
        super().__init__()
        self.t_last_frame = 0
        self.start = True

    def update(self, **args):

        self.t_last_frame += args["t_frame"]

        numFrames = self.t_last_frame // ANIMATION_RATE
        if self.start:
            numFrames += 1
            self.start = False

        self.t_last_frame = self.t_last_frame % ANIMATION_RATE

        for entity, comps in self.world.get_components(AnimationC, RenderC):
            Anim = comps[0]
            Render = comps[1]

            animation = Anim.animations["idle"]
            if self.world.has_component(entity, MyTurnC):
                animation = Anim.animations["ready"]
            if self.world.has_component(entity, InitiativeC):
                if self.world.entity_component(entity, InitiativeC).nextturn <= self.world.entity_component(self.world.tags.player, InitiativeC).nextturn:
                    animation = Anim.animations["ready"]

            if Anim.current_animation != animation:
                Anim.current_animation = animation
                Anim.pos = 0
            else:
                Anim.pos = int((Anim.pos + numFrames) %
                               len(Anim.current_animation))

            Render.imagename = Anim.current_animation[Anim.pos]


# MAIN

def get_input():
    # ----------------------------------- INPUTS ----
    keypress = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            leave()

        if event.type == pygame.KEYDOWN:
            keypress = event.key

            if event.key == pygame.K_ESCAPE:
                leave()

            if event.key == pygame.K_w or event.key == pygame.K_UP:
                keypress = UP

            if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                keypress = LEFT

            if event.key == pygame.K_s or event.key == pygame.K_DOWN:
                keypress = DOWN

            if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                keypress = RIGHT

    return keypress


def main():

    while True:

        ms = clock.tick(60)
        fps = clock.get_fps()
        if fps != 0:
            avgms = 1000/fps
        else:
            avgms = ms

        screen.fill(BLACK)

        keypress = get_input()

        if keypress == pygame.K_MINUS:  # Zooming out
            game.camera.zoom(-20)

        if keypress == pygame.K_EQUALS:  # Zooming in
            game.camera.zoom(20)

        ui.send_event(("input", ui.get_focus(), keypress))

        done = False
        t_frame = ms
        while not done:
            game.world.update(playerinput=None, t_frame=t_frame)
            t_frame = 0
            try:
                for entity, component in game.world.get_component(MyTurnC):
                    if entity == game.world.tags.player:
                        done = True
            except:
                pass

        renderer.t += ms
        ui.send_event(("update", avgms))
        ui.draw_menus()

        renderer.draw_text(screen, (200, 50, 50), (0, 0),
                           "FPS: " + str(int(fps)), 10)
        renderer.draw_text(screen, (200, 50, 50), (0, 12),
                           "TOTAL IMAGES: " + str(renderer.total_images), 10)
        pygame.display.update()


if __name__ == "__main__":
    clock = pygame.time.Clock()

    # VARIABLES
    if FULLSCREEN_MODE:
        infoObject = pygame.display.Info()
        WIDTH = infoObject.current_w
        HEIGHT = infoObject.current_h
        screen = pygame.display.set_mode(
            (WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
    else:
        WIDTH = 1200
        HEIGHT = 800
        screen = pygame.display.set_mode((WIDTH, HEIGHT))

    MENU_SCALE = round(WIDTH/600)

    # Initialising audio
    audio = {}
    for au in glob.glob(AUDIO+"*.wav"):
        auname = au[len(AUDIO):-4]
        audio[auname] = pygame.mixer.Sound(au)

    game = Game()

    game.world.add_system(GridSystem())
    game.world.add_system(InitiativeSystem())

    game.world.add_system(PlayerInputSystem())
    game.world.add_system(AISystem())
    game.world.add_system(FreezingSystem())
    game.world.add_system(BumpSystem())
    game.world.add_system(PickupSystem())

    game.world.add_system(AnimationSystem())

    game.generate_level()

    game.world.tags.focus = game.world.tags.player = game.world.create_entity(
        RenderC("magnum"),
        TilePositionC(20, 20),
        PlayerInputC(),
        MovementC(),
        InitiativeC(1),
        BlockerC(),
        HealthC(50),
        CarrierC(10),
        AttackC(5)
    )

    renderer = Renderer(game)
    ui = UI()
    ui.add_menu(MainMenu(game), focus=True)

    # Playing music
    pygame.mixer.music.load(random.choice(glob.glob(MUSIC+"*")))
    pygame.mixer.music.set_volume(MUSIC_VOLUME)
    pygame.mixer.music.play(-1)

    main()
    # profile.run('main()')

    # VV Do this to profile VV
    # py -m cProfile -s tottime  <NAME OF FILE>
