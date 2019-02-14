"""Contains the GameOver scene."""

import pygame

import audio
import constants
import key_input
import widget as wgt
from misc import pluralise, time_to_str

from . import character_select, main_menu
from .scene import Scene


class GameOver(Scene):
    """A display that is shown when the player dies."""
    REL_WIDTH = 200
    REL_HEIGHT = 7*9 + 8
    def __init__(self, dungeon, victory, **kwargs):
        super().__init__(**kwargs)
        self.dungeon = dungeon
        self.width = self.REL_WIDTH * constants.MENU_SCALE
        self.height = self.REL_HEIGHT * constants.MENU_SCALE
        self.x = (self.game.width - self.width) / 2
        self.y = (self.game.height - self.height) / 2

        text_x = self.x + 5 * constants.MENU_SCALE
        text_y = self.y + 5 * constants.MENU_SCALE
        if victory:
            top_text = self._get_win_text()
        else:
            top_text = self._get_lose_text()
        self.text = wgt.TextLines(
            renderer=self.game.renderer,
            color=constants.WHITE,
            size=5*constants.MENU_SCALE,
            offset=(text_x, text_y),
            text=(
                *top_text,
                "Score: :PLACEHOLDER:",
                "Time: " + time_to_str(dungeon.game_time),
                "You killed " + pluralise(dungeon.kills, "creature") + ".",
                " ",
                "Space to play again",
                "Escape to return to the Main Menu"
            )
        )

    def _get_completed_levels(self):
        """Return how many levels were completed by the player."""
        return self.dungeon.level_num - 1

    def _get_win_text(self):
        """Return a string of what to display if the player wins."""
        return (
            "You win!",
            "You completed " + pluralise(self._get_completed_levels(), "level") + "."
        )

    def _get_lose_text(self):
        """Return a string of what to display if the player loses."""
        return (
            "You lose!",
            "You completed " + pluralise(self._get_completed_levels(), "level") + ".",
            "You were killed by :PLACEHOLDER:."      # Will implement this, probably by adding an AttackedBy component.
        )

    def handle_input(self, keypress):
        if keypress.has_action(key_input.Action.ACCEPT):
            audio.play_music(constants.MUSIC_DUNGEON)
            self.game.change_base_scene(character_select.CharacterSelect)
            return True
        if keypress.has_action(key_input.Action.BACK):
            self.game.change_base_scene(main_menu.MainMenu)
            return True

    def draw(self, screen):
        pygame.draw.rect(screen, constants.ALMOST_BLACK, (self.x, self.y, self.width, self.height))
        self.text.draw(screen)
