"""Contains the Settings scene."""

import pygame

import config
import constants
import key_input
import widget as wgt

from .scene import Scene
from .toggle import Toggle


class Settings(Scene):
    """Lets you look at and modify the config file."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = config.Config()
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
                ),
            wgt.TextLines(
                renderer=self.game.renderer,
                text=["This menu is a work in progress.", "Graphics settings will take effect on a game restart."],
                offset=(self.box_rect.centerx, self.box_rect.bottom + constants.MENU_SCALE * 15),
                size=constants.MENU_SCALE*5,
                color=constants.LIGHT_GRAY,
                centered=True
                )
        ]
        self.options = []
        self.option_index = None

        toggle_pos = (self.box_rect.left + 10 * constants.MENU_SCALE, self.box_rect.top + 40 * constants.MENU_SCALE)
        toggle = self.add_child_scene(Toggle, "Fullscreen", toggle_pos, state=self.config.fullscreen_mode)
        toggle.connect_signal("changed_state", lambda x: self.set_setting("fullscreen_mode", x))
        self.options.append(toggle)

    def set_setting(self, setting, value):
        """Set a setting to the specified value."""
        setattr(self.config, setting, value)

    def handle_input(self, keypress):
        if keypress.has_action(key_input.Action.BACK):
            self.config.save_to_file()
            self.remove_scene()
        if keypress.has_action(key_input.Action.UP):
            self._change_option(max(self.option_index-1, 0))
        if keypress.has_action(key_input.Action.DOWN):
            self._change_option(min(self.option_index+1, len(self.options)-1))

        return True

    def update(self, delta):
        if self.option_index is None: # Done like this since if Settings sets this focus in init, Settings focusing afterwards will override it.
            self.option_index = 0
            self.game.set_focus(self.options[0])

    def _change_option(self, index):
        """Change to a different option, unfocusing the last one and focusing the new one."""
        if self.option_index == index:
            return
        self.game.remove_focus(self.options[self.option_index])
        self.option_index = index
        self.game.set_focus(self.options[self.option_index])

    def draw(self, screen):
        pygame.draw.rect(screen, constants.DARK_GRAY, self.box_rect.inflate(self.border_size, self.border_size))
        pygame.draw.rect(screen, constants.ALMOST_BLACK, self.box_rect)
        for widget in self.widgets:
            widget.draw(screen)
