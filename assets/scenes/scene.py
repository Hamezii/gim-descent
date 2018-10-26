"""Contains the base Scene class."""


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
        if self.has_focus_scene():
            self.game.set_focus(self.parent)
        self.parent.children.remove(self)

    def has_focus_scene(self):
        """Return True if this scene or any of its children are the focus scene."""
        return any((self is self.game.focus_scene, *(child.has_focus_scene() for child in self.children)))

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
