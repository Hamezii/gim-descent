"""Contains the GameOver scene."""

import pygame

import audio
import constants
import widget as wgt
from misc import pluralise, time_to_str

from . import character_select, main_menu
from .scene import Scene


class GameOver(Scene):
    """A display that is shown when the player dies."""
    REL_WIDTH = 200
    REL_HEIGHT = 7*9 + 8
    def __init__(self, dungeon, **kwargs):
        super().__init__(**kwargs)
        self.dungeon = dungeon
        self.width = self.REL_WIDTH * constants.MENU_SCALE
        self.height = self.REL_HEIGHT * constants.MENU_SCALE
        self.x = (self.game.width - self.width) / 2
        self.y = (self.game.height - self.height) / 2

        levels = dungeon.level_num - 1
        text_x = self.x + 5 * constants.MENU_SCALE
        text_y = self.y + 5 * constants.MENU_SCALE
        self.text = wgt.TextLines(
            renderer=self.game.renderer,
            color=constants.WHITE,
            size=5*constants.MENU_SCALE,
            offset=(text_x, text_y),
            text=(
                "You lose!",
                "You completed " + pluralise(levels, "level") + ".",
                "You were killed by :PLACEHOLDER:.",      # Will implement this, probably by adding an AttackedBy component.
                "Score: :PLACEHOLDER:",
                "Time: " + time_to_str(dungeon.game_time),
                "You killed " + pluralise(dungeon.kills, "creature") + ".",
                " ",
                "Space for quick replay",
                "Escape to return to the Main Menu"
            )
        )

    def handle_input(self, keypress):
        if keypress == pygame.K_SPACE:
            audio.play_music(constants.MUSIC_DUNGEON)
            self.game.change_base_scene(character_select.CharacterSelect)
            return True
        if keypress == pygame.K_ESCAPE:
            self.game.change_base_scene(main_menu.MainMenu)
            return True

    def draw(self, screen):
        pygame.draw.rect(screen, constants.ALMOST_BLACK, (self.x, self.y, self.width, self.height))
        self.text.draw(screen)
