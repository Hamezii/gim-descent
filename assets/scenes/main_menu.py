"""Contains the MainMenu scene."""

import pygame

import audio
import constants
import key_input
import widget as wgt
from misc import leave

from .character_select import CharacterSelect
from .dungeon import Dungeon
from .main_menu_title import MainMenuTitle
from .option_select import OptionSelect
from .scene import Scene
from .settings import Settings


class MainMenu(Scene):
    """The starting menu of the game."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.animation_done = False
        self.title_background = None

        self.title = self.add_child_scene(MainMenuTitle)

        self.widgets = tuple()
        audio.stop_music()

    def _exit_game(self):
        """Exit the game from the main menu."""
        leave()

    def _start_main_menu(self):
        """Add everything to the main menu. Called after the title drops.

        The main menu animation and proper main menu could be two seperate scenes.
        """
        audio.play_music(constants.MUSIC_DUNGEON)
        options = ["New game", "Settings", "Exit"]
        if self.game.has_save():
            options.insert(0, "Continue game")
        pos = (self.game.width // 2, self.game.height//2)
        option_select = self.add_child_scene(OptionSelect, options, pos)
        self.game.set_focus(option_select)
        option_select.connect_signal("selected", self.selected_option)

        # Help text
        self.widgets = (
            wgt.Text(
                renderer=self.game.renderer,
                offset=(5*constants.MENU_SCALE, 5*constants.MENU_SCALE),
                size=5*constants.MENU_SCALE,
                color=constants.LIGHT_GRAY,
                text="CONTROLS"
            ),
            wgt.TextLines(
                renderer=self.game.renderer,
                offset=(5*constants.MENU_SCALE, 16*constants.MENU_SCALE),
                size=5*constants.MENU_SCALE,
                color=constants.GRAY,
                text=[
                    "WASD, ARROWS       MOVE",
                    "Z, SPACE, ENTER    SELECT/OPEN INVENTORY",
                    "X, ESCAPE          BACK/EXIT",
                    "TAB                OPEN/CLOSE INVENTORY",
                    "PLUS, MINUS        ZOOM IN AND OUT"
                ]
            )
        )

    def selected_option(self, option):
        """Respond to an option being selected."""
        if option == "New game":
            self.game.change_base_scene(CharacterSelect)
        if option == "Continue game":
            self.game.change_base_scene(Dungeon)
            self.game.base_scene.load_game()
        if option == "Settings":
            self.game.set_focus(self.add_child_scene(Settings))
        if option == "Exit":
            self._exit_game()

    def handle_input(self, keypress):
        if keypress.has_action(key_input.Action.BACK):
            self._exit_game()

    def update(self, delta):
        if not self.animation_done:
            if self.title.offset[1] == self.title.y_goal:
                self.animation_done = True
                self._start_main_menu()


    def draw(self, screen):
        if self.title_background is None:
            # Logic to get title image to scale on differently sized monitors
            if self.game.width/1920 > self.game.height/1080:
                size = (self.game.width, int(self.game.width/1920*1080))
            else:
                size = (int(self.game.height/1080*1920), self.game.height)
            self.title_background = pygame.transform.scale(self.game.renderer.get_image(name="title_background"), size)
        # Logic to get title background to show in the right place
        # for different sized sceens
        screen.blit(self.title_background, (0, self.game.height-self.title_background.get_height()))
        for widget in self.widgets:
            widget.draw(screen)
