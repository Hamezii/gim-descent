'''
James Lecomte

To do:
- Add an exit option and settings option to main menu

- Improve AI
'''

# VV Do this to profile VV
# py -m cProfile -s tottime gim.pyw

import pygame

import audio
import config as config_api
import constants
import key_input
from assets.scenes.main_menu import MainMenu
from game_manager import GameManager
from misc import leave

#from functools import lru_cache

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()

pygame.mixer.set_num_channels(8)

audio.load_audio()

def main():
    """Run the game."""

    screen, width, height = init_screen()

    game = GameManager(width, height)
    game.change_base_scene(MainMenu)

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                game.save_game()
                leave()
            if event.type == pygame.KEYDOWN:
                keypress = key_input.Keypress(event.key)
                game.input(keypress)
                game.call_all_scenes("unfocused_input", keypress)

        game.update()

        screen.fill(constants.BLACK)
        game.draw(screen)
        pygame.display.update()

def init_screen():
    """Returns the screen surface, as well as width and height constants."""

    pygame.display.set_caption("Gim Descent")
    config = config_api.Config()

    if config.fullscreen_mode:
        info_object = pygame.display.Info()
        width = info_object.current_w
        height = info_object.current_h

        screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
    else:
        width = config.width
        height = config.height
        screen = pygame.display.set_mode((width, height))

    constants.MENU_SCALE = round(width/600)

    pygame.display.set_icon(pygame.image.load(constants.IMAGES+"logo.png").convert_alpha())

    return screen, width, height

if __name__ == "__main__":
    main()
