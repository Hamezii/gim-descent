"""Contains the Dungeon scene."""

import os
import random

import pygame

import audio
import components as c
import constants
import entity_templates
import levelgen
import systems as s
from camera import Camera
from ecs import World

from .debug import Debug
from .hud import HUD
from .inventory import Inventory
from . import main_menu
from .scene import Scene
from .viewport import Viewport


class Dungeon(Scene):
    """A floor of the dungeon. Can perform functions on the ECS."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.world: World = None
        self.camera = Camera(speed=5)
        self.keypress = None

        self.add_child_scene(Viewport)
        self.add_child_scene(HUD)
        self.add_child_scene(Debug)
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
            self.game.change_base_scene(main_menu.MainMenu)

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
        """Save the game state.

        Temporarily disabled.
        """
        pass
        # if self.world is not None: # If there is a world to save
        #     if not self.world.has_component(self.world.tags.player, c.Dead): # If the player is not dead
        #         with open("save.save", "wb") as save_file:
        #             pickle.dump(self.world, save_file)

    def load_game(self):
        """Load the game from where it was last saved.

        Temporarily disabled.
        """
        pass
        # with open("save.save", "rb") as save_file:
        #     self.world = pickle.load(save_file)
        #     self.world.set_game_reference(self)

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
