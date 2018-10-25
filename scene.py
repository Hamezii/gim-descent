"""Contains the GameManager and the Scene classes."""

import os
<<<<<<< HEAD
=======
import pickle
>>>>>>> 262464466c9f513d5fcfba61b887d4aa9b0081cd
import random

import pygame

import audio
import components as c
import constants
import entity_templates
import levelgen
import renderer
import systems as s
import widget as wgt
from camera import Camera
from ecs import World
from misc import leave, DynamicPos


class GameManager:
    """The main game manager class.

    Stores global objects as well as the scene tree.
    """
    def __init__(self):
        self.renderer = renderer.Renderer()
        self.clock = pygame.time.Clock()
        self.t_elapsed = 0
        self.fps = 0

        self.base_scene = None
        self.focus_scene = None

    def change_base_scene(self, scene_type, *args, **kwargs):
        """Replace the scene tree with a base scene given its type and input parameters. Focus on this scene."""
        self.base_scene = scene_type(*args, **kwargs, game=self)
        self.set_focus(self.base_scene)

    def set_focus(self, scene):
        """Set the focused scene."""
        self.focus_scene = scene

    def send_event(self, event_name, *args, **kwargs):
        """Recursively call a function on all scenes in the scene tree."""
        self.base_scene.get_event(event_name, *args, **kwargs)

    def has_save(self):
<<<<<<< HEAD
        """Return True if there is a save file and False otherwise.

        Temporarily disabled.
        """
        pass
        # return os.path.isfile("save.save")
=======
        """Return True if there is a save file and False otherwise."""
        return os.path.isfile("save.save")
>>>>>>> 262464466c9f513d5fcfba61b887d4aa9b0081cd

    def input(self, keypress):
        """Send an input to the currently focused scene.

        Send the input up the tree until it is handled.
        """
        input_scene = self.focus_scene
        input_handled = input_scene.get_input(keypress)
        while (not input_handled) and (input_scene.parent is not None):
            input_scene = input_scene.parent
            input_handled = input_scene.get_input(keypress)

    def update(self):
        """Run a tick of the scenes."""
        delta = self.clock.tick()
        self.t_elapsed += delta
        self.fps = int(self.clock.get_fps())
        self.send_event("update", delta)
<<<<<<< HEAD
=======
    
>>>>>>> 262464466c9f513d5fcfba61b887d4aa9b0081cd
    def draw(self, screen):
        """Draw the whole scene tree, taking into account draw order."""
        self.__draw_scene(screen, self.base_scene)

    def __draw_scene(self, screen, scene):
        """Draw a scene and its child scenes."""
        for child in scene.children:
            if not child.scene_properties["draw_above_parent"]:
                self.__draw_scene(screen, child)
        scene.draw(screen)
        for child in scene.children:
            if child.scene_properties["draw_above_parent"]:
                self.__draw_scene(screen, child)
class Scene:
    """A node in the scene tree."""
    scene_properties = {
        "draw_above_parent": True
    }
    def __init__(self, game, parent=None):
        self.game = game
        self.parent = parent
        self.children = []

    def add_child_scene(self, scene_type, *args, **kwargs):
        """Add a child scene given its type and input parameters."""
        child_scene = scene_type(*args, **kwargs, game=self.game, parent=self)
        self.children.append(child_scene)
        return child_scene

    def remove_scene(self):
        """Remove this scene from the scene tree."""
        if self is self.game.base_scene:
            raise ValueError("Base scene can't be removed, only replaced.")
        if self is self.game.focus_scene:
            self.game.set_focus(self.parent)
        self.parent.children.remove(self)

    def get_event(self, event_name, *args, **kwargs):
        """Call a function on this scene given its name and parameters.

        Call get_event on children.
        """
        function = getattr(self, event_name, None)
        if function is not None:
            function(*args, **kwargs)
        for child in self.children:
            child.get_event(event_name, *args, **kwargs)

    def get_input(self, keypress):
        """Handle a user input.

        Return True if the input was handled.
        """
        pass

    def update(self, delta):
        """Update the current scene given how much time has passed."""
        pass

    def draw(self, screen):
        """Draw this scene to a pygame surface."""
        pass


