"""Contains the GameOptions scene."""

import pygame

import constants

from . import main_menu
from .option_select import OptionSelect
from .scene import Scene


class GameOptions(Scene):
    """An options box that can be opened during the game."""
    V_BORDER = 5
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        x = self.game.width/2 - constants.MENU_SCALE * 55
        y = self.game.height/2 - constants.MENU_SCALE * (2.5 + self.V_BORDER)
        width = constants.MENU_SCALE * 110
        height = constants.MENU_SCALE * (13 + self.V_BORDER * 2)
        self.box_rect = pygame.Rect(x, y, width, height)
        self.option_scene = self.add_child_scene(
            OptionSelect,
            pos=(self.game.width/2, self.game.height/2),
            options=("Resume", "Main Menu")
        )
        self.option_scene.connect_signal("selected", self.selected)

    def handle_input(self, keypress):
        if self.option_scene.handle_input(keypress):
            return True
        if keypress in [pygame.K_ESCAPE, pygame.K_x]:
            self.remove_scene()
            return True
        if keypress in constants.DIRECTIONS:
            return True

    def draw(self, screen):
        pygame.draw.rect(screen, constants.ALMOST_BLACK, self.box_rect)

    def selected(self, option):
        """Respond when an option has been selected."""
        if option == "Resume":
            self.remove_scene()
        if option == "Main Menu":
            self.game.save_game()
            self.game.change_base_scene(main_menu.MainMenu)
