'''
GIM Descent 4

James Lecomte

To do:
- Make enemies do different things when attacking ie. goblins explode when attacking

- Maybe implement an event system, where Systems emit events which other Systems recieve

- Fix the grid cache system
 - I think this is done


'''

# VV Do this to profile VV
# py -m cProfile -s tottime gim.pyw

import glob
import random
import sys
from math import hypot

import pygame

import ecs


FULLSCREEN_MODE = True
MUSIC_VOLUME = 1


pygame.mixer.pre_init(44100, -16, 8, 2048)
pygame.init()
pygame.mixer.init()

#random.seed(1)

# CONSTANTS

TILE_SIZE = 40

FOLDER = "assets/"
IMAGES = FOLDER + "images/"
AUDIO = FOLDER + "audio/"
MUSIC = AUDIO + "music/"
DEFAULT_IMAGES = FOLDER + "images/"

BLACK = (0, 0, 0)
ALMOST_BLACK = (10, 10, 10)
WHITE = (255, 255, 255)
GRAY = (122, 122, 122)
DARK_RED = (150, 0, 0)
DARK_GREEN = (0, 150, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
ORANGE = (255, 170, 50)


LEFT = (-1, 0)
RIGHT = (1, 0)
UP = (0, -1)
DOWN = (0, 1)
DIRECTIONS = (UP, DOWN, LEFT, RIGHT)

# FUCTIONS


def dist(pos1, pos2):
    """Return the distance between 2 points using Pythagoras."""
    return hypot(abs(pos1.x-pos2.x), abs(pos1.y-pos2.y))


def clamp(value, minimum, maximum):
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
        self._ppt = round(MENU_SCALE*1.5)*20
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
        x = (self._pos.x + random.uniform(-self._shake_x, self._shake_x)) * self._ppt / TILE_SIZE
        y = (self._pos.y + random.uniform(-self._shake_y, self._shake_y)) * self._ppt / TILE_SIZE
        rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        rect.center = (x, y)
        return rect

    def get_scale(self):
        """Return scale of camera. Larger number means more zoomed in."""
        return self._ppt / TILE_SIZE

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
        return ((x+0.5)*TILE_SIZE, (y+0.5)*TILE_SIZE)

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
        self.camera = Camera(speed=10)
        self.world = ecs.World(self)

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
                        DestructibleC(),
                    )
                else:
                    if random.randint(1, 45) == 1:      # Creating items
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
                                #ExplosiveC(3)
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


class MenuManager:
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

    def add_menu(self, menu, focus=True):
        """Add a menu instance.

        If focus is True, focus will change to the new menu.
        """
        self.menus.append(menu)
        if focus:
            self.focuses.append(menu)

    def remove_menu(self, menu):
        """Remove a menu instance."""
        self.menus.remove(menu)
        if menu in self.focuses:
            self.unfocus_menu(menu)

    def unfocus_menu(self, menu):
        """Remove a menu from the focuses."""
        self.focuses.remove(menu)

    def get_focus(self):
        """Return which menu is currently being focused on."""
        return self.focuses[-1]


class Menu:
    """A class that can be interacted with and drawn to the screen."""

    def __init__(self, game: Game):
        self.game = game

    def get_event(self, event):
        """React to an event.

        An event is a list of arbitrary length.
        The first element of the list is the name of the event.
        """
        raise NotImplementedError

    def draw(self):
        """Draw the menu."""
        raise NotImplementedError