class MainMenu(Scene):
    """The starting menu of the game."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.animation_done = False
        self.title_background = None

        self.options = ["New game"]
        if self.game.has_save():
            self.options.insert(0, "Continue game")

        self.title = wgt.MainMenuTitle(renderer=self.game.renderer)

        self.cursor_pos = 0

        self.options_widget = wgt.TextLines(
            renderer=self.game.renderer,
            text=self.options,
            v_spacing=1.6,
            size=constants.MENU_SCALE*5,
            offset=(constants.WIDTH // 2, constants.HEIGHT//2),
            centered=True
        )
        self.widgets = [
            self.title
        ]

        audio.play_music()

    def get_input(self, keypress):
        if self.animation_done:

            if keypress == constants.DOWN:
                self.cursor_pos = min(len(self.options)-1, self.cursor_pos + 1)

            if keypress == constants.UP:
                self.cursor_pos = max(0, self.cursor_pos - 1)

            if keypress in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                if self.options[self.cursor_pos] == "New game":
                    self.game.change_base_scene(CharacterSelect)
                if self.options[self.cursor_pos] == "Continue game":
                    self.game.change_base_scene(Dungeon)
                    self.game.base_scene.load_game()

        if keypress == pygame.K_ESCAPE:
            leave()

        return True

    def update(self, delta):
        for widget in self.widgets:
            widget.update(delta)

        if not self.animation_done:
            if self.title.offset[1] == self.title.y_goal:
                self.animation_done = True
                self.widgets.append(self.options_widget)

    def draw(self, screen):
        # Logic to get title background to show in the right place
        # for different sized sceens
        if self.title_background is None:
            # Logic to get title image to scale on differently sized monitors
<<<<<<< HEAD
            if constants.WIDTH/1920 > constants.HEIGHT/1080:
=======
            if constants.WIDTH/1920 > constants.HEIGHT/1080:  
>>>>>>> 262464466c9f513d5fcfba61b887d4aa9b0081cd
                size = (constants.WIDTH, int(constants.WIDTH/1920*1080))
            else:
                size = (int(constants.HEIGHT/1080*1920), constants.HEIGHT)
            self.title_background = pygame.transform.scale(self.game.renderer.get_image(name="title_background"), size)

        screen.blit(self.title_background, (0, constants.HEIGHT-self.title_background.get_height()))

        if self.animation_done:
            x = constants.WIDTH/2 - constants.MENU_SCALE * 50
            y = constants.HEIGHT/2 + constants.MENU_SCALE*8*self.cursor_pos
            color = (*constants.WHITE, pygame.BLEND_ADD)
            cursor_image = self.game.renderer.get_image(name="cursor", color=color, scale=constants.MENU_SCALE)
            self.game.renderer.draw_centered_image(screen, cursor_image, (x, y))

        for widget in self.widgets:
            widget.draw(screen)



class CharacterSelect(Scene):
    """Allows you to choose who you play as. Opens at new game."""
    characters = ("magnum", "mecha", "edward")
    num_characters = 3
    character_desc = (
        "Relies on skill",
        "Armoured guy",
        "Crazy brawler",
    )
    character_detail = (
        ("Default character", "Most playtested"),
        ("Thick armour comes in handy", "Hard to drink potions from it"),
        ("Gets an adreneline rush from killing things", "Cant take many hits")
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cursor_pos = 0
        self.desc_widget = wgt.Text(
            renderer=self.game.renderer,
            size=constants.MENU_SCALE * 10,
            offset=(constants.WIDTH/4, constants.HEIGHT/2 + constants.MENU_SCALE * 45)
        )
        self.detail_widget = wgt.TextLines(
            renderer=self.game.renderer,
            size=constants.MENU_SCALE * 5,
            offset=(constants.WIDTH/4, constants.HEIGHT/2 + constants.MENU_SCALE * 60)
        )

        self.widgets = [
            wgt.Text(
                renderer=self.game.renderer,
                text="Choose your character",
                size=constants.MENU_SCALE * 15,
                offset=(constants.WIDTH / 2, constants.MENU_SCALE * 100),
                centered=True
            ),
            self.desc_widget,
            self.detail_widget
        ]

    def get_input(self, keypress):
        if keypress == constants.RIGHT:
            self.cursor_pos = min(self.cursor_pos+1, 2)

        if keypress == constants.LEFT:
            self.cursor_pos = max(self.cursor_pos-1, 0)

        if keypress == pygame.K_ESCAPE:
            self.game.change_base_scene(MainMenu)

        if keypress == pygame.K_z:
            self.game.change_base_scene(Dungeon)
            dungeon = self.game.base_scene
            dungeon.init_world()
            if self.cursor_pos == 0: # Magnum
                dungeon.world.tags.player = dungeon.world.create_entity(*entity_templates.magnum(0, 0))
            if self.cursor_pos == 1: # Mecha
                dungeon.world.tags.player = dungeon.world.create_entity(*entity_templates.mecha(0, 0))
            if self.cursor_pos == 2: # Edward
                dungeon.world.tags.player = dungeon.world.create_entity(*entity_templates.edward(0, 0))
            dungeon.new_game()
        return True

    def draw(self, screen):
        screen.fill(constants.ALMOST_BLACK)
        cursor_image = self.game.renderer.get_image(name="inventory-cursor-box", scale=constants.MENU_SCALE)

        for i, character in enumerate(self.characters):
            spacing = constants.MENU_SCALE* constants.TILE_SIZE * 2
            character_pos = (constants.WIDTH/2 + spacing*(i - (self.num_characters-1)/2), constants.HEIGHT/2)
            character_image = self.game.renderer.get_image(name=character, scale=constants.MENU_SCALE)
            self.game.renderer.draw_centered_image(screen, character_image, (character_pos))
            if self.cursor_pos == i:
                self.game.renderer.draw_centered_image(screen, cursor_image, (character_pos))

        self.desc_widget.text = self.character_desc[self.cursor_pos]
        self.detail_widget.text = self.character_detail[self.cursor_pos]

        for widget in self.widgets:
            widget.draw(screen)


class Dungeon(Scene):
    """A floor of the dungeon. Can perform functions on the ECS."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.world: World = None
        self.camera = Camera(speed=5)
        self.keypress = None

        self.add_child_scene(Viewport)
        self.add_child_scene(HUD)
        self.add_child_scene(DebugMenu)
        self.inventory = self.add_child_scene(Inventory)

    def get_input(self, keypress):
        if keypress == pygame.K_MINUS:  # Zooming out
            if self.camera.get_zoom() > 20:
                self.camera.zoom(-20)
        if keypress == pygame.K_EQUALS:  # Zooming in
            self.camera.zoom(20)
        if keypress == pygame.K_F10: # Save
            self.save_game()
        if keypress == pygame.K_F11: # Load
            self.load_game()
        if keypress == pygame.K_z: # Inventory
            # Only open if player does not have Dead component
            if not self.world.has_component(self.world.tags.player, c.Dead):
                self.inventory.show()
        if keypress in constants.DIRECTIONS: # Caching movement direction
            self.keypress = keypress
        if keypress == pygame.K_ESCAPE: # Exiting to menu
            self.save_game()
            self.game.change_base_scene(MainMenu)

        return True

    def update(self, delta):
        self.world.process(playerinput=self.keypress, d_t=delta)
        self.keypress = None
        while not self.world.has_component(self.world.tags.player, c.MyTurn): # Waiting for input
            self.world.process(playerinput=None, d_t=0)

        # Move the camera towards the player and update it
        cameragoal = self.__player_pos_to_camera_pos()
        self.camera.update(delta, cameragoal)
        # Cut out music when the player is dead
        if self.world.has_component(self.world.tags.player, c.Dead):
            audio.stop_music()

    def is_blinking(self):
        """Return True if blinking images should be lit up at the moment."""
        if self.game.t_elapsed % constants.BLINK_RATE < constants.BLINK_RATE/2:
            return True
        return False

    def __player_pos_to_camera_pos(self):
        """
        Find the tile position of the player and return the
        'pixel' position of the centre of the player (excluding zoom).
        """
        pos = self.world.entity_component(self.world.tags.player, c.TilePosition)
        camera_pos = self.camera.tile_to_camera_pos(pos.x, pos.y)
        return camera_pos

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
            data["blinking"] = self.world.entity_component(entity, c.Render).blinking and self.is_blinking()

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
        entity_surface = self.game.renderer.entity_image(scale, **self.entity_draw_data(entity))
        self.game.renderer.draw_centered_image(surface, entity_surface, pos)

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

    def generate_level(self):
        """Generate a level depending on how far the player is."""

        level_num = self.world.entity_component(self.world.tags.player, c.Level).level_num
        g_sys = self.world.get_system(s.GridSystem)
        gridsize = (g_sys.gridwidth, g_sys.gridheight)
        if level_num == 12:
            level = levelgen.generate_fly_boss_level(gridsize)
        else:
            level = levelgen.generate_random_level(gridsize, level_num)

        for components in level.entities:
            self.world.create_entity(*components)
        self.world.add_component(self.world.tags.player, c.TilePosition(*level.player_start))

        if level_num == 1:
            pos = self.world.entity_component(self.world.tags.player, c.TilePosition)
            for _ in range(3):
                self.world.create_entity(*entity_templates.bomb(pos.x, pos.y))

        self.camera.set_target(self.__player_pos_to_camera_pos(), direct=True)

    def get_health_bar_color(self, health_comp):
        """Return what color an entity's health bar should be given its health component."""
        amount_left = health_comp.current / health_comp.max
        if amount_left > 0.5:
            return constants.GREEN
        if amount_left > 0.2:
            return constants.ORANGE
        return constants.RED

    def delete_save(self):
        """Delete the save file."""
        os.remove("save.save")

    def save_game(self):
