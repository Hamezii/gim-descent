'''
GIM Descent 4

James Lecomte

To do:
- Improve AI
'''

# VV Do this to profile VV
# py -m cProfile -s tottime gim.pyw

import pygame

import audio
import constants
from assets.scenes.main_menu import MainMenu
from game_manager import GameManager
from misc import leave

#from functools import lru_cache

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()

pygame.mixer.set_num_channels(8)

audio.load_audio()


def get_input(events):
    """Return the last key that was just pressed."""
    keypress = None

    for event in events:
        if event.type == pygame.KEYDOWN:
            keypress = event.key

            if event.key == pygame.K_w or event.key == pygame.K_UP:
                keypress = constants.UP

            if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                keypress = constants.LEFT

            if event.key == pygame.K_s or event.key == pygame.K_DOWN:
                keypress = constants.DOWN

            if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                keypress = constants.RIGHT

    return keypress


def main():
    """Run the game."""

    screen = init_screen()

    game = GameManager()

    game.change_base_scene(MainMenu)

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                game.save_game()
                leave()
        keypress = get_input(events)
        game.input(keypress)
        game.send_event("unfocused_input", keypress)

        game.update()

        screen.fill(constants.BLACK)
        game.draw(screen)
        pygame.display.update()

def init_screen():
    """Returns the screen surface, as well as WIDTH and HEIGHT constants."""

    pygame.display.set_caption("Gim 4")

    if constants.FULLSCREEN_MODE:
        info_object = pygame.display.Info()
        constants.WIDTH = info_object.current_w
        constants.HEIGHT = info_object.current_h

        screen = pygame.display.set_mode((constants.WIDTH, constants.HEIGHT), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
    else:
        screen = pygame.display.set_mode((constants.WIDTH, constants.HEIGHT))

    constants.MENU_SCALE = round(constants.WIDTH/600)

    pygame.display.set_icon(pygame.image.load(constants.IMAGES+"logo.png").convert_alpha())

    return screen

if __name__ == "__main__":
    main()
