'''
Contains Menus and the MenuManager for Gim Descent.
'''

import random
import sys

import pygame

import audio
import constants
import components as c
from systems import GridSystem


def leave():
    """Close the game."""
    pygame.quit()
    sys.exit(0)

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

class Widget:
    """A UI element which can be reused in the UI."""
    def __init__(self, renderer, offset=(0, 0)):
        self.renderer = renderer
        self.offset = offset

        self.dirty_attributes = []
        self._surface_attributes = None

        #self.redraws = 0 # Used for debugging

        self._draw_surface = None

    def _update_surface(self):
        """Update the draw surface."""
        pass

    def update(self, delta):
        """Update the widget."""
        pass

    def _is_dirty(self):
        """Return True if the surface requires updating."""
        current_attributes = {attr: getattr(self, attr) for attr in self.dirty_attributes}

        if self._surface_attributes is None:
            self._surface_attributes = current_attributes
            return True

        if current_attributes == self._surface_attributes:
            return False

        self._surface_attributes = current_attributes
        return True

    def draw(self, surface, pos=(0, 0)):
        """Draw the widget to a surface."""
        if self._is_dirty():
            #self.redraws += 1
            #print(self.redraws)
            self._update_surface()


        surface.blit(self._draw_surface, [pos[i]+self.offset[i] for i in range(2)])