<<<<<<< HEAD
        """Save the game state.

        Temporarily disabled.
        """
        pass
=======
        """Save the game state."""
        return "disabled temporarily"
>>>>>>> 262464466c9f513d5fcfba61b887d4aa9b0081cd
        # if self.world is not None: # If there is a world to save
        #     if not self.world.has_component(self.world.tags.player, c.Dead): # If the player is not dead
        #         with open("save.save", "wb") as save_file:
        #             pickle.dump(self.world, save_file)

    def load_game(self):
<<<<<<< HEAD
        """Load the game from where it was last saved.

        Temporarily disabled.
        """
        pass
        # with open("save.save", "rb") as save_file:
        #     self.world = pickle.load(save_file)
        #     self.world.set_game_reference(self)
=======
        """Load the game from where it was last saved."""
        with open("save.save", "rb") as save_file:
            self.world = pickle.load(save_file)
            self.world.set_game_reference(self)
>>>>>>> 262464466c9f513d5fcfba61b887d4aa9b0081cd

    def add_system(self, system_instance):
        """Add a system to the ECS and give it a reference to this game."""
        self.world.add_system(system_instance)
        system_instance.game = self
        system_instance.renderer = self.game.renderer

    def init_world(self):
        """Initialise for a new game."""
        self.world = World()

        self.add_system(s.GameStatsSystem())

        self.add_system(s.GridSystem())
        self.add_system(s.InitiativeSystem())

        self.add_system(s.PlayerInputSystem())
        self.add_system(s.AIFlyWizardSystem())
        self.add_system(s.AISystem())
        self.add_system(s.FreezingSystem())
        self.add_system(s.BurningSystem())
        self.add_system(s.AIDodgeSystem())
        self.add_system(s.BumpSystem())

        self.add_system(s.ExplosionSystem())
        self.add_system(s.DamageSystem())
        self.add_system(s.RegenSystem())
        self.add_system(s.PickupSystem())
        self.add_system(s.IdleSystem())
        self.add_system(s.SplitSystem())
        self.add_system(s.StairsSystem())

        self.add_system(s.AnimationSystem())

        self.add_system(s.DeadSystem())
        self.add_system(s.DeleteSystem())

    def new_game(self):
        """Set the seed then generate a level."""
        if constants.SEED is not None:
            random.seed(constants.SEED)

        self.generate_level()


