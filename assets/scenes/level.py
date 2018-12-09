"""Contains the Level scene."""

import random

import pygame

import audio
import components as c
import constants
import systems as s
from camera import Camera
from ecs import World

from .debug import Debug
from .hud import HUD
from .inventory import Inventory
from .scene import Scene
from .viewport import Viewport
from .level_select import LevelSelect
from .game_over import GameOver


class Level(Scene):
    """The current level. Contains a collection of scenes and helper functions which interact with the ECS."""

    def __init__(self, world, **kwargs):
        super().__init__(**kwargs)
        self.world: World = world
        self.world.set_game_reference(self)
        self.camera = Camera(speed=5, rect_size=(self.game.width, self.game.height))
        self.camera.set_target(self.__player_pos_to_camera_pos(), direct=True)

        self.keypress = None
        self.player_alive = True

        self.add_child_scene(Viewport)
        self.add_child_scene(HUD)
        self.add_child_scene(Debug)
        self.inventory = self.add_child_scene(Inventory)

    def handle_input(self, keypress):
        if keypress == pygame.K_MINUS:  # Zooming out
            if self.camera.get_zoom() > 20:
                self.camera.zoom(-20)
            return True
        if keypress == pygame.K_EQUALS:  # Zooming in
            self.camera.zoom(20)
            return True
        if keypress == pygame.K_z: # Inventory
            # Only open if player does not have Dead component
            if not self.world.has_component(self.world.tags.player, c.Dead):
                self.inventory.show()
            return True
        if keypress in constants.DIRECTIONS: # Caching movement direction
            self.keypress = keypress
            return True

    def update(self, delta):
        if not self.player_alive:
            self.keypress = None
        self.world.process(playerinput=self.keypress, d_t=delta)
        self.keypress = None
        while not self.world.has_component(self.world.tags.player, c.MyTurn) and self.player_alive: # Waiting for input
            self.world.process(playerinput=None, d_t=0)

        # Move the camera towards the player and update it
        cameragoal = self.__player_pos_to_camera_pos()
        self.camera.update(delta, cameragoal)
        # Cut out music when the player is dead
        if self.player_alive:
            if self.world.has_component(self.world.tags.player, c.Dead):
                self.player_alive = False
                if self.game.has_save():
                    self.game.delete_save()
                audio.stop_music()
                self.game.set_focus(self.add_child_scene(GameOver, self.parent, victory=False))

    def __player_pos_to_camera_pos(self):
        """
        Find the tile position of the player and return the
        'pixel' position of the centre of the player (excluding zoom).
        """
        pos = self.world.entity_component(self.world.tags.player, c.TilePosition)
        camera_pos = self.camera.tile_to_camera_pos(pos.x, pos.y)
        return camera_pos

    def select_next_level(self):
        """Open the LevelSelect scene."""
        self.remove_scene()
        self.game.set_focus(self.parent.add_child_scene(LevelSelect))

    def show_win_screen(self):
        """Show the win screen."""
        self.game.remove_focus(self)
        self.game.set_focus(self.add_child_scene(GameOver, self.parent, victory=True))

    def draw_centered_entity(self, surface, entity, scale, pos):
        """Draw an entity, including icons etc.

        Calls Dungeon's method.
        """
        return self.parent.draw_centered_entity(surface, entity, scale, pos)

    def get_health_bar_color(self, health_comp):
        """Return what color an entity's health bar should be given its health component.

        Calls Dungeon's method.
        """
        return self.parent.get_health_bar_color(health_comp)

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
