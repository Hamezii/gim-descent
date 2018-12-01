"""Contains the Settings scene."""

import pygame

import audio
import config
import constants
import widget as wgt

from .scene import Scene
from .toggle import Toggle


class Settings(Scene):
    """Lets you look at and modify the config file."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = config.Settings()
        x = self.game.width // 2 - constants.MENU_SCALE * 200
        y = self.game.height // 2 - constants.MENU_SCALE * 120
        width = constants.MENU_SCALE * 400
        height = constants.MENU_SCALE * 240
        self.box_rect = pygame.Rect(x, y, width, height)
        self.border_size = constants.MENU_SCALE * 4

        self.widgets = [
            wgt.Text(
                renderer=self.game.renderer,
                text="Settings",
                offset=(self.box_rect.centerx, self.box_rect.top + constants.MENU_SCALE * 15),
                size=constants.MENU_SCALE*10,
                color=constants.DARK_GREEN,
                centered=True
                )
        ]
        toggle_pos = (self.box_rect.left + 10 * constants.MENU_SCALE, self.box_rect.top + 40 * constants.MENU_SCALE)
        self.toggle = self.add_child_scene(Toggle, "Fullscreen", toggle_pos, state=self.settings.fullscreen_mode)
        self.toggle.connect("changed_state", lambda x: self.set_setting("fullscreen_mode", x))

    def set_setting(self, setting, value):
        """Set a setting to the specified value."""
        setattr(self.settings, setting, value)

    def handle_input(self, keypress):
        self.game.set_focus(self.toggle) # testing
        if keypress == pygame.K_ESCAPE:
            self.settings.save_settings()
            self.remove_scene()
        return True

    def draw(self, screen):
        pygame.draw.rect(screen, constants.DARK_GRAY, self.box_rect.inflate(self.border_size, self.border_size))
        pygame.draw.rect(screen, constants.ALMOST_BLACK, self.box_rect)
        for widget in self.widgets:
            widget.draw(screen)
