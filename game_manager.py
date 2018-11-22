"""Contains the GameManager class."""

import pygame

import renderer


class GameManager:
    """The main game manager class.

    Stores global objects as well as the scene tree.
    """
    def __init__(self, width, height):
        self.renderer = renderer.Renderer()
        self.clock = pygame.time.Clock()
        self.width = width
        self.height = height

        self.t_elapsed = 0
        self.fps = 0

        self.base_scene = None
        self._focus_scene_stack = []

    def change_base_scene(self, scene_type, *args, **kwargs):
        """Replace the scene tree with a base scene given its type and input parameters. Focus on this scene."""
        self.base_scene = scene_type(*args, **kwargs, game=self)
        self.set_focus(self.base_scene)

    @property
    def focus_scene(self):
        """Get the scene being currently focused on."""
        return self._focus_scene_stack[-1]

    def set_focus(self, scene):
        """Set the focused scene."""
        self._focus_scene_stack.append(scene)

    def remove_focus(self, scene):
        """Remove focus from a scene."""
        self._focus_scene_stack.remove(scene)

    def remove_scene(self, scene, parent_being_removed=False):
        """Remove a scene from the scene tree."""
        if scene is self.base_scene:
            raise ValueError("Base scene can't be removed, only replaced.")
        for child in scene.children:
            self.remove_scene(child, parent_being_removed=True)
        if scene in self._focus_scene_stack:
            self.remove_focus(scene)
        if not parent_being_removed:
            scene.parent.children.remove(scene)

    def send_event(self, event_name, *args, **kwargs):
        """Recursively call a function on all scenes in the scene tree."""
        self.base_scene.get_event(event_name, *args, **kwargs)

    def has_save(self):
        """Return True if there is a save file and False otherwise.

        Temporarily disabled.
        """
        pass
        # return os.path.isfile("save.save")

    def save_game(self):
        """Save the state of the game in a file.

        Currently not implemented.
        """
        pass

    def input(self, keypress):
        """Send an input to the currently focused scene.

        Send the input up the tree until it is handled.
        """
        stack_pos = len(self._focus_scene_stack) - 1
        input_handled = self._focus_scene_stack[stack_pos].handle_input(keypress)
        while (input_handled is not True) and stack_pos > 0:
            stack_pos -= 1
            input_handled = self._focus_scene_stack[stack_pos].handle_input(keypress)

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
