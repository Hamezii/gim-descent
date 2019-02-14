"""Contains the Toggle Scene."""

import pygame

import constants
import key_input
import widget as wgt

from .scene import Scene


class Toggle(Scene):
    """A toggleable piece of UI which functions like a tickbox."""

    def __init__(self, text, pos, state, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        width = constants.MENU_SCALE * (110 + len(text)*0)
        height = constants.MENU_SCALE * 15
        self.box_rect = pygame.Rect(pos[0]+10 * constants.MENU_SCALE, pos[1], width, height)
        self.state = state
        self.text_widget = wgt.Text(
            renderer=self.game.renderer,
            text=text,
            size=constants.MENU_SCALE*5,
            offset=(self.box_rect.left, self.box_rect.top + 5 * constants.MENU_SCALE),
            color=constants.GRAY
        )

    def handle_input(self, keypress):
        if keypress.has_action(key_input.Action.ACCEPT):
            self.state = not self.state
            self.emit_signal("changed_state", self.state)
            return True

    def draw(self, screen):
        if self is self.game.focus_scene:
            text_x = 20
            image_dict = {"name": "toggle-box-on", "color": (*constants.LIGHT_GRAY, pygame.BLEND_ADD)}
        else:
            text_x = 10
            image_dict = {"name": "toggle-box-off", "color": (*constants.GRAY, pygame.BLEND_ADD)}
        screen.blit(self.game.renderer.get_image(**image_dict, scale=constants.MENU_SCALE), self.box_rect)
        # pos = (self.box_rect.left, self.box_rect.centery)
        # if self is self.game.focus_scene:
        #     pygame.draw.circle(screen, constants.GRAY, pos, constants.MENU_SCALE * 12)
        #     pygame.draw.circle(screen, constants.DARK_GRAY, pos, constants.MENU_SCALE * 8)
        # else:
        #     pygame.draw.circle(screen, constants.DARK_GRAY, pos, constants.MENU_SCALE * 10)
        # pygame.draw.rect(screen, constants.DARK_GRAY, self.box_rect)

        if self.state:
            color = constants.DARK_GREEN
        else:
            color = constants.GRAY
        pos = (self.box_rect.right - 10 * constants.MENU_SCALE, self.box_rect.centery)
        pygame.draw.circle(screen, color, pos, constants.MENU_SCALE * 2)
        self.text_widget.draw(screen, (text_x * constants.MENU_SCALE, 0))
