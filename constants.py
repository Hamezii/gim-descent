'''
Contains all the constants for Gim.
'''

import os
import sys

SEED = None

DEFAULT_SETTINGS = {
    "fullscreen_mode": True,
    "width": 1200,
    "height": 800,
    # "MUSIC_VOLUME": 0.5,
}

BLINK_RATE = 250

TILE_SIZE = 40

PATH = getattr(sys, '_MEIPASS', os.getcwd())
ASSETS = os.path.join(PATH, "assets", "")
IMAGES = os.path.join(ASSETS, "images", "")
AUDIO = os.path.join(ASSETS, "audio", "")
MUSIC = os.path.join(AUDIO, "music", "")
DEFAULT_IMAGES = os.path.join(ASSETS, "images", "")
# DEFAULT_IMAGES is sort of redundant, would be used if there were texture packs
CONFIG_PATH = os.path.join(ASSETS, "config.cfg")

MUSIC_NORMAL_VOLUME = 0.5
MUSIC_DIMMED_VOLUME = 0.25

MUSIC_DUNGEON = MUSIC + "dungeon_theme.ogg"

BLACK = (0, 0, 0)
ALMOST_BLACK = (10, 10, 10)
DARK_GRAY = (70, 70, 70)
GRAY = (122, 122, 122)
LIGHT_GRAY = (170, 170, 170)
WHITE = (255, 255, 255)

DARK_RED = (150, 50, 50)
DARK_GREEN = (50, 150, 50)
RED = (230, 25, 25)
GREEN = (25, 230, 50)
ORANGE = (255, 170, 50)

COLOR_KEY = (255, 0, 255)

LEFT = (-1, 0)
RIGHT = (1, 0)
UP = (0, -1)
DOWN = (0, 1)
DIRECTIONS = (UP, DOWN, LEFT, RIGHT)

MENU_SCALE = None
