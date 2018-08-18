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

class MenuManager:
    """Stores all the menu instances.

    Used to update, draw and send messages to the menus.
    """

    def __init__(self, renderer):
        self.renderer = renderer

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

    def add_menu(self, menu, focus=True):
        """Add a menu instance.

        If focus is True, focus will change to the new menu.
        """
        menu.renderer = self.renderer
        menu.menu_manager = self
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

    def __init__(self, game):
        self.game = game
        self.renderer = None
        self.menu_manager = None

    def get_event(self, event):
        """React to an event.

        An event is a list of arbitrary length.
        The first element of the list is the name of the event.
        """
        raise NotImplementedError

    def draw(self, screen):
        """Draw the menu."""
        raise NotImplementedError


class MainMenuTitle:
    """The game title."""

    def __init__(self):
        self.pos = DynamicPos((constants.WIDTH//2, -200), 0)
        self.y_goal = constants.HEIGHT/2 - 50*constants.MENU_SCALE
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

    def draw(self, renderer, screen):
        """Draw the title."""
        image = renderer.get_image(name="title", scale=constants.MENU_SCALE/2)
        renderer.draw_centered_image(screen, image, (self.pos.x+self.shake_x, self.pos.y+self.shake_y))


class MainMenu(Menu):
    """The starting menu of the game."""

    def __init__(self, game):
        super().__init__(game)
        self.title = MainMenuTitle()
        self.animation_done = False
        self.title_background = None

    def get_event(self, event):
        if event[0] == "update":
            delta = event[1]
            self.title.update(delta)

            if not self.animation_done:
                if self.title.pos.y == self.title.y_goal:
                    self.animation_done = True
        if event[0] == "input" and event[1] == self:
            keypress = event[2]
            if self.animation_done:
                if keypress:
                    self.menu_manager.add_menu(GameMenu(self.game))
                    self.menu_manager.remove_menu(self)
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

        self.renderer.draw_image(screen, self.title_background, (0, constants.HEIGHT-self.title_background.get_height()))

        if self.animation_done:
            color = (random.randint(0, 5)*50, 122, 0)
            pos = (constants.WIDTH // 2, constants.HEIGHT//2)
            self.renderer.draw_text(screen, color, pos, "Press any key to begin", constants.MENU_SCALE*5, centered=True)

        self.title.draw(self.renderer, screen)

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
            cameragoal = self.game.camera.tile_to_camera_pos(cameragoal.x, cameragoal.y)
            self.game.camera.update(delta, cameragoal)
        if event[0] == "input":
            keypress = event[2]

            if keypress == pygame.K_ESCAPE:
                self.menu_manager.add_menu(ExitMenu(self.game))

            if event[1] is self:
                if keypress == pygame.K_z:
                    self.menu_manager.add_menu(Inventory(self.game))
                if keypress in constants.DIRECTIONS:
                    self.game.world.update(playerinput=keypress, t_frame=0)

    def draw(self, screen):
        camerarect = self.game.camera.get_rect()
        camerazoom = self.game.camera.get_zoom()
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

            pixelpos = self.game.camera.tile_to_pixel_pos(pos.x, pos.y)
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


        # Drawing HUD

        # Health bar
        health = self.game.world.entity_component(self.game.world.tags.player, c.Health)
        health_color = self._get_health_bar_color(health)

        health_bar_pos = constants.MENU_SCALE*8*4, screen.get_rect().height - constants.MENU_SCALE*8*5
        health_bar_size = constants.MENU_SCALE*8*14, constants.MENU_SCALE*8
        health_bar = pygame.Rect(health_bar_pos, health_bar_size)

        pygame.draw.rect(screen, constants.ALMOST_BLACK, health_bar.inflate(constants.MENU_SCALE*4, constants.MENU_SCALE*4))

        if health.current > 0:
            health_width = health_bar.width * (health.current / health.max)
            pygame.draw.rect(screen, health_color, (health_bar.topleft, (health_width, health_bar.height)))

        health_text_pos = (health_bar.left + 5*constants.MENU_SCALE, health_bar.top - 15*constants.MENU_SCALE)
        self.renderer.draw_text(screen, health_color, health_text_pos, str(health.current), 15*constants.MENU_SCALE)

        level = self.game.world.entity_component(self.game.world.tags.player, c.Level).level_num
        level_text_pos = (health_bar.x, health_bar.bottom + 5*constants.MENU_SCALE)
        self.renderer.draw_text(screen, constants.LIGHT_GRAY, level_text_pos, "Level " + str(level), 10*constants.MENU_SCALE)

        kills = self.game.world.entity_component(self.game.world.tags.player, c.GameStats).kills
        kills_text_pos = (health_bar.x, health_bar.bottom + 17.5*constants.MENU_SCALE)
        self.renderer.draw_text(screen, constants.LIGHT_GRAY, kills_text_pos, "Kills " + str(kills), 10*constants.MENU_SCALE)

    def _get_health_bar_color(self, health_comp):
        """Return what color an entity's health bar should be given its health component."""
        amount_left = health_comp.current / health_comp.max
        if amount_left > 0.5:
            return constants.DARK_GREEN
        if amount_left > 0.2:
            return constants.ORANGE
        return constants.DARK_RED


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
                    self.menu_manager.add_menu(InventoryOptions(self.game, items[itempos]))

    def draw(self, screen):
        drawposx = round(self.pos.x)
        drawposy = round(self.pos.y)

        black_box_pos = (drawposx-5*constants.MENU_SCALE, drawposy-5*constants.MENU_SCALE)
        black_box_size = tuple(self.slot_size * self.size[i] +10*constants.MENU_SCALE for i in range(2))
        pygame.draw.rect(screen, constants.BLACK, (black_box_pos, black_box_size))

        inventory = self.game.world.entity_component(self.game.world.tags.player, c.Inventory)

        inventory_slot = self.renderer.get_image(name="inventory-slot", scale=constants.MENU_SCALE)
        for x in range(self.size[0]):
            for y in range(self.size[1]):
                screen.blit(inventory_slot, (drawposx+self.slot_size*x, drawposy+self.slot_size*y))

        for i, entity in enumerate(inventory.contents):
            pos = (drawposx+self.slot_size*(i//self.size[1]+0.5), drawposy+self.slot_size*(i % self.size[1]+0.5))
            self.game.draw_centered_entity(screen, entity, constants.MENU_SCALE, pos)

        inv_cursor_screenpos = (drawposx + self.slot_size * self.cursorpos[0], drawposy + self.slot_size * self.cursorpos[1])
        screen.blit(self.renderer.get_image(name="inventory-cursor-box", scale=constants.MENU_SCALE), inv_cursor_screenpos)

        self.renderer.draw_text(screen, constants.WHITE, (drawposx, drawposy - 19*constants.MENU_SCALE), "Z to select", 5*constants.MENU_SCALE)
        self.renderer.draw_text(screen, constants.WHITE, (drawposx, drawposy - 12*constants.MENU_SCALE), "X to return", 5*constants.MENU_SCALE)


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
                    self.menu_manager.add_menu(ThrowOptions(self.game, self.item))

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

        if self.game.world.has_component(self.item, c.Describable):
            text_pos = (self.pos[0] + constants.TILE_SIZE * constants.MENU_SCALE * 1.6, self.pos[1])
            describe = self.game.world.entity_component(self.item, c.Describable)
            self.renderer.draw_text(screen, constants.WHITE, text_pos, describe.name, size=10 * constants.MENU_SCALE)
            self.renderer.draw_text(screen, constants.WHITE, (text_pos[0], text_pos[1]+15*constants.MENU_SCALE), describe.desc, size=5 * constants.MENU_SCALE)



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
                self.menu_manager.add_menu(InventoryOptions(self.game, self.item))

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
            itempos = (constants.WIDTH//2+self.dir[0]*self.game.camera.get_zoom()/2, constants.HEIGHT//2+self.dir[1]*self.game.camera.get_zoom()/2)
            self.game.draw_centered_entity(screen, self.item, self.game.camera.get_scale(), itempos)
            if self.targettile is not None:
                self.renderer.draw_centered_image(screen, self.renderer.get_image(
                    name="crosshair", scale=self.game.camera.get_scale()), self.game.camera.tile_to_screen_pos(*self.targettile))

        text_size = 5*constants.MENU_SCALE
        y_off = 0
        self.renderer.draw_text(screen, constants.LIGHT_GRAY, (self.help_pos.x, self.help_pos.y), "Pick a direction", text_size, centered=True)
        y_off += 7*constants.MENU_SCALE
        self.renderer.draw_text(screen, constants.WHITE, (self.help_pos.x, self.help_pos.y + y_off), "Z to throw", text_size, centered=True)
        y_off += 7*constants.MENU_SCALE
        self.renderer.draw_text(screen, constants.WHITE, (self.help_pos.x, self.help_pos.y + y_off), "X to cancel", text_size, centered=True)
