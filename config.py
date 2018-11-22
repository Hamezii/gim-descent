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

    def __getattr__(self, var):
        if var in self._dict:
            return self._dict[var]
        else:
            raise AttributeError("'Settings' object has no attribute '"+var+"'")
