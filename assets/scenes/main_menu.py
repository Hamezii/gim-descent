"""Contains the MainMenu scene."""

import pygame

import audio
import constants
import widget as wgt
from misc import leave

from .character_select import CharacterSelect
from .dungeon import Dungeon
from .main_menu_title import MainMenuTitle
from .scene import Scene


class MainMenu(Scene):
    """The starting menu of the game."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.animation_done = False
        self.title_background = None

        self.options = ["New game"]
        if self.game.has_save():
            self.options.insert(0, "Continue game")

        self.title = self.add_child_scene(MainMenuTitle)

        self.cursor_pos = 0

        self.options_widget = wgt.TextLines(
            renderer=self.game.renderer,
            text=self.options,
            v_spacing=1.6,
            size=constants.MENU_SCALE*5,
            offset=(constants.WIDTH // 2, constants.HEIGHT//2),
            centered=True
        )

        self.widgets = []

        audio.play_music()

    def get_input(self, keypress):
        if self.animation_done:

            if keypress == constants.DOWN:
                self.cursor_pos = min(len(self.options)-1, self.cursor_pos + 1)

            if keypress == constants.UP:
                self.cursor_pos = max(0, self.cursor_pos - 1)

            if keypress in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                if self.options[self.cursor_pos] == "New game":
                    self.game.change_base_scene(CharacterSelect)
                if self.options[self.cursor_pos] == "Continue game":
                    self.game.change_base_scene(Dungeon)
                    self.game.base_scene.load_game()

        if keypress == pygame.K_ESCAPE:
            leave()

        return True

    def update(self, delta):
        for widget in self.widgets:
            widget.update(delta)

        if not self.animation_done:
            if self.title.offset[1] == self.title.y_goal:
                self.animation_done = True
                self.widgets.append(self.options_widget)

    def draw(self, screen):
        # Logic to get title background to show in the right place
        # for different sized sceens
        if self.title_background is None:
            # Logic to get title image to scale on differently sized monitors
            if constants.WIDTH/1920 > constants.HEIGHT/1080:
                size = (constants.WIDTH, int(constants.WIDTH/1920*1080))
            else:
                size = (int(constants.HEIGHT/1080*1920), constants.HEIGHT)
            self.title_background = pygame.transform.scale(self.game.renderer.get_image(name="title_background"), size)

        screen.blit(self.title_background, (0, constants.HEIGHT-self.title_background.get_height()))

        if self.animation_done:
            x = constants.WIDTH/2 - constants.MENU_SCALE * 50
            y = constants.HEIGHT/2 + constants.MENU_SCALE*8*self.cursor_pos
            color = (*constants.WHITE, pygame.BLEND_ADD)
            cursor_image = self.game.renderer.get_image(name="cursor", color=color, scale=constants.MENU_SCALE)
            self.game.renderer.draw_centered_image(screen, cursor_image, (x, y))

        for widget in self.widgets:
            widget.draw(screen)