class DebugMenu(Scene):
    """Prints debug info."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.active = False

        self.debug_text = wgt.TextLines(
            renderer=self.game.renderer,
            size=10,
            v_spacing=1.2,
            color=constants.RED,
            offset=(0, 12),
        )

    def unfocused_input(self, keypress):
        """Respond to player input independent of what scene is being focused on."""
        if keypress == pygame.K_F12:
            self.active = not self.active

    def draw(self, screen):
        if not self.active:
            return
        info = self.get_debug_info()
        self.debug_text.text = info
        self.debug_text.draw(screen)

    def get_debug_info(self):
        """Return a tuple of text for debug info."""
        info = (
            "FPS: " + str(self.game.fps),
            "TOTAL IMAGES: " + str(self.game.renderer.total_images),
            "OBJECTS: " + str(len([*self.parent.world.get_component(c.TilePosition)])),
            "SCENES: " + str(self.__how_many_scenes(self.game.base_scene))
        )
        return info

    def __how_many_scenes(self, scene):
        """Return how many scenes there are below and including this scene.

        Defined recursively.
        """
        amount = 1
        for child in scene.children:
            amount += self.__how_many_scenes(child)
        return amount

class Viewport(Scene):
    """The main dungeon view. Draws what the player can see of the dungeon."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._floor_cache = None
        self._zoom_cache = 0

    def draw(self, screen):
        camerarect = self.parent.camera.get_rect()
        camerazoom = self.parent.camera.get_zoom()
        camerascale = camerazoom/constants.TILE_SIZE

        if self._zoom_cache != camerazoom:
            self._zoom_cache = camerazoom

            gridwidth = self.parent.world.get_system(s.GridSystem).gridwidth
            gridheight = self.parent.world.get_system(s.GridSystem).gridheight

            self._floor_cache = pygame.surface.Surface((gridwidth*camerazoom, gridheight*camerazoom))
            floor_image = self.game.renderer.get_image(name="floor", scale=camerascale)
            for x in range(0, gridwidth):
                for y in range(0, gridheight):
                    self._floor_cache.blit(floor_image, (x*camerazoom, y*camerazoom))

        screen.blit(self._floor_cache, (0, 0), (camerarect.x, camerarect.y, camerarect.width, camerarect.height))

        for entity, comps in self.parent.world.get_components(c.Render, c.TilePosition):
            pos = comps[1]

            pixelpos = self.parent.camera.tile_to_pixel_pos(pos.x, pos.y)
            rect = pygame.Rect(0, 0, camerazoom*1.5, camerazoom*1.5)
            rect.center = pixelpos

            drawing = rect.colliderect(camerarect)

            if drawing:
                pixelpos = (pixelpos[0] - camerarect.x, pixelpos[1] - camerarect.y)
                self.parent.draw_centered_entity(screen, entity, camerascale, pixelpos)

                if self.parent.world.has_component(entity, c.Health):    # Healthbar
                    health = self.parent.world.entity_component(entity, c.Health)
                    barpos = (pixelpos[0] - camerazoom*0.35, pixelpos[1] + camerazoom*0.4)
                    barsize = camerazoom*0.7, camerazoom*0.05
                    barrect = pygame.Rect(barpos, barsize)
                    pygame.draw.rect(screen, constants.ALMOST_BLACK, barrect.inflate(camerazoom*0.1, camerazoom*0.1))
                    if health.current > 0:
                        health_width = barrect.width*(health.current / health.max)
                        pygame.draw.rect(screen, self.parent.get_health_bar_color(health), (barpos, (health_width, barrect.height)))


