"""Contains the Settings class which manages the config file."""

import json
import os

import constants

class Settings:
    """Contains data from the config file."""
    def __init__(self):
        self._dict = {}
        # Read the data in the config file
        if os.path.exists(constants.CONFIG_PATH):
            with open(constants.CONFIG_PATH, 'r') as config_file:
                config_dict = json.load(config_file)
        else:
            # Make a new config file with default settings
            with open(constants.CONFIG_PATH, 'w') as config_file:
                json.dump(constants.DEFAULT_SETTINGS, config_file)
                config_dict = constants.DEFAULT_SETTINGS
        for key, value in config_dict.items():
            self._dict[key] = value

    def save_settings(self):
        """Save the configuration to the config file."""
        with open(constants.CONFIG_PATH, 'w') as config_file:
            json.dump(self._dict, config_file)

    @property
    def fullscreen_mode(self):
        """Get fullscreen_mode setting."""
        return self._dict["fullscreen_mode"]
    @fullscreen_mode.setter
    def fullscreen_mode(self, value):
        """Set fullscreen_mode setting."""
        self._dict["fullscreen_mode"] = value

    @property
    def width(self):
        """Get width setting."""
        return self._dict["width"]
    @width.setter
    def width(self, value):
        """Set width setting."""
        self._dict["width"] = value

    @property
    def height(self):
        """Get height setting."""
        return self._dict["height"]
    @height.setter
    def height(self, value):
        """Set height setting."""
        self._dict["height"] = value