class MainMenuTitle:
    """The game title."""

    def __init__(self):
        self.pos = DynamicPos((WIDTH//2, -200), 0)
        self.y_goal = HEIGHT/2 - 50*MENU_SCALE
        self.speed = 0
        self.shake_x = 0
        self.shake_y = 0
        self.shake = 0
        self.lastshake = 1000/60

    def update(self, delta):
        """Update the title."""
        if self.pos.y < self.y_goal:
            self.speed += delta*0.001
            self.pos.move((self.pos.x, min(self.pos.y+self.speed*delta, self.y_goal)), instant=True)
            if self.pos.y == self.y_goal:
                self.shake = 15*MENU_SCALE
        else:
            if self.shake > 0:
                self.lastshake += delta
                while self.lastshake > 1000/60:
                    self.lastshake -= 1000/60
                    self.shake_x = random.uniform(-self.shake, self.shake)
                    self.shake_y = random.uniform(-self.shake, self.shake)
                    self.shake *= 0.9
                    if self.shake < 1:
                        self.shake = 0

    def draw(self):
        """Draw the title."""
        RENDERER.draw_centered_image(SCREEN, RENDERER.get_image(
            name="title", scale=MENU_SCALE/2), (self.pos.x+self.shake_x, self.pos.y+self.shake_y))


class MainMenu(Menu):
    """The starting menu of the game."""

    def __init__(self, game):
        super().__init__(game)
        self.title = MainMenuTitle()
        self.active = False
        if WIDTH/1920 > HEIGHT/1080:  # Logic to get title image to scale on differently sized monitors
            self.title_background = pygame.transform.scale(RENDERER.get_image(name="title_background"), (WIDTH, int(WIDTH/1920*1080)))
        else:
            self.title_background = pygame.transform.scale(RENDERER.get_image(name="title_background"), (int(HEIGHT/1080*1920), HEIGHT))

    def get_event(self, event):
        if event[0] == "update":
            delta = event[1]
            self.title.update(delta)

            if not self.active:
                if self.title.pos.y == self.title.y_goal:
                    self.active = True
        if event[0] == "input" and event[1] == self:
            keypress = event[2]
            if self.active:
                if keypress:
                    UI.add_menu(GameMenu(self.game))
                    UI.remove_menu(self)

    def draw(self):
        # Logic to get title image to show in the right place
        RENDERER.draw_image(SCREEN, self.title_background,
                            (0, HEIGHT-self.title_background.get_height()))
        # for different sized sceens
        if self.active:
            RENDERER.draw_text(SCREEN, (random.randint(0, 5)*50, 122, 0), (WIDTH //
                                                                           2, HEIGHT//2), "Press any key to begin", MENU_SCALE*5, centered=True)
        self.title.draw()


class GameMenu(Menu):
    """The main game menu. Takes player input and draws the game."""

    def __init__(self, game):
        super().__init__(game)
        self._floor_cache = None
        self._zoom_cache = 0

    def get_event(self, event):
        if event[0] == "update":
            delta = event[1]
            cameragoal = self.game.world.entity_component(
                self.game.world.tags.focus, TilePositionC)
            cameragoal = self.game.camera.tile_to_camera_pos(
                cameragoal.x, cameragoal.y)
            self.game.camera.update(delta, cameragoal)
        if event[0] == "input" and event[1] is self:
            keypress = event[2]
            if keypress == pygame.K_z:
                UI.add_menu(Inventory(self.game))
            if keypress in DIRECTIONS:
                self.game.world.update(playerinput=keypress, t_frame=0)

    def draw(self):
        camerarect = self.game.camera.get_rect()
        camerazoom = self.game.camera.get_zoom()
        camerascale = camerazoom/TILE_SIZE

        if self._zoom_cache != camerazoom:
            self._zoom_cache = camerazoom

            gridwidth = self.game.world.get_system(GridSystem).gridwidth
            gridheight = self.game.world.get_system(GridSystem).gridheight

            self._floor_cache = pygame.surface.Surface(
                (gridwidth*camerazoom, gridheight*camerazoom))
            for x in range(0, gridwidth):
                for y in range(0, gridheight):
                    self._floor_cache.blit(RENDERER.get_image(
                        name="floor", scale=camerascale), (x*camerazoom, y*camerazoom))

        SCREEN.blit(self._floor_cache, (0, 0), (camerarect.x,
                                                camerarect.y, camerarect.width, camerarect.height))

        for entity, comps in self.game.world.get_components(RenderC, TilePositionC):
            pos = comps[1]

            pixelpos = self.game.camera.tile_to_pixel_pos(pos.x, pos.y)
            rect = pygame.Rect(0, 0, camerazoom*1.5, camerazoom*1.5)
            rect.center = pixelpos

            drawing = rect.colliderect(camerarect)

            if drawing:
                image = RENDERER.entity_image(entity, scale=camerascale)
                pixelpos = (pixelpos[0] - camerarect.x,
                            pixelpos[1] - camerarect.y)
                RENDERER.draw_centered_image(SCREEN, image, pixelpos)


                if self.game.world.has_component(entity, FrozenC):
                    RENDERER.draw_centered_image(SCREEN, RENDERER.get_image(
                        name="ice-cube", scale=camerascale), pixelpos)

                icon_pos = [pixelpos[0] - camerazoom*0.25, pixelpos[1] + camerazoom*0.2]
                if self.game.world.has_component(entity, FireElementC):
                    RENDERER.draw_centered_image(SCREEN, RENDERER.get_image(name="elementFire", scale=camerascale), icon_pos)
                    icon_pos[0] += camerazoom*0.2
                if self.game.world.has_component(entity, IceElementC):
                    RENDERER.draw_centered_image(SCREEN, RENDERER.get_image(name="elementIce", scale=camerascale), icon_pos)
                    icon_pos[0] += camerazoom*0.2

                if self.game.world.has_component(entity, ExplosiveC):
                    explosive = self.game.world.entity_component(entity, ExplosiveC)
                    if explosive.primed:
                        RENDERER.draw_centered_image(SCREEN, RENDERER.get_image(name="explosive", scale=camerascale), icon_pos)
                        text_pos = (icon_pos[0], icon_pos[1]-camerazoom*0.3)
                        RENDERER.draw_text(SCREEN, WHITE, text_pos, str(explosive.fuse), 10 * camerascale, centered=True)
                        icon_pos[0] += camerazoom*0.2

                if self.game.world.has_component(entity, FreeTurnC):
                    freeturn = self.game.world.entity_component(entity, FreeTurnC)
                    RENDERER.draw_centered_image(SCREEN, RENDERER.get_image(name="free-turn", scale=camerascale), icon_pos)
                    text_pos = (icon_pos[0], icon_pos[1]-camerazoom*0.3)
                    RENDERER.draw_text(SCREEN, WHITE, text_pos, str(freeturn.life), 10 * camerascale, centered=True)
                    icon_pos[0] += camerazoom*0.2


                if self.game.world.has_component(entity, HealthC):    # Healthbar
                    health = self.game.world.entity_component(entity, HealthC)
                    barrect = pygame.Rect(pixelpos[0] - camerazoom*0.35, pixelpos[1] + camerazoom*0.4, camerazoom*0.7, camerazoom*0.05)
                    pygame.draw.rect(SCREEN, ALMOST_BLACK, barrect.inflate(camerazoom*0.1, camerazoom*0.1))
                    try:
                        pygame.draw.rect(SCREEN, DARK_GREEN, (barrect.topleft, (barrect.width*(health.current / health.max), barrect.height)))
                    except ZeroDivisionError:
                        pass


class Inventory(Menu):
    """Main inventory menu."""

    def __init__(self, game):
        super().__init__(game)
        self.cursorpos = [0, 0]
        self.size = [2, 5]
        self.pos = DynamicPos(
            (-TILE_SIZE*MENU_SCALE*2-21, HEIGHT/2-TILE_SIZE*MENU_SCALE*3), speed=10)
        self.show()

    def show(self):
        """Tell inventory to move onscreen."""
        self.pos.move((40, self.pos.y))

    def hide(self):
        """Tell inventory to move offscreen."""
        self.pos.move((-TILE_SIZE*MENU_SCALE*2-21, self.pos.y))

    def get_event(self, event):

        if event[0] == "update":
            delta = event[1]
            self.pos.update(delta)
            if self.pos.x < -TILE_SIZE*MENU_SCALE*2-20:
                UI.remove_menu(self)

        if event[0] == "input" and event[1] is self:
            keypress = event[2]
            if keypress == pygame.K_x:
                UI.unfocus_menu(self)
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
                    self.game.world.tags.player, InventoryC).contents
                if itempos < len(items):
                    UI.add_menu(InventoryOptions(self.game, items[itempos]))

    def draw(self):
        drawposx = round(self.pos.x)
        drawposy = round(self.pos.y)

        pygame.draw.rect(SCREEN, BLACK, (drawposx-5*MENU_SCALE, drawposy-5*MENU_SCALE, TILE_SIZE *
                                         self.size[0]*MENU_SCALE+10*MENU_SCALE, TILE_SIZE*self.size[1]*MENU_SCALE+10*MENU_SCALE))

        inventory = self.game.world.entity_component(
            self.game.world.tags.player, InventoryC)

        for x in range(self.size[0]):
            for y in range(self.size[1]):
                SCREEN.blit(RENDERER.get_image(name="inventory-slot", scale=MENU_SCALE),
                            (drawposx+TILE_SIZE*MENU_SCALE*x, drawposy+TILE_SIZE*MENU_SCALE*y))

        for i, entity in enumerate(inventory.contents):
            RENDERER.draw_centered_image(SCREEN, RENDERER.entity_image(entity, scale=MENU_SCALE), (
                drawposx+TILE_SIZE*MENU_SCALE*(i//self.size[1]+0.5), drawposy+TILE_SIZE*MENU_SCALE*(i % self.size[1]+0.5)))

        inv_cursor_screenpos = (drawposx + TILE_SIZE * MENU_SCALE *
                                self.cursorpos[0], drawposy + TILE_SIZE * MENU_SCALE * self.cursorpos[1])
        SCREEN.blit(RENDERER.get_image(name="inventory-cursor-box",
                                       scale=MENU_SCALE), inv_cursor_screenpos)

        RENDERER.draw_text(SCREEN, WHITE, (drawposx, drawposy -
                                           19*MENU_SCALE), "Z to select", 5*MENU_SCALE)
        RENDERER.draw_text(SCREEN, WHITE, (drawposx, drawposy -
                                           12*MENU_SCALE), "X to return", 5*MENU_SCALE)


class InventoryOptions(Menu):
    """Option menu for item selected in menu."""

    def __init__(self, game, item):
        super().__init__(game)
        self.item = item
        self.options = []
        if self.game.world.has_component(item, UseEffectC):
            self.options.append("use")
        if self.game.world.has_component(item, ExplosiveC):
            self.options.append("prime")
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
            delta = event[1]
            for pos in self.options_pos:
                pos.update(delta)
        if event[0] == "input" and event[1] is self:
            keypress = event[2]
            if keypress == DOWN:
                self.cursorpos = min(self.cursorpos + 1, self.size-1)
            if keypress == UP:
                self.cursorpos = max(self.cursorpos - 1, 0)
            if keypress == pygame.K_x:
                UI.remove_menu(self)
            if keypress == pygame.K_z:
                UI.remove_menu(self)

                selection = self.options[self.cursorpos]
                if selection == "use":
                    use = self.game.world.entity_component(self.item, UseEffectC)
                    for effect in use.effects:
                        effect[0](self.game.world.tags.player, *effect[1:])
                    if self.game.world.entity_component(self.item, ItemC).consumable:
                        self.game.world.entity_component(self.game.world.tags.player, InventoryC).contents.remove(self.item)
                        self.game.world.delete_entity(self.item)

                if selection == "prime":
                    self.game.world.entity_component(self.item, ExplosiveC).primed = True

                if selection == "throw":
                    UI.add_menu(ThrowOptions(self.game, self.item))

                if selection == "drop":
                    self.game.world.entity_component(self.game.world.tags.player, InventoryC).contents.remove(self.item)
                    self.game.world.remove_component(self.item, StoredC)

                    pos = self.game.world.entity_component(self.game.world.tags.player, TilePositionC)
                    self.game.world.add_component(self.item, TilePositionC(pos.x, pos.y))


    def draw(self):
        for i, pos in enumerate(self.options_pos):
            if i == self.cursorpos:
                pos.move((self.pos[0]+24*MENU_SCALE, pos.y))
            else:
                pos.move((self.pos[0]+12*MENU_SCALE, pos.y))
            pygame.draw.rect(SCREEN, (0, 0, 0), (pos.x, pos.y,
                                                 60*MENU_SCALE, 12*MENU_SCALE), 0)
            RENDERER.draw_text(SCREEN, (255, 255, 255), (pos.x+30*MENU_SCALE, pos.y +
                                                         6*MENU_SCALE), self.options[i], size=5 * MENU_SCALE, centered=True)

        option_cursor_image = RENDERER.get_image(name="cursor", color=(
            255, 255, 255, pygame.BLEND_ADD), scale=MENU_SCALE)
        option_cursor_pos = (self.pos[0], self.pos[1]+12*MENU_SCALE *
                             (self.cursorpos+0.5)+(TILE_SIZE*1.5+10)*MENU_SCALE)
        RENDERER.draw_centered_image(
            SCREEN, option_cursor_image, option_cursor_pos)

        RENDERER.draw_centered_image(SCREEN, RENDERER.get_image(name="inventory-slot", scale=MENU_SCALE*1.5),
                                     (self.pos[0]+TILE_SIZE*MENU_SCALE*0.75, self.pos[1]+TILE_SIZE*MENU_SCALE*0.75))
        RENDERER.draw_centered_image(SCREEN, RENDERER.entity_image(
            self.item, MENU_SCALE*1.5), (self.pos[0]+TILE_SIZE*MENU_SCALE*0.75, self.pos[1]+TILE_SIZE*MENU_SCALE*0.75))


class ThrowOptions(Menu):
    """Throw direction selector once an item has been chosen to throw."""

    def __init__(self, game, item):
        super().__init__(game)
        self.item = item
        self.dir = (0, 0)
        self.targettile = None

        self.help_pos = DynamicPos((WIDTH//2, HEIGHT+MENU_SCALE*2.5), speed=10)
        self.help_pos.move((self.help_pos.x, HEIGHT/2+TILE_SIZE*MENU_SCALE))

    def get_event(self, event):
        if event[0] == "update":
            delta = event[1]
            self.help_pos.update(delta)
            if self.help_pos.y > HEIGHT+MENU_SCALE*2.5:
                UI.remove_menu(self)
        if event[0] == "input" and event[1] is self:
            keypress = event[2]
            if keypress == pygame.K_x:
                UI.remove_menu(self)
                UI.add_menu(InventoryOptions(self.game, self.item))

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
                    if not self.game.world.get_system(GridSystem).on_grid(self.targettile):
                        self.targettile[0] -= self.dir[0]
                        self.targettile[1] -= self.dir[1]
                        hitblocker = True
                    if self.game.world.get_system(GridSystem).get_blocker_at(self.targettile) != 0:
                        hitblocker = True
                    if distance == 5:
                        hitblocker = True

            if keypress == pygame.K_z:
                if self.targettile is not None:
                    self.game.world.entity_component(self.game.world.tags.player, InventoryC).contents.remove(self.item)
                    self.game.world.remove_component(self.item, StoredC)
                    self.game.world.add_component(self.item, TilePositionC(*self.targettile))

                    target = self.game.world.get_system(
                        GridSystem).get_blocker_at(self.targettile)
                    if target:
                        if self.game.world.has_component(self.item, UseEffectC):
                            use = self.game.world.entity_component(
                                self.item, UseEffectC)
                            for effect in use.effects:
                                effect[0](target, *effect[1:])
                        if self.game.world.entity_component(self.item, ItemC).consumable:
                            self.game.world.delete_entity(self.item)

                    UI.remove_menu(self)

    def draw(self):
        if UI.get_focus() == self:
            RENDERER.draw_centered_image(SCREEN, RENDERER.entity_image(self.item, scale=self.game.camera.get_scale(
            )), (WIDTH//2+self.dir[0]*self.game.camera.get_zoom()/2, HEIGHT//2+self.dir[1]*self.game.camera.get_zoom()/2))
            if self.targettile is not None:
                RENDERER.draw_centered_image(SCREEN, RENDERER.get_image(
                    name="crosshair", scale=self.game.camera.get_scale()), self.game.camera.tile_to_screen_pos(*self.targettile))
        RENDERER.draw_text(SCREEN, (170, 170, 170), (self.help_pos.x,
                                                     self.help_pos.y), "Pick a direction", 5*MENU_SCALE, centered=True)
        RENDERER.draw_text(SCREEN, (255, 255, 255), (self.help_pos.x,
                                                     self.help_pos.y+7*MENU_SCALE), "Z to throw", 5*MENU_SCALE, centered=True)
        RENDERER.draw_text(SCREEN, (255, 255, 255), (self.help_pos.x, self.help_pos.y +
                                                     14*MENU_SCALE), "X to cancel", 5*MENU_SCALE, centered=True)


class Renderer:
    """Rendering wrapper which stores cached surfaces."""
    BLINK_RATE = 250
    SPECIAL_CHARS = {":": "col", "-": "dash", ".": "dot",
                     "!": "exc", "/": "fwdslash", "?": "que", " ": "space"}

    def __init__(self):
        self.images = {}
        self.imported_images = {}
        self.total_images = 0
        self.t_elapsed = 0
        self.world = None

    def get_image(self, **args):
        """Get an image surface from the cache. If it does not exist, the image is created.

        Optional modifier parameters like scale and color can be used.
        """
        if "scale" not in args:
            args["scale"] = 1

        key = str(args)

        if key not in self.images:
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
            except pygame.error:
                image = pygame.image.load(
                    DEFAULT_IMAGES+name+".png").convert_alpha()
            self.imported_images[name] = image

        return self.imported_images[name].copy()

    def entity_image(self, entity, scale):
        """Return the current image of an entity referred to by its id."""
        color = [0, 0, 0]
        if self.world.has_component(entity, FireElementC) or self.world.has_component(entity, BurningC):
            color[0] += 100
        if self.world.has_component(entity, IceElementC):
            color[0] += 0
            color[1] += 50
            color[2] += 100

        if self.t_elapsed % self.BLINK_RATE < self.BLINK_RATE/2 and entity != self.world.tags.player:
            if self.world.has_component(entity, InitiativeC):
                entity_nextturn = self.world.entity_component(
                    entity, InitiativeC).nextturn
                player_nextturn = self.world.entity_component(
                    self.world.tags.player, InitiativeC).nextturn
                if entity_nextturn <= player_nextturn:
                    color[0] += 50
                    color[1] += 50
                    color[2] += 50

        if any(color):
            img = self.get_image(name=self.world.entity_component(
                entity, RenderC).imagename, scale=scale, color=(color[0], color[1], color[2], pygame.BLEND_ADD))
        else:
            img = self.get_image(name=self.world.entity_component(
                entity, RenderC).imagename, scale=scale)
        return img

    def draw_text(self, surface, color, pos, text, size, centered=False):
        """Draw text to a surface.

        size refers to the height and width of each character in pixels.
        """
        color = (color[0], color[1], color[2], pygame.BLEND_ADD)
        character_width = size * 0.8

        if centered:
            pos = (pos[0] - (len(text)/2) * character_width + 0.1 * size, pos[1] - size * 0.5)

        for i, character in enumerate(text):
            if character in self.SPECIAL_CHARS:
                surface.blit(self.get_image(
                    name="txt_"+self.SPECIAL_CHARS[character], scale=size*0.2, color=color), (pos[0] + i * character_width, pos[1]))
            else:
                surface.blit(self.get_image(
                    name="txt-"+character, scale=size*0.2, color=color), (pos[0] + i * character_width, pos[1]))

    def draw_image(self, surface, image, pos):
        """Blit an image to a surface."""
        surface.blit(image, pos)

    def draw_centered_image(self, surface, image, centerpos):
        """Blit an image to a surface, centering it at centerpos."""
        surface.blit(
            image, (centerpos[0] - image.get_width()//2, centerpos[1] - image.get_height()//2))


# COMPONENTS
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
        self.nextturn = random.randint(1, speed)


class AIC:
    """Tags an entity as controlled by the computer. Stores id of entity to attack."""
    def __init__(self):
        self.target = 0


class RegenC:
    """Tags an entity as able to passively regenerate."""
    def __init__(self):
        self.amount = 1


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


# SYSTEMS


class GridSystem(ecs.System):
    """Stores grid attributes and a grid of blocker entities."""

    def __init__(self):
        super().__init__()
        self.gridwidth = 40
        self.gridheight = 40
        self.blocker_grid = self.blocker_grid = [[0 for y in range(self.gridheight)] for x in range(self.gridwidth)]
        self.grid = self.grid = [[set() for y in range(self.gridheight)] for x in range(self.gridwidth)]
        self._cached_pos = {}

    def on_grid(self, pos):
        """Return True if a position is on the grid."""
        if clamp(pos[0], 0, self.gridwidth-1) == pos[0]:
            if clamp(pos[1], 0, self.gridheight-1) == pos[1]:
                return True
        return False

    def get_blocker_at(self, pos):
        """Get id of blocker entity at a certain position.

        Returns 0 if there is no blocker entity at this position.
        """
        return self.blocker_grid[pos[0]][pos[1]]

    def move_entity(self, entity, pos):
        """Move an entity to a position, raising an error if not possible."""
        entity_pos = self.world.entity_component(entity, TilePositionC)

        if self.blocker_grid[entity_pos.x][entity_pos.y] == entity:
            if self.blocker_grid[pos[0]][pos[1]] == 0:
                self.blocker_grid[entity_pos.x][entity_pos.y] = 0
                self.blocker_grid[pos[0]][pos[1]] = entity

            else:
                raise IndexError("Entity moving to an occupied tile")

        self.grid[entity_pos.x][entity_pos.y].remove(entity)
        entity_pos.x, entity_pos.y = pos
        self.grid[entity_pos.x][entity_pos.y].add(entity)
        self._cached_pos[entity] = pos

    def _remove_pos(self, entity):
        """Remove an entity from the grid."""
        cache_x, cache_y = self._cached_pos[entity]
        self.grid[cache_x][cache_y].remove(entity)
        if self.blocker_grid[cache_x][cache_y] == entity:
            self.blocker_grid[cache_x][cache_y] = 0
        del self._cached_pos[entity]

    def update(self, **args):
        for entity, pos in self.world.get_component(TilePositionC):
            if not entity in self._cached_pos:
                self._cached_pos[entity] = (pos.x, pos.y)
                self.grid[pos.x][pos.y].add(entity)
                if self.world.has_component(entity, BlockerC):
                    self.blocker_grid[pos.x][pos.y] = entity

        for entity in tuple(self._cached_pos):
            if not self.world.has_entity(entity):
                self._remove_pos(entity)
                continue
            if not self.world.has_component(entity, TilePositionC):
                self._remove_pos(entity)
                continue

            pos = self.world.entity_component(entity, TilePositionC)
            if (pos.x, pos.y) != self._cached_pos[entity]:
                cache_x, cache_y = self._cached_pos[entity]
                self._cached_pos[entity] = (pos.x, pos.y)

                self.grid[cache_x][cache_y].remove(entity)
                self.grid[pos.x][pos.y].add(entity)


                if self.blocker_grid[cache_x][cache_y] == entity:
                    self.blocker_grid[cache_x][cache_y] = 0
                    self.blocker_grid[pos.x][pos.y] = entity


class InitiativeSystem(ecs.System):
    """Acts on Initiative components once a turn passes and hands out MyTurn components."""
    def __init__(self):
        super().__init__()
        self.tick = False

    def update(self, **args):

        self.tick = True
        try:
            for _ in self.world.get_component(MyTurnC):
                self.tick = False
        except KeyError:
            pass

        for entity, freeturn in self.world.get_component(FreeTurnC):
            if self.world.has_component(entity, InitiativeC):
                if self.tick:
                    freeturn.life -= 1
                    if freeturn.life <= 0:
                        self.world.remove_component(entity, FreeTurnC)

                    initiative = self.world.entity_component(entity, InitiativeC)
                    initiative.nextturn -= 1
                    if initiative.nextturn <= 0:
                        initiative.nextturn += initiative.speed
                        self.world.add_component(entity, MyTurnC())
                self.tick = False
            else:
                self.world.remove_component(entity, FreeTurnC)

            return

        for entity, initiative in self.world.get_component(InitiativeC):
            if not self.world.has_component(entity, MyTurnC):
                if self.tick:
                    initiative.nextturn -= 1
                if initiative.nextturn <= 0:
                    initiative.nextturn += initiative.speed
                    self.world.add_component(entity, MyTurnC())


class PlayerInputSystem(ecs.System):
    """Interprets input from the player, applying it to all entities with a PlayerInput component."""

    def update(self, **args):
        playerinput = args["playerinput"]
        if playerinput in DIRECTIONS:
            for entity, comps in self.world.get_components(TilePositionC, PlayerInputC, MyTurnC):
                tilepos = comps[0]
                bumppos = (tilepos.x+playerinput[0], tilepos.y+playerinput[1])
                self.world.add_component(entity, BumpC(*bumppos))


class AISystem(ecs.System):
    """Lets all AI controlled entities decide what action to make."""

    def update(self, **args):
        grid = self.world.get_system(GridSystem)

        for entity, comps in self.world.get_components(MovementC, TilePositionC, AIC, MyTurnC):
            movement = comps[0]
            pos = comps[1]
            ai = comps[2]

            playerpos = self.world.entity_component(self.world.tags.player, TilePositionC)
            if dist(pos, playerpos) <= 15:
                ai.target = self.world.tags.player
            else:
                ai.target = 0

            if ai.target:
                targetpos = self.world.entity_component(ai.target, TilePositionC)

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
                    if grid.get_blocker_at((pos.x+movex, pos.y+movey)) in (0, ai.target):
                        moved = True
                        self.world.add_component(entity, BumpC(pos.x+movex, pos.y+movey))

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

                    if grid.get_blocker_at((pos.x+movex, pos.y+movey)) in (0, ai.target):
                        moved = True
                        self.world.add_component(entity, BumpC(pos.x+movex, pos.y+movey))

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
                    if grid.get_blocker_at((pos.x+movex, pos.y+movey)) in (0, ai.target):
                        moved = True
                        self.world.add_component(entity, BumpC(pos.x+movex, pos.y+movey))


class FreezingSystem(ecs.System):
    """Cancels the action of frozen entities attempting to move, defreezing them instead."""

    def update(self, **args):

        try:
            for entity, _ in self.world.get_components(FrozenC, MyTurnC, BumpC):
                self.world.remove_component(entity, FrozenC)
                self.world.remove_component(entity, MyTurnC)
                self.world.entity_component(entity, InitiativeC).nextturn = 1
        except ValueError:
            pass

class BurningSystem(ecs.System):
    """Damages burning players, with the fire dying after a certain amount of time."""

    def update(self, **args):

        if not self.world.get_system(InitiativeSystem).tick:
            return

        for entity, burning in self.world.get_component(BurningC):

            if self.world.has_component(entity, HealthC):
                self.world.create_entity(DamageC(entity, 1))

            burning.life -= 1
            if burning.life <= 0:
                self.world.remove_component(entity, BurningC)


class BumpSystem(ecs.System):
    """Carries out bump actions, then deletes the Bump components."""

    def update(self, **args):
        for entity, comps in self.world.get_components(TilePositionC, BumpC, MyTurnC):
            pos = comps[0]
            bump = comps[1]
            bumppos = (bump.x, bump.y)

            if not self.world.get_system(GridSystem).on_grid(bumppos):
                continue

            targetent = self.world.get_system(GridSystem).get_blocker_at(bumppos)

            if targetent == 0:

                self.world.get_system(GridSystem).move_entity(entity, bumppos)
                self.world.remove_component(entity, MyTurnC)

            else:
                if self.world.has_component(targetent, HealthC) and self.world.has_component(entity, AttackC):
                    if entity == self.world.tags.player or targetent == self.world.tags.player:
                        # The player must be involved for damage to be inflicted in a bump.
                        # This is so that AI don't attack each other by accident.
                        damage = self.world.entity_component(entity, AttackC).damage
                        self.world.create_entity(
                            DamageC(targetent, damage,
                                    burn=self.world.has_component(entity, FireElementC),
                                    freeze=self.world.has_component(entity, IceElementC)
                                   )
                        )

                        if entity == self.world.tags.player:
                            self.game.camera.shake(5)

                        self.world.remove_component(entity, MyTurnC)
        for entity, _ in self.world.get_component(BumpC):
            self.world.remove_component(entity, BumpC)


class ExplosionSystem(ecs.System):
    """Manages explosives and makes anything with an ExplodeC component explode."""

    def update(self, **args):

        if self.world.get_system(InitiativeSystem).tick:
            for entity, explosive in self.world.get_component(ExplosiveC):
                if explosive.primed:
                    explosive.fuse -= 1
                    if explosive.fuse <= 0:
                        self.world.add_component(entity, ExplodeC())


        for entity, explode in self.world.get_component(ExplodeC):
            self.world.delete_entity(entity)

            iterentity = entity
            while self.world.has_component(iterentity, StoredC):  # Getting carrier entity
                iterentity = self.world.entity_component(iterentity, StoredC).carrier

            if self.world.has_component(iterentity, TilePositionC):             # Damaging things around it
                pos = self.world.entity_component(iterentity, TilePositionC)
                for x in range(pos.x - explode.radius, pos.x + explode.radius + 1):
                    for y in range(pos.y - explode.radius, pos.y + explode.radius + 1):
                        if not self.world.get_system(GridSystem).on_grid((x, y)):
                            continue
                        target_entity = self.world.get_system(GridSystem).get_blocker_at((x, y))
                        if target_entity != 0:

                            if self.world.has_component(target_entity, DestructibleC) and not self.world.has_component(target_entity, HealthC):
                                self.world.delete_entity(target_entity)
                            else:
                                self.world.create_entity(
                                    DamageC(target_entity, explode.damage)
                                )

                explosion_distance = dist(pos, self.world.entity_component(self.world.tags.player, TilePositionC))
                if explosion_distance < 10:
                    self.game.camera.shake(40 - explosion_distance * 3)

class DamageSystem(ecs.System):
    """Manages damage events, applying the damage and then deleting the message entity."""

    def update(self, **args):
        for message_entity, damage in self.world.get_component(DamageC):
            if self.world.has_component(damage.target, HealthC):
                targethealth = self.world.entity_component(
                    damage.target, HealthC)

                targethealth.current -= damage.amount
                if damage.target == self.world.tags.player:
                    self.game.camera.shake(5 + damage.amount*2)
                if targethealth.current <= 0:
                    self.world.delete_entity(damage.target)

                if damage.burn and not self.world.has_component(damage.target, FireElementC):
                    self.world.add_component(damage.target, BurningC(5))

                if damage.freeze and not self.world.has_component(damage.target, IceElementC):
                    self.world.add_component(damage.target, FrozenC())

            if self.world.has_component(damage.target, ExplosiveC):
                self.world.entity_component(damage.target, ExplosiveC).primed = True

            self.world.delete_entity(message_entity)

class RegenSystem(ecs.System):
    """Heals creatures with a RegenC component when they are injured."""
    def update(self, **args):
        if self.world.get_system(InitiativeSystem).tick:
            for entity, regen in self.world.get_component(RegenC):
                if self.world.has_component(entity, HealthC):
                    health = self.world.entity_component(entity, HealthC)
                    if health.current < health.max:
                        health.current = min(health.current + regen.amount, health.max)


class PickupSystem(ecs.System):
    """Allows carrier entities to pick up entities with a Pickup component as long it is not their turn."""

    def update(self, **args):
        for entity, comps in self.world.get_components(TilePositionC, InventoryC):
            if not self.world.has_component(entity, MyTurnC):
                pos = comps[0]
                inventory = comps[1]
                for item, item_comps in self.world.get_components(TilePositionC, ItemC):
                    if len(inventory.contents) < inventory.capacity:
                        item_pos = item_comps[0]
                        if (item_pos.x, item_pos.y) == (pos.x, pos.y):
                            self.world.remove_component(item, TilePositionC)
                            self.world.add_component(item, StoredC(entity))
                            inventory.contents.append(item)


class IdleSystem(ecs.System):
    """Makes AI controlled entities idle for a turn if no action was taken."""

    def update(self, **args):
        for entity, _ in self.world.get_components(AIC, MyTurnC):
            self.world.remove_component(entity, MyTurnC)
            if self.world.has_component(entity, InitiativeC):
                self.world.entity_component(entity, InitiativeC).nextturn = 1


class AnimationSystem(ecs.System):
    """Updates Render components on entities with an Animation component."""

    ANIMATION_RATE = 1000/4

    def __init__(self):
        super().__init__()
        self.t_last_frame = 0

    def update(self, **args):

        self.t_last_frame += args["t_frame"]

        frames_elapsed = self.t_last_frame // self.ANIMATION_RATE

        self.t_last_frame = self.t_last_frame % self.ANIMATION_RATE

        for entity, comps in self.world.get_components(AnimationC, RenderC):
            animation = comps[0]
            render = comps[1]

            playing_animation = animation.animations["idle"]

            if self.world.has_component(entity, InitiativeC):
                entity_nextturn = self.world.entity_component(
                    entity, InitiativeC).nextturn
                player_nextturn = self.world.entity_component(
                    self.world.tags.player, InitiativeC).nextturn
                if entity_nextturn <= player_nextturn:
                    playing_animation = animation.animations["ready"]

            if animation.current_animation != playing_animation:
                animation.current_animation = playing_animation
                animation.pos = 0
            else:
                animation.pos = int((animation.pos + frames_elapsed) %
                                    len(animation.current_animation))

            render.imagename = animation.current_animation[animation.pos]


# MAIN

def get_input():
    """Return the key that was just pressed."""
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

    game.world.add_system(AnimationSystem())

    game.generate_level()

    game.world.tags.focus = game.world.tags.player = game.world.create_entity(
        RenderC("magnum"),
        TilePositionC(0, 0),
        PlayerInputC(),
        MovementC(),
        InitiativeC(1),
        BlockerC(),
        HealthC(50),
        InventoryC(10),
        AttackC(5)
    )
    game.world.get_system(GridSystem).update()
    game.teleport_entity(game.world.tags.player, game.world.get_system(GridSystem).gridwidth)

    RENDERER.world = game.world
    UI.add_menu(MainMenu(game))

    debugging = False

    while True:

        delta = CLOCK.tick()
        fps = CLOCK.get_fps()
        if fps != 0:
            avgms = 1000/fps
        else:
            avgms = delta

        SCREEN.fill(BLACK)

        keypress = get_input()

        if keypress == pygame.K_MINUS:  # Zooming out
            if game.camera.get_zoom() > 20:
                game.camera.zoom(-20)

        if keypress == pygame.K_EQUALS:  # Zooming in
            game.camera.zoom(20)

        if keypress == pygame.K_F12:
            debugging = not debugging

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
        UI.draw_menus()

        if debugging:
            print_debug_info(game)

        pygame.display.update()

def print_debug_info(game):
    """Show debug info in the topleft corner."""
    fps = CLOCK.get_fps()
    infos = (
        "FPS: " + str(int(fps)),
        "TOTAL IMAGES: " + str(RENDERER.total_images),
        "NEXTTURN: " + str(game.world.entity_component(game.world.tags.player, InitiativeC).nextturn),
        "TICK: " + str(game.world.get_system(InitiativeSystem).tick)
    )
    for i, info in enumerate(infos):
        RENDERER.draw_text(SCREEN, (200, 50, 50), (0, 12*i), info, 10)


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

UI: MenuManager

if __name__ == "__main__":
    CLOCK = pygame.time.Clock()

    # VARIABLES
    SCREEN, WIDTH, HEIGHT = init_screen()

    MENU_SCALE = round(WIDTH/600)

    # Initialising audio
    SOUNDS = {}
    for au in glob.glob(AUDIO+"*.wav"):
        auname = au[len(AUDIO):-4]
        SOUNDS[auname] = pygame.mixer.Sound(au)

    RENDERER = Renderer()
    UI = MenuManager()

    # Playing music
    pygame.mixer.music.load(random.choice(glob.glob(MUSIC+"*")))
    pygame.mixer.music.set_volume(MUSIC_VOLUME)
    pygame.mixer.music.play(-1)

    main()