class HUD(Scene):
    """Displays information about your health, etc."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        health_bar_pos = constants.MENU_SCALE*8*4, constants.HEIGHT - constants.MENU_SCALE*8*5
        health_bar_size = constants.MENU_SCALE*8*14, constants.MENU_SCALE*8
        self.health_bar = pygame.Rect(health_bar_pos, health_bar_size)

        self.max_health_text = wgt.Text(
            renderer=self.game.renderer,
            size=15*constants.MENU_SCALE
        )

        self.health_text = wgt.Text(
            renderer=self.game.renderer,
            size=15*constants.MENU_SCALE,
            offset=(self.health_bar.left + 5*constants.MENU_SCALE, self.health_bar.top - 15*constants.MENU_SCALE)
        )

        self.level_text = wgt.Text(
            renderer=self.game.renderer,
            size=10*constants.MENU_SCALE,
            offset=(self.health_bar.x, self.health_bar.bottom + 5*constants.MENU_SCALE),
            color=constants.LIGHT_GRAY
        )

        self.kills_text = wgt.Text(
            renderer=self.game.renderer,
            size=10*constants.MENU_SCALE,
            offset=(self.health_bar.x, self.health_bar.bottom + 17.5*constants.MENU_SCALE),
            color=constants.LIGHT_GRAY
        )

        self.time_text = wgt.Text(
            renderer=self.game.renderer,
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

    def unfocused_input(self, keypress):
        """Respond to an input independent of what scene is currently being focused on."""
        if keypress == pygame.K_F8:
            self.remove_scene()

    def draw(self, screen):
        # Health bar
        health = self.parent.world.entity_component(self.parent.world.tags.player, c.Health)
        health_color = self.parent.get_health_bar_color(health)

        border_rect = self.health_bar.inflate(constants.MENU_SCALE*4, constants.MENU_SCALE*4)
        pygame.draw.rect(screen, constants.ALMOST_BLACK, border_rect)

        if health.current > 0:
            health_width = self.health_bar.width * (health.current / health.max)
            pygame.draw.rect(screen, health_color, (self.health_bar.topleft, (health_width, self.health_bar.height)))



        # Widgets

        self.health_text.color = self.max_health_text.color = health_color
        self.health_text.text = str(health.current)

        self.max_health_text.text = "/"+str(health.max)
        text_len = len(self.max_health_text.text)
        self.max_health_text.offset = (self.health_bar.right + (1 - text_len*4)*3*constants.MENU_SCALE, self.health_bar.top - 15*constants.MENU_SCALE)

        kills = self.parent.world.entity_component(self.parent.world.tags.player, c.GameStats).kills
        self.kills_text.text = "Kills " + str(kills)

        time = self.parent.world.entity_component(self.parent.world.tags.player, c.GameStats).time
        time_s = str(int(time % 60))
        if len(time_s) == 1:
            time_s = "0" + time_s
        time_m = str(int(time // 60))

        self.time_text.text = "Time " + time_m + ":" + time_s

        level = self.parent.world.entity_component(self.parent.world.tags.player, c.Level).level_num
        self.level_text.text = "Level " + str(level)

        for widget in self.widgets:
            widget.draw(screen)


class Inventory(Scene):
    """Main inventory menu."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.visible = False
        self.cursorpos = [0, 0]
        self.size = [2, 5]
        self.slot_size = constants.TILE_SIZE*constants.MENU_SCALE
        self.pos = DynamicPos((-self.slot_size*2-21, constants.HEIGHT/2-self.slot_size*3), speed=10)

        self.widgets = (
            wgt.TextLines(
                renderer=self.game.renderer, size=5*constants.MENU_SCALE, offset=(0, - 19*constants.MENU_SCALE),
                text=["Z to select", "X to return"]
            ),
            wgt.ImageGrid(
                renderer=self.game.renderer,
                grid_size=[2, 5],
                image=self.game.renderer.get_image(name="inventory-slot", scale=constants.MENU_SCALE)
            ),
        )

    def get_input(self, keypress):
        handled = False
        if keypress == pygame.K_x:
            handled = True
            self.game.set_focus(self.parent)
            self.hide()

        if keypress in constants.DIRECTIONS:
            handled = True
            audio.play("click3", replace=True)
        if keypress == constants.UP:
            self.cursorpos[1] = max(self.cursorpos[1] - 1, 0)
        if keypress == constants.DOWN:
            self.cursorpos[1] = min(self.cursorpos[1] + 1, self.size[1]-1)
        if keypress == constants.LEFT:
            self.cursorpos[0] = max(self.cursorpos[0] - 1, 0)
        if keypress == constants.RIGHT:
            self.cursorpos[0] = min(self.cursorpos[0] + 1, self.size[0]-1)

        if keypress == pygame.K_z:
            handled = True
            itempos = self.cursorpos[0]*self.size[1]+self.cursorpos[1]
            items = self.parent.world.entity_component(self.parent.world.tags.player, c.Inventory).contents
            if itempos < len(items):
                self.game.set_focus(self.add_child_scene(InventoryOptions, items[itempos]))

        return handled

    def update(self, delta):
        if self.visible or self.game.focus_scene is self:
            self.pos.update(delta)
            if self.pos.x < -self.slot_size*2-20:
                self.visible = False
            else:
                self.visible = True

    def draw(self, screen):
        if not self.visible:
            return

        drawposx = round(self.pos.x)
        drawposy = round(self.pos.y)

        black_box_pos = (drawposx-5*constants.MENU_SCALE, drawposy-5*constants.MENU_SCALE)
        black_box_size = tuple(self.slot_size * self.size[i] +10*constants.MENU_SCALE for i in range(2))
        pygame.draw.rect(screen, constants.BLACK, (black_box_pos, black_box_size))

        inventory = self.parent.world.entity_component(self.parent.world.tags.player, c.Inventory)

        for widget in self.widgets:
            widget.draw(screen, (drawposx, drawposy))

        for i, entity in enumerate(inventory.contents):
            pos = (drawposx+self.slot_size*(i//self.size[1]+0.5), drawposy+self.slot_size*(i % self.size[1]+0.5))
            self.parent.draw_centered_entity(screen, entity, constants.MENU_SCALE, pos)

        inv_cursor_screenpos = (drawposx + self.slot_size * self.cursorpos[0], drawposy + self.slot_size * self.cursorpos[1])
        screen.blit(self.game.renderer.get_image(name="inventory-cursor-box", scale=constants.MENU_SCALE), inv_cursor_screenpos)

    def show(self):
        """Tell inventory to move onscreen."""
        self.pos.move((40, self.pos.y))
        audio.play("snap1", replace=True)
        audio.dim_music()
        self.game.set_focus(self)

    def hide(self):
        """Tell inventory to move offscreen."""
        self.pos.move((-self.slot_size*2-21, self.pos.y))
        audio.play("drop", replace=True)
        audio.undim_music()
        self.game.set_focus(self.parent)




class InventoryOptions(Scene):
    """Option menu for item selected in menu."""

    def __init__(self, item, **kwargs):
        super().__init__(**kwargs)
        self.world = self.parent.parent.world
        self.item = item
        self.options = []
        self.visible = True
        if self.world.has_component(item, c.UseEffect):
            self.options.append("use")
        if self.world.has_component(item, c.Explosive):
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
        if self.world.has_component(self.item, c.Describable):
            text_x = constants.TILE_SIZE * constants.MENU_SCALE * 1.6
            describe = self.world.entity_component(self.item, c.Describable)
            self.widgets.extend((
                wgt.Text(renderer=self.game.renderer, size=10*constants.MENU_SCALE, text=describe.name, offset=(text_x, 0)),
                wgt.Text(renderer=self.game.renderer, size=5*constants.MENU_SCALE, text=describe.desc, offset=(text_x, 15*constants.MENU_SCALE)),
            ))

    def get_input(self, keypress):
        if keypress == constants.DOWN:
            self.cursorpos = min(self.cursorpos + 1, self.size-1)
            audio.play("click2", replace=True)
        if keypress == constants.UP:
            self.cursorpos = max(self.cursorpos - 1, 0)
            audio.play("click2", replace=True)
        if keypress == pygame.K_x:
            self.remove_scene()
            audio.play("drop", replace=True)
        if keypress == pygame.K_z:
            audio.play("snap1", replace=True)

            selection = self.options[self.cursorpos]
            if selection == "use":
                self.remove_scene()
                use = self.world.entity_component(self.item, c.UseEffect)
                if self.world.has_component(self.world.tags.player, c.WeakPotions):
                    for effect in use.effects: # Weak potions for mecha
                        getattr(self.parent.parent, effect[0])(self.world.tags.player, int(effect[1]/2), *effect[2:])
                else:
                    for effect in use.effects: # Normal effect
                        getattr(self.parent.parent, effect[0])(self.world.tags.player, *effect[1:])

                if self.world.entity_component(self.item, c.Item).consumable:
                    self.world.entity_component(self.world.tags.player, c.Inventory).contents.remove(self.item)
                    self.world.delete_entity(self.item)

            if selection == "prime":
                self.world.entity_component(self.item, c.Explosive).primed = True

            if selection == "throw":
                self.visible = False
                throw_scene = self.parent.add_child_scene(ThrowOptions, self.item)
                self.game.set_focus(throw_scene)
                self.remove_scene()

            if selection == "drop":
                self.remove_scene()
                self.world.entity_component(self.world.tags.player, c.Inventory).contents.remove(self.item)
                self.world.remove_component(self.item, c.Stored)

                pos = self.world.entity_component(self.world.tags.player, c.TilePosition)
                self.world.add_component(self.item, c.TilePosition(pos.x, pos.y))

        handled = keypress in (*constants.DIRECTIONS, pygame.K_z, pygame.K_x)
        return handled

    def update(self, delta):
        for pos in self.options_pos:
            pos.update(delta)

    def draw(self, screen):
        if not self.visible:
            return
        for i, pos in enumerate(self.options_pos):
            if i == self.cursorpos:
                pos.move((self.pos[0]+24*constants.MENU_SCALE, pos.y))
            else:
                pos.move((self.pos[0]+12*constants.MENU_SCALE, pos.y))
            pygame.draw.rect(screen, (0, 0, 0), (pos.x, pos.y, 60*constants.MENU_SCALE, 12*constants.MENU_SCALE), 0)
            text_pos = (pos.x+30*constants.MENU_SCALE, pos.y + 6*constants.MENU_SCALE)
            self.game.renderer.draw_text(screen, constants.WHITE, text_pos, self.options[i], size=5 * constants.MENU_SCALE, centered=True)

        option_cursor_image = self.game.renderer.get_image(name="cursor", color=(
            255, 255, 255, pygame.BLEND_ADD), scale=constants.MENU_SCALE)
        option_cursor_pos = (self.pos[0], self.pos[1]+12*constants.MENU_SCALE *
                             (self.cursorpos+0.5)+(constants.TILE_SIZE*1.5+10)*constants.MENU_SCALE)
        self.game.renderer.draw_centered_image(screen, option_cursor_image, option_cursor_pos)

        pos = (self.pos[0] + constants.TILE_SIZE * constants.MENU_SCALE * 0.75, self.pos[1] + constants.TILE_SIZE * constants.MENU_SCALE * 0.75)
        self.game.renderer.draw_centered_image(screen, self.game.renderer.get_image(name="inventory-slot", scale=constants.MENU_SCALE*1.5), pos)
        self.parent.parent.draw_centered_entity(screen, self.item, constants.MENU_SCALE*1.5, pos)

        for widget in self.widgets:
            widget.draw(screen, self.pos)


class ThrowOptions(Scene):
    """Throw direction selector once an item has been chosen to throw."""
    scene_properties = {
        **Scene.scene_properties,
        "draw_above_parent": False
    }
    def __init__(self, item, **kwargs):
        super().__init__(**kwargs)
        self.camera = self.parent.parent.camera
        self.world = self.parent.parent.world
        self.item = item
        self.dir = (0, 0)
        self.targettile = None
        self.droptile = None

        self.help_pos = DynamicPos((constants.WIDTH//2, constants.HEIGHT+constants.MENU_SCALE*2.5), speed=10)
        self.help_pos.move((self.help_pos.x, constants.HEIGHT/2+constants.TILE_SIZE*constants.MENU_SCALE))

        text_args = {
            "renderer":self.game.renderer,
            "size":5*constants.MENU_SCALE,
            "centered":True
        }

        self.help_text = (
            wgt.Text(
                **text_args,
                text="Pick a direction",
                offset=(0, 0),
                color=constants.LIGHT_GRAY
            ),
            wgt.TextLines(
                **text_args,
                text=["Z to throw", "X to cancel"],
                offset=(0, 7*constants.MENU_SCALE)
            )
        )

    def get_input(self, keypress):
        handled = False
        if keypress == pygame.K_x:
            self.game.set_focus(self.parent.add_child_scene(InventoryOptions, self.item))
            self.remove_scene()
            handled = True

        if keypress in constants.DIRECTIONS:
            self.dir = keypress
            playerpos = self.world.entity_component(
                self.world.tags.player, c.TilePosition)
            self.targettile = [playerpos.x, playerpos.y]
            stopped = False
            distance = 0
            while not stopped:
                self.targettile[0] += self.dir[0]
                self.targettile[1] += self.dir[1]
                distance += 1
                if not self.world.get_system(s.GridSystem).on_grid(self.targettile):
                    self.targettile[0] -= self.dir[0]
                    self.targettile[1] -= self.dir[1]
                    distance -= 1
                    stopped = True
                if self.world.get_system(s.GridSystem).get_blocker_at(self.targettile) != 0:
                    distance -= 1
                    stopped = True
                if distance == 5:
                    stopped = True

            self.droptile = [playerpos.x + self.dir[0] * distance, playerpos.y + self.dir[1] * distance]

            handled = True

        if keypress == pygame.K_z:
            if self.droptile is not None:
                self.world.entity_component(self.world.tags.player, c.Inventory).contents.remove(self.item)
                self.world.remove_component(self.item, c.Stored)
                self.world.add_component(self.item, c.TilePosition(*self.droptile))
            if self.targettile is not None:
                target = self.world.get_system(s.GridSystem).get_blocker_at(self.targettile)
                if target:
                    if self.world.has_component(self.item, c.UseEffect):
                        use = self.world.entity_component(self.item, c.UseEffect)
                        for effect in use.effects:
                            getattr(self.game, effect[0])(target, *effect[1:])
                    if self.world.entity_component(self.item, c.Item).consumable:
                        self.world.add_component(self.item, c.Dead())
                self.remove_scene()

            handled = True

        return handled

    def update(self, delta):
        self.help_pos.update(delta)

    def draw(self, screen):
        item_x = constants.WIDTH//2+self.dir[0]*self.camera.get_zoom()/2
        item_y = constants.HEIGHT//2+self.dir[1]*self.camera.get_zoom()/2
        self.parent.parent.draw_centered_entity(screen, self.item, self.camera.get_scale(), (item_x, item_y))
        if self.targettile is not None:
            crosshair = self.game.renderer.get_image(name="crosshair", scale=self.camera.get_scale())
            self.game.renderer.draw_centered_image(screen, crosshair, self.camera.tile_to_screen_pos(*self.targettile))

        for text in self.help_text:
            text.draw(screen, (self.help_pos.x, self.help_pos.y))
