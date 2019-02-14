"""Contains the Debug scene."""

import pygame

import components as c
import constants
import widget as wgt

from .scene import Scene


class Debug(Scene):
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
        if keypress.key == pygame.K_F12:
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