class MainMenuTitle(Widget):
    """The game title."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._draw_surface = self.renderer.get_image(name="title", scale=constants.MENU_SCALE/2)
        c_x, c_y = self._draw_surface.get_rect().center

        self.offset = [constants.WIDTH//2-c_x, -c_y*2]
        self.y_goal = constants.HEIGHT/2 - 50*constants.MENU_SCALE - 200
        self.speed = 0
        self.shake_x = 0
        self.shake_y = 0
        self.shake = 0
        self.lastshake = 1000/60

    def update(self, delta):
        if self.offset[1] < self.y_goal:
            self.speed += delta*0.001
            self.offset[1] = min(self.offset[1]+self.speed*delta, self.y_goal)
            if self.offset[1] == self.y_goal:
                self.shake = 15*constants.MENU_SCALE
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

    def draw(self, surface, pos=(0, 0)):
        super().draw(surface, (self.shake_x, self.shake_y))

class ImageGrid(Widget):
    """An image."""
    def __init__(self, image=None, grid_size=None, **kwargs):
        super().__init__(**kwargs)

        self._image = image
        self._grid_size = grid_size

    def _update_surface(self):
        image_rect = self._image.get_rect()
        surface_width = image_rect.width * self._grid_size[0]
        surface_height = image_rect.height * self._grid_size[1]
        self._draw_surface = pygame.Surface((surface_width, surface_height))
        for x in range(self._grid_size[0]):
            for y in range(self._grid_size[1]):
                self._draw_surface.blit(self._image, (image_rect.width*x, image_rect.height*y))


class Text(Widget):
    """A line of text."""
    def __init__(self, size=None, color=constants.WHITE, text="", centered=False, **kwargs):
        super().__init__(**kwargs)

        self.size = size
        self.color = color
        self.centered = centered
        self.text = text

        self.dirty_attributes = ("size", "color", "centered", "text")

    def _update_surface(self):
        if self.centered and self._draw_surface is not None:
            center = self._draw_surface.get_rect().center
            self.offset = tuple(self.offset[i]+center[i] for i in range(2))

        self._draw_surface = self.renderer.make_text(self.color, self.text, self.size)

        if self.centered:
            center = self._draw_surface.get_rect().center
            for i in range(2):
                self.offset = tuple(self.offset[i]-center[i]*0.5 for i in range(2))

class MenuManager:
    """Stores all the menu instances.

    Used to update, draw and send messages to the menus.
    """

    def __init__(self, game):
        self.game = game

        self.menus = []
        self.focuses = []

    def send_event(self, event):
        """Send an event to all menus."""
        for menu in self.menus:
            menu.get_event(event)

    def draw_menus(self, screen):
        """Draw all the menus."""
        for menu in self.menus:
            menu.draw(screen)

    def add_menu(self, menu_type, *args, focus=True):
        """Instace and add a menu.

        If focus is True, focus will change to the new menu.
        """
        menu = menu_type(self.game, *args)
        menu.menu_manager = self
        self.menus.append(menu)
        if focus:
            self.focuses.append(menu)

    def remove_all_menus(self):
        """Remove all menu instances."""
        for menu in self.menus:
            self.remove_menu(menu)

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

    def __init__(self, game):
        self.game = game
        self.renderer = game.renderer
        self.menu_manager: MenuManager = None # Set by the ManuManager after instancing

    def get_event(self, event):
        """React to an event.

        An event is a list of arbitrary length.
        The first element of the list is the name of the event.
        """
        raise NotImplementedError

    def draw(self, screen):
        """Draw the menu."""
        raise NotImplementedError

class DebugMenu(Menu):
    """Prints debug info."""

    def __init__(self, game):
        super().__init__(game)

        self.active = False

        self.debug_text = [
            Text(
                renderer=self.renderer,
                size=10,
                color=constants.RED,
                offset=(0, 12*i),
            ) for i in range(3)
        ]

    def get_event(self, event):
        if event[0] == "input":
            keypress = event[2]
            if keypress == pygame.K_F12:
                self.active = not self.active

    def draw(self, screen):
        if not self.active:
            return
        info = self.game.get_debug_info()
        for i, widget in enumerate(self.debug_text):
            widget.text = info[i]
            widget.draw(screen)


class MainMenu(Menu):
    """The starting menu of the game."""

    def __init__(self, game):
        super().__init__(game)
        self.animation_done = False
        self.title_background = None

        self.title = MainMenuTitle(renderer=self.renderer)
        self.options = ("New game", "Load game")

        self.cursor_pos = 0

        self.widgets = [
            self.title
        ]

    def get_event(self, event):
        if event[0] == "update":
            delta = event[1]

            for widget in self.widgets:
                widget.update(delta)

            if not self.animation_done:
                if self.title.offset[1] == self.title.y_goal:
                    self.animation_done = True
                    y = constants.HEIGHT//2
                    for option in self.options:
                        self.widgets.append(
                            Text(
                                renderer=self.renderer,
                                text=option,
                                size=constants.MENU_SCALE*5,
                                offset=(constants.WIDTH // 2, y),
                                centered=True
                            )
                        )
                        y += constants.MENU_SCALE * 8


        if event[0] == "input" and event[1] == self:
            keypress = event[2]
            if self.animation_done:

                if keypress == constants.DOWN:
                    self.cursor_pos = min(1, self.cursor_pos + 1)

                if keypress == constants.UP:
                    self.cursor_pos = max(0, self.cursor_pos - 1)

                if keypress in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                    self.menu_manager.add_menu(GameMenu)
                    self.menu_manager.add_menu(HUD, focus=False)
                    self.menu_manager.add_menu(DebugMenu, focus=False)
                    self.menu_manager.remove_menu(self)
                    if self.options[self.cursor_pos] == "New game":
                        self.game.new_game()
                        self.menu_manager.add_menu(CharacterSelect)
                    if self.options[self.cursor_pos] == "Load game":
                        self.game.load_game()

            if keypress == pygame.K_ESCAPE:
                leave()


    def draw(self, screen: pygame.surface.SurfaceType):
        # Logic to get title background to show in the right place
        # for different sized sceens
        if self.title_background is None:
            if constants.WIDTH/1920 > constants.HEIGHT/1080:  # Logic to get title image to scale on differently sized monitors
                size = (constants.WIDTH, int(constants.WIDTH/1920*1080))
            else:
                size = (int(constants.HEIGHT/1080*1920), constants.HEIGHT)
            self.title_background = pygame.transform.scale(self.renderer.get_image(name="title_background"), size)

        screen.blit(self.title_background, (0, constants.HEIGHT-self.title_background.get_height()))

        if self.animation_done:
            pos = (constants.WIDTH/2 - constants.MENU_SCALE * 50, constants.HEIGHT/2 + constants.MENU_SCALE*8*self.cursor_pos)
            color = (*constants.WHITE, pygame.BLEND_ADD)
            self.renderer.draw_centered_image(screen, self.renderer.get_image(name="cursor", color=color, scale=constants.MENU_SCALE), pos)


        for widget in self.widgets:
            widget.draw(screen)

class CharacterSelect(Menu):
    """Allows you to choose who you play as. Opens at new game."""
    characters = ("magnum", "edward", "sentinel")
    num_characters = 3
    def __init__(self, game):
        super().__init__(game)
        self.cursor_pos = 0
        self.widgets = [
            Text(
                renderer=self.renderer,
                text="Choose your character",
                size=constants.MENU_SCALE * 15,
                offset=(constants.WIDTH / 2, constants.MENU_SCALE * 100),
                centered=True
            )
        ]

    def get_event(self, event):
        if event[0] == "input" and event[1] is self:
            keypress = event[2]

            if keypress == constants.RIGHT:
                self.cursor_pos = min(self.cursor_pos+1, 2)

            if keypress == constants.LEFT:
                self.cursor_pos = max(self.cursor_pos-1, 0)

            if keypress == pygame.K_z:
                self.game.world.entity_component(self.game.world.tags.player, c.Render).imagename = self.characters[self.cursor_pos]
                self.menu_manager.remove_menu(self)

    def draw(self, screen):
        screen.fill(constants.ALMOST_BLACK)
        cursor_image = self.renderer.get_image(name="inventory-cursor-box", scale=constants.MENU_SCALE)

        for i, character in enumerate(self.characters):
            spacing = constants.MENU_SCALE* constants.TILE_SIZE * 2
            x = constants.WIDTH/2 + spacing*(i - (self.num_characters-1)/2)
            self.renderer.draw_centered_image(screen, self.renderer.get_image(name=character, scale=constants.MENU_SCALE), (x, constants.HEIGHT/2))
            if self.cursor_pos == i:
                self.renderer.draw_centered_image(screen, cursor_image, (x, constants.HEIGHT/2))

        for widget in self.widgets:
            widget.draw(screen)

class GameMenu(Menu):
    """The main game menu. Takes player input and draws the game."""

    def __init__(self, game):
        super().__init__(game)
        self._floor_cache = None
        self._zoom_cache = 0

    def get_event(self, event):
        if event[0] == "update":
            delta = event[1]
            cameragoal = self.game.world.entity_component(self.game.world.tags.player, c.TilePosition)
            cameragoal = self.renderer.camera.tile_to_camera_pos(cameragoal.x, cameragoal.y)
            self.renderer.camera.update(delta, cameragoal)
        if event[0] == "input":
            keypress = event[2]

            if keypress == pygame.K_ESCAPE:
                self.menu_manager.add_menu(ExitMenu)

            if keypress == pygame.K_DELETE:
                self.menu_manager.remove_all_menus()
                self.menu_manager.add_menu(MainMenu)

            if event[1] is self:
                if keypress == pygame.K_z:
                    self.menu_manager.add_menu(Inventory)
                if keypress in constants.DIRECTIONS:
                    self.game.world.process(playerinput=keypress, d_t=0)

    def draw(self, screen):
        camerarect = self.renderer.camera.get_rect()
        camerazoom = self.renderer.camera.get_zoom()
        camerascale = camerazoom/constants.TILE_SIZE

        if self._zoom_cache != camerazoom:
            self._zoom_cache = camerazoom

            gridwidth = self.game.world.get_system(GridSystem).gridwidth
            gridheight = self.game.world.get_system(GridSystem).gridheight

            self._floor_cache = pygame.surface.Surface((gridwidth*camerazoom, gridheight*camerazoom))
            for x in range(0, gridwidth):
                for y in range(0, gridheight):
                    self._floor_cache.blit(self.renderer.get_image(name="floor", scale=camerascale), (x*camerazoom, y*camerazoom))

        screen.blit(self._floor_cache, (0, 0), (camerarect.x, camerarect.y, camerarect.width, camerarect.height))

        for entity, comps in self.game.world.get_components(c.Render, c.TilePosition):
            pos = comps[1]

            pixelpos = self.renderer.camera.tile_to_pixel_pos(pos.x, pos.y)
            rect = pygame.Rect(0, 0, camerazoom*1.5, camerazoom*1.5)
            rect.center = pixelpos

            drawing = rect.colliderect(camerarect)

            if drawing:
                pixelpos = (pixelpos[0] - camerarect.x, pixelpos[1] - camerarect.y)
                self.game.draw_centered_entity(screen, entity, camerascale, pixelpos)

                if self.game.world.has_component(entity, c.Health):    # Healthbar
                    health = self.game.world.entity_component(entity, c.Health)
                    barrect = pygame.Rect(pixelpos[0] - camerazoom*0.35, pixelpos[1] + camerazoom*0.4, camerazoom*0.7, camerazoom*0.05)
                    pygame.draw.rect(screen, constants.ALMOST_BLACK, barrect.inflate(camerazoom*0.1, camerazoom*0.1))
                    if health.current > 0:
                        health_width = barrect.width*(health.current / health.max)
                        pygame.draw.rect(screen, self._get_health_bar_color(health), (barrect.topleft, (health_width, barrect.height)))

    def _get_health_bar_color(self, health_comp):
        """Return what color an entity's health bar should be given its health component."""
        amount_left = health_comp.current / health_comp.max
        if amount_left > 0.5:
            return constants.GREEN
        if amount_left > 0.2:
            return constants.ORANGE
        return constants.RED

