"""Contains the OptionSelect screen."""

import pygame

import constants
import key_input
import widget as wgt

from .scene import Scene


class OptionSelect(Scene):
    """A scene which lets the user pick from a list of options."""
    def __init__(self, options, pos, **kwargs):
        super().__init__(**kwargs)
        self.options = options
        self.pos = pos
        self.cursor_pos = 0
        self.text = self.options_widget = wgt.TextLines(
            renderer=self.game.renderer,
            text=self.options,
            v_spacing=1.6,
            size=constants.MENU_SCALE*5,
            offset=self.pos,
            centered=True
        )

    def handle_input(self, keypress):
        if keypress.has_action(key_input.Action.DOWN):
            self.cursor_pos = min(len(self.options)-1, self.cursor_pos + 1)
            return True

        if keypress.has_action(key_input.Action.UP):
            self.cursor_pos = max(0, self.cursor_pos - 1)
            return True

        if keypress.has_action(key_input.Action.ACCEPT):
            self.emit_signal("selected", self.options[self.cursor_pos])
            return True

    def draw(self, screen):
        x = self.pos[0] - constants.MENU_SCALE * 50
        y = self.pos[1] + constants.MENU_SCALE*8*self.cursor_pos
        color = (*constants.WHITE, pygame.BLEND_ADD)
        cursor_image = self.game.renderer.get_image(name="cursor", color=color, scale=constants.MENU_SCALE)
        self.game.renderer.draw_centered_image(screen, cursor_image, (x, y))
        self.text.draw(screen)
