"""Contains the Config class which interfaces with the config file."""

import json
import os

import constants

DEFAULT_SETTINGS = {
    "fullscreen_mode": True,
    "width": 1200,
    "height": 800,
    # "MUSIC_VOLUME": 0.5,
}

class Config:
    """Contains data from the config file."""
    def __init__(self):
        self.config_dict = {}

        if os.path.exists(constants.CONFIG_PATH):
            self.load_from_file()
        else:
            self.config_dict = constants.DEFAULT_SETTINGS.copy()
            self.save_to_file()

    def load_from_file(self):
        """Set the config dictionary to the one from the config file."""
        with open(constants.CONFIG_PATH, 'r') as config_file:
            self.config_dict = json.load(config_file)

    def save_to_file(self):
        """Save the config dictionary to the config file."""
        with open(constants.CONFIG_PATH, 'w') as config_file:
            json.dump(self.config_dict, config_file)

    @property
    def fullscreen_mode(self):
        """Get fullscreen_mode setting."""
        return self.config_dict["fullscreen_mode"]
    @fullscreen_mode.setter
    def fullscreen_mode(self, value):
        """Set fullscreen_mode setting."""
        self.config_dict["fullscreen_mode"] = value

    @property
    def width(self):
        """Get width setting."""
        return self.config_dict["width"]
    @width.setter
    def width(self, value):
        """Set width setting."""
        self.config_dict["width"] = value

    @property
    def height(self):
        """Get height setting."""
        return self.config_dict["height"]
    @height.setter
    def height(self, value):
        """Set height setting."""
        self.config_dict["height"] = value
