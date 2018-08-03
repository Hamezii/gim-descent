'''
Handles sound storing and playing.
'''

import glob
import random

import pygame

import constants

# Initialising audio
CACHE = {}

def init_cache():
    '''Initialise the cache of Sound objects.'''
    for name in glob.glob(constants.AUDIO+"*.wav"):
        add_to_cache(name)
    for name in glob.glob(constants.AUDIO+"*.ogg"):
        add_to_cache(name)

def add_to_cache(filename):
    '''Add an audio file to the cache of Sound objects.'''
    cache_name = filename[len(constants.AUDIO):-4]
    CACHE[cache_name] = pygame.mixer.Sound(filename)

def play(name, volume=1, replace=False):
    '''Play an audio sample.

    Using replace will stop all playback of the sound before playing it.
    '''
    sound = CACHE[name]
    if replace:
        sound.stop()
    channel = sound.play()
    if channel:
        channel.set_volume(volume)

def play_music():
    '''Loop a random piece of music.'''
    pygame.mixer.music.load(random.choice(glob.glob(constants.MUSIC+"*")))
    pygame.mixer.music.set_volume(constants.MUSIC_NORMAL_VOLUME)
    pygame.mixer.music.play(-1)

def dim_music():
    '''Temporarily quieten the playback of the music.'''
    pygame.mixer.music.set_volume(constants.MUSIC_DIMMED_VOLUME)

def undim_music():
    '''Return the playback of the music to its original volume.'''
    pygame.mixer.music.set_volume(constants.MUSIC_NORMAL_VOLUME)