class HUD(Menu):
    """Displays information about your health, etc."""

    def __init__(self, game):
        super().__init__(game)
        health_bar_pos = constants.MENU_SCALE*8*4, constants.HEIGHT - constants.MENU_SCALE*8*5
        health_bar_size = constants.MENU_SCALE*8*14, constants.MENU_SCALE*8
        self.health_bar = pygame.Rect(health_bar_pos, health_bar_size)

        self.max_health_text = Text(
            renderer=self.renderer,
            size=15*constants.MENU_SCALE
        )

        self.health_text = Text(
            renderer=self.renderer,
            size=15*constants.MENU_SCALE,
            offset=(self.health_bar.left + 5*constants.MENU_SCALE, self.health_bar.top - 15*constants.MENU_SCALE)
        )

        self.level_text = Text(
            renderer=self.renderer,
            size=10*constants.MENU_SCALE,
            offset=(self.health_bar.x, self.health_bar.bottom + 5*constants.MENU_SCALE),
            color=constants.LIGHT_GRAY
        )

        self.kills_text = Text(
            renderer=self.renderer,
            size=10*constants.MENU_SCALE,
            offset=(self.health_bar.x, self.health_bar.bottom + 17.5*constants.MENU_SCALE),
            color=constants.LIGHT_GRAY
        )

        self.time_text = Text(
            renderer=self.renderer,
            size=10*constants.MENU_SCALE,
            offset=(self.health_bar.x + 80 * constants.MENU_SCALE, self.health_bar.bottom + 17.5*constants.MENU_SCALE),
            color=constants.LIGHT_GRAY
        )

        self.widgets = [
            self.max_health_text,
            self.health_text,
            self.level_text,
            self.kills_text,
            self.time_text
        ]

    def get_event(self, event):
        pass

    def draw(self, screen):
        # Health bar
        health = self.game.world.entity_component(self.game.world.tags.player, c.Health)
        health_color = self._get_health_bar_color(health)

        pygame.draw.rect(screen, constants.ALMOST_BLACK, self.health_bar.inflate(constants.MENU_SCALE*4, constants.MENU_SCALE*4))

        if health.current > 0:
            health_width = self.health_bar.width * (health.current / health.max)
            pygame.draw.rect(screen, health_color, (self.health_bar.topleft, (health_width, self.health_bar.height)))



        # Widgets

        self.health_text.color = self.max_health_text.color = health_color
        self.health_text.text = str(health.current)

        self.max_health_text.text = "/"+str(health.max)
        text_len = len(self.max_health_text.text)
        self.max_health_text.offset = (self.health_bar.right + (1 - text_len*4)*3*constants.MENU_SCALE, self.health_bar.top - 15*constants.MENU_SCALE)

        kills = self.game.world.entity_component(self.game.world.tags.player, c.GameStats).kills
        self.kills_text.text = "Kills " + str(kills)

        time = self.game.world.entity_component(self.game.world.tags.player, c.GameStats).time
        time_s = str(int(time % 60))
        if len(time_s) == 1:
            time_s = "0" + time_s
        time_m = str(int(time // 60))

        self.time_text.text = "Time " + time_m + ":" + time_s

        level = self.game.world.entity_component(self.game.world.tags.player, c.Level).level_num
        self.level_text.text = "Level " + str(level)

        for widget in self.widgets:
            widget.draw(screen)

    def _get_health_bar_color(self, health_comp):
        """Return what color an entity's health bar should be given its health component."""
        amount_left = health_comp.current / health_comp.max
        if amount_left > 0.5:
            return constants.GREEN
        if amount_left > 0.2:
            return constants.ORANGE
        return constants.RED


class ExitMenu(Menu):
    """Popup on exit."""
    def __init__(self, game):
        super().__init__(game)
        leave()

    def get_event(self, event):
        pass

    def draw(self, screen):
        pass

class Inventory(Menu):
    """Main inventory menu."""

    def __init__(self, game):
        super().__init__(game)
        self.cursorpos = [0, 0]
        self.size = [2, 5]
        self.slot_size = constants.TILE_SIZE*constants.MENU_SCALE
        self.pos = DynamicPos((-self.slot_size*2-21, constants.HEIGHT/2-self.slot_size*3), speed=10)

        self.widgets = (
            Text(renderer=self.renderer, size=5*constants.MENU_SCALE, text="Z to select", offset=(0, - 19*constants.MENU_SCALE)),
            Text(renderer=self.renderer, size=5*constants.MENU_SCALE, text="X to return", offset=(0, - 12*constants.MENU_SCALE)),
            ImageGrid(renderer=self.renderer, grid_size=[2, 5], image=self.renderer.get_image(name="inventory-slot", scale=constants.MENU_SCALE)),
        )

        self.show()

    def show(self):
        """Tell inventory to move onscreen."""
        self.pos.move((40, self.pos.y))
        audio.play("snap1", replace=True)
        audio.dim_music()

    def hide(self):
        """Tell inventory to move offscreen."""
        self.pos.move((-self.slot_size*2-21, self.pos.y))
        audio.play("drop", replace=True)
        audio.undim_music()

    def get_event(self, event):

        if event[0] == "update":
            delta = event[1]
            self.pos.update(delta)
            if self.pos.x < -self.slot_size*2-20:
                self.menu_manager.remove_menu(self)

        if event[0] == "input" and event[1] is self:
            keypress = event[2]
            if keypress == pygame.K_x:
                self.menu_manager.unfocus_menu(self)
                self.hide()

            if keypress == constants.UP:
                audio.play("click3", replace=True)
                self.cursorpos[1] = max(self.cursorpos[1] - 1, 0)
            if keypress == constants.DOWN:
                audio.play("click3", replace=True)
                self.cursorpos[1] = min(self.cursorpos[1] + 1, self.size[1]-1)

            if keypress == constants.LEFT:
                audio.play("click3", replace=True)
                self.cursorpos[0] = max(self.cursorpos[0] - 1, 0)
            if keypress == constants.RIGHT:
                audio.play("click3", replace=True)
                self.cursorpos[0] = min(self.cursorpos[0] + 1, self.size[0]-1)

            if keypress == pygame.K_z:
                itempos = self.cursorpos[0]*self.size[1]+self.cursorpos[1]
                items = self.game.world.entity_component(self.game.world.tags.player, c.Inventory).contents
                if itempos < len(items):
                    self.menu_manager.add_menu(InventoryOptions, items[itempos])

    def draw(self, screen):
        drawposx = round(self.pos.x)
        drawposy = round(self.pos.y)

        black_box_pos = (drawposx-5*constants.MENU_SCALE, drawposy-5*constants.MENU_SCALE)
        black_box_size = tuple(self.slot_size * self.size[i] +10*constants.MENU_SCALE for i in range(2))
        pygame.draw.rect(screen, constants.BLACK, (black_box_pos, black_box_size))

        inventory = self.game.world.entity_component(self.game.world.tags.player, c.Inventory)

        for widget in self.widgets:
            widget.draw(screen, (drawposx, drawposy))

        for i, entity in enumerate(inventory.contents):
            pos = (drawposx+self.slot_size*(i//self.size[1]+0.5), drawposy+self.slot_size*(i % self.size[1]+0.5))
            self.game.draw_centered_entity(screen, entity, constants.MENU_SCALE, pos)

        inv_cursor_screenpos = (drawposx + self.slot_size * self.cursorpos[0], drawposy + self.slot_size * self.cursorpos[1])
        screen.blit(self.renderer.get_image(name="inventory-cursor-box", scale=constants.MENU_SCALE), inv_cursor_screenpos)


class InventoryOptions(Menu):
    """Option menu for item selected in menu."""

    def __init__(self, game, item):
        super().__init__(game)
        self.item = item
        self.options = []
        if self.game.world.has_component(item, c.UseEffect):
            self.options.append("use")
        if self.game.world.has_component(item, c.Explosive):
            self.options.append("prime")
        self.options.append("throw")
        self.options.append("drop")
        self.size = len(self.options)

        inv_slot_size = constants.TILE_SIZE*constants.MENU_SCALE
        self.pos = (40 + inv_slot_size*2 + 12*constants.MENU_SCALE, constants.HEIGHT/2 - inv_slot_size*3)
        image_bottom = self.pos[1]+inv_slot_size*1.5
        self.options_pos = [DynamicPos((self.pos[0], image_bottom + (10 + i*12)*constants.MENU_SCALE), speed=20) for i in range(self.size)]
        self.cursorpos = 0

        audio.play("snap2", replace=True)

        self.widgets = []
        if self.game.world.has_component(self.item, c.Describable):
            text_x = constants.TILE_SIZE * constants.MENU_SCALE * 1.6
            describe = self.game.world.entity_component(self.item, c.Describable)
            self.widgets.extend((
                Text(renderer=self.renderer, size=10*constants.MENU_SCALE, text=describe.name, offset=(text_x, 0)),
                Text(renderer=self.renderer, size=5*constants.MENU_SCALE, text=describe.desc, offset=(text_x, 15*constants.MENU_SCALE)),
            ))

    def get_event(self, event):
        if event[0] == "update":
            delta = event[1]
            for pos in self.options_pos:
                pos.update(delta)
        if event[0] == "input" and event[1] is self:
            keypress = event[2]
            if keypress == constants.DOWN:
                self.cursorpos = min(self.cursorpos + 1, self.size-1)
                audio.play("click2", replace=True)
            if keypress == constants.UP:
                self.cursorpos = max(self.cursorpos - 1, 0)
                audio.play("click2", replace=True)
            if keypress == pygame.K_x:
                self.menu_manager.remove_menu(self)
                audio.play("drop", replace=True)
            if keypress == pygame.K_z:
                audio.play("snap1", replace=True)

                selection = self.options[self.cursorpos]
                if selection == "use":
                    self.menu_manager.remove_menu(self)
                    use = self.game.world.entity_component(self.item, c.UseEffect)
                    for effect in use.effects:
                        getattr(self.game, effect[0])(self.game.world.tags.player, *effect[1:])
                    if self.game.world.entity_component(self.item, c.Item).consumable:
                        self.game.world.entity_component(self.game.world.tags.player, c.Inventory).contents.remove(self.item)
                        self.game.world.delete_entity(self.item)

                if selection == "prime":
                    self.game.world.entity_component(self.item, c.Explosive).primed = True

                if selection == "throw":
                    self.menu_manager.remove_menu(self)
                    self.menu_manager.add_menu(ThrowOptions, self.item)

                if selection == "drop":
                    self.menu_manager.remove_menu(self)
                    self.game.world.entity_component(self.game.world.tags.player, c.Inventory).contents.remove(self.item)
                    self.game.world.remove_component(self.item, c.Stored)

                    pos = self.game.world.entity_component(self.game.world.tags.player, c.TilePosition)
                    self.game.world.add_component(self.item, c.TilePosition(pos.x, pos.y))


    def draw(self, screen):
        for i, pos in enumerate(self.options_pos):
            if i == self.cursorpos:
                pos.move((self.pos[0]+24*constants.MENU_SCALE, pos.y))
            else:
                pos.move((self.pos[0]+12*constants.MENU_SCALE, pos.y))
            pygame.draw.rect(screen, (0, 0, 0), (pos.x, pos.y, 60*constants.MENU_SCALE, 12*constants.MENU_SCALE), 0)
            text_pos = (pos.x+30*constants.MENU_SCALE, pos.y + 6*constants.MENU_SCALE)
            self.renderer.draw_text(screen, constants.WHITE, text_pos, self.options[i], size=5 * constants.MENU_SCALE, centered=True)

        option_cursor_image = self.renderer.get_image(name="cursor", color=(
            255, 255, 255, pygame.BLEND_ADD), scale=constants.MENU_SCALE)
        option_cursor_pos = (self.pos[0], self.pos[1]+12*constants.MENU_SCALE *
                             (self.cursorpos+0.5)+(constants.TILE_SIZE*1.5+10)*constants.MENU_SCALE)
        self.renderer.draw_centered_image(screen, option_cursor_image, option_cursor_pos)

        pos = (self.pos[0] + constants.TILE_SIZE * constants.MENU_SCALE * 0.75, self.pos[1] + constants.TILE_SIZE * constants.MENU_SCALE * 0.75)
        self.renderer.draw_centered_image(screen, self.renderer.get_image(name="inventory-slot", scale=constants.MENU_SCALE*1.5), pos)
        self.game.draw_centered_entity(screen, self.item, constants.MENU_SCALE*1.5, pos)

        for widget in self.widgets:
            widget.draw(screen, self.pos)


class ThrowOptions(Menu):
    """Throw direction selector once an item has been chosen to throw."""

    def __init__(self, game, item):
        super().__init__(game)
        self.item = item
        self.dir = (0, 0)
        self.targettile = None
        self.droptile = None

        self.help_pos = DynamicPos((constants.WIDTH//2, constants.HEIGHT+constants.MENU_SCALE*2.5), speed=10)
        self.help_pos.move((self.help_pos.x, constants.HEIGHT/2+constants.TILE_SIZE*constants.MENU_SCALE))

        text_args = {
            "renderer":self.renderer,
            "size":5*constants.MENU_SCALE,
            "centered":True
        }

        self.help_text = (
            Text(
                **text_args,
                text="Pick a direction",
                offset=(0, 0),
                color=constants.LIGHT_GRAY
            ),
            Text(
                **text_args,
                text="Z to throw",
                offset=(0, 7*constants.MENU_SCALE)
            ),
            Text(
                **text_args,
                text="X to cancel",
                offset=(0, 14*constants.MENU_SCALE)
            )
        )

    def get_event(self, event):
        if event[0] == "update":
            delta = event[1]
            self.help_pos.update(delta)
            if self.help_pos.y > constants.HEIGHT+constants.MENU_SCALE*2.5:
                self.menu_manager.remove_menu(self)
        if event[0] == "input" and event[1] is self:
            keypress = event[2]
            if keypress == pygame.K_x:
                self.menu_manager.remove_menu(self)
                self.menu_manager.add_menu(InventoryOptions, self.item)

            if keypress in constants.DIRECTIONS:
                self.dir = keypress
                playerpos = self.game.world.entity_component(
                    self.game.world.tags.player, c.TilePosition)
                self.targettile = [playerpos.x, playerpos.y]
                stopped = False
                distance = 0
                while not stopped:
                    self.targettile[0] += self.dir[0]
                    self.targettile[1] += self.dir[1]
                    distance += 1
                    if not self.game.world.get_system(GridSystem).on_grid(self.targettile):
                        self.targettile[0] -= self.dir[0]
                        self.targettile[1] -= self.dir[1]
                        distance -= 1
                        stopped = True
                    if self.game.world.get_system(GridSystem).get_blocker_at(self.targettile) != 0:
                        distance -= 1
                        stopped = True
                    if distance == 5:
                        stopped = True

                self.droptile = [playerpos.x + self.dir[0] * distance, playerpos.y + self.dir[1] * distance]

            if keypress == pygame.K_z:
                if self.droptile is not None:
                    self.game.world.entity_component(self.game.world.tags.player, c.Inventory).contents.remove(self.item)
                    self.game.world.remove_component(self.item, c.Stored)
                    self.game.world.add_component(self.item, c.TilePosition(*self.droptile))
                if self.targettile is not None:
                    target = self.game.world.get_system(GridSystem).get_blocker_at(self.targettile)
                    if target:
                        if self.game.world.has_component(self.item, c.UseEffect):
                            use = self.game.world.entity_component(self.item, c.UseEffect)
                            for effect in use.effects:
                                getattr(self.game, effect[0])(target, *effect[1:])
                        if self.game.world.entity_component(self.item, c.Item).consumable:
                            self.game.world.add_component(self.item, c.Dead())

                    self.menu_manager.remove_menu(self)

    def draw(self, screen):
        if self.menu_manager.get_focus() == self:
            item_x = constants.WIDTH//2+self.dir[0]*self.renderer.camera.get_zoom()/2
            item_y = constants.HEIGHT//2+self.dir[1]*self.renderer.camera.get_zoom()/2
            self.game.draw_centered_entity(screen, self.item, self.renderer.camera.get_scale(), (item_x, item_y))
            if self.targettile is not None:
                self.renderer.draw_centered_image(screen, self.renderer.get_image(
                    name="crosshair", scale=self.renderer.camera.get_scale()), self.renderer.camera.tile_to_screen_pos(*self.targettile))

        for text in self.help_text:
            text.draw(screen, (self.help_pos.x, self.help_pos.y))
