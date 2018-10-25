"""Contains the GameManager and the base Scene class."""

import pygame

import renderer


class GameManager:
    """The main game manager class.

    Stores global objects as well as the scene tree.
    """
    def __init__(self):
        self.renderer = renderer.Renderer()
        self.clock = pygame.time.Clock()
        self.t_elapsed = 0
        self.fps = 0

        self.base_scene = None
        self.focus_scene = None

    def change_base_scene(self, scene_type, *args, **kwargs):
        """Replace the scene tree with a base scene given its type and input parameters. Focus on this scene."""
        self.base_scene = scene_type(*args, **kwargs, game=self)
        self.set_focus(self.base_scene)

    def set_focus(self, scene):
        """Set the focused scene."""
        self.focus_scene = scene

    def send_event(self, event_name, *args, **kwargs):
        """Recursively call a function on all scenes in the scene tree."""
        self.base_scene.get_event(event_name, *args, **kwargs)

    def has_save(self):
        """Return True if there is a save file and False otherwise.

        Temporarily disabled.
        """
        pass
        # return os.path.isfile("save.save")

    def input(self, keypress):
        """Send an input to the currently focused scene.

        Send the input up the tree until it is handled.
        """
        input_scene = self.focus_scene
        input_handled = input_scene.get_input(keypress)
        while (not input_handled) and (input_scene.parent is not None):
            input_scene = input_scene.parent
            input_handled = input_scene.get_input(keypress)

    def update(self):
        """Run a tick of the scenes."""
        delta = self.clock.tick()
        self.t_elapsed += delta
        self.fps = int(self.clock.get_fps())
        self.send_event("update", delta)
    def draw(self, screen):
        """Draw the whole scene tree, taking into account draw order."""
        self.__draw_scene(screen, self.base_scene)

    def __draw_scene(self, screen, scene):
        """Draw a scene and its child scenes."""
        for child in scene.children:
            if not child.scene_properties["draw_above_parent"]:
                self.__draw_scene(screen, child)
        scene.draw(screen)
        for child in scene.children:
            if child.scene_properties["draw_above_parent"]:
                self.__draw_scene(screen, child)
class Scene:
    """A node in the scene tree."""
    scene_properties = {
        "draw_above_parent": True
    }
    def __init__(self, game, parent=None):
        self.game = game
        self.parent = parent
        self.children = []

    def add_child_scene(self, scene_type, *args, **kwargs):
        """Add a child scene given its type and input parameters."""
        child_scene = scene_type(*args, **kwargs, game=self.game, parent=self)
        self.children.append(child_scene)
        return child_scene

    def remove_scene(self):
        """Remove this scene from the scene tree."""
        if self is self.game.base_scene:
            raise ValueError("Base scene can't be removed, only replaced.")
        if self is self.game.focus_scene:
            self.game.set_focus(self.parent)
        self.parent.children.remove(self)

    def get_event(self, event_name, *args, **kwargs):
        """Call a function on this scene given its name and parameters.

        Call get_event on children.
        """
        function = getattr(self, event_name, None)
        if function is not None:
            function(*args, **kwargs)
        for child in self.children:
            child.get_event(event_name, *args, **kwargs)

    def get_input(self, keypress):
        """Handle a user input.

        Return True if the input was handled.
        """
        pass

    def update(self, delta):
        """Update the current scene given how much time has passed."""
        pass

    def draw(self, screen):
        """Draw this scene to a pygame surface."""
        pass
