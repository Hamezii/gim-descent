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
    def FULLSCREEN_MODE(self):
        """Get FULLSCREEN_MODE setting."""
        return self._dict["FULLSCREEN_MODE"]
    @FULLSCREEN_MODE.setter
    def FULLSCREEN_MODE(self, value):
        """Set FULLSCREEN_MODE setting."""
        self._dict["FULLSCREEN_MODE"] = value

    @property
    def WIDTH(self):
        """Get WIDTH setting."""
        return self._dict["WIDTH"]
    @WIDTH.setter
    def WIDTH(self, value):
        """Set WIDTH setting."""
        self._dict["WIDTH"] = value

    @property
    def HEIGHT(self):
        """Get HEIGHT setting."""
        return self._dict["HEIGHT"]
    @HEIGHT.setter
    def HEIGHT(self, value):
        """Set HEIGHT setting."""
        self._dict["HEIGHT"] = value
