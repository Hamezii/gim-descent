"""Contains the base Scene class."""

import game_manager

class Scene:
    """A node in the scene tree."""
    scene_properties = {
        "draw_above_parent": True
    }
    def __init__(self, game, parent=None):
        self.game: game_manager.GameManager = game
        self.parent = parent
        self.children = []
        self.signals = {}

    def add_child_scene(self, scene_type, *args, **kwargs):
        """Add a child scene given its type and input parameters."""
        child_scene = scene_type(*args, **kwargs, game=self.game, parent=self)
        self.children.append(child_scene)
        return child_scene

    def remove_scene(self):
        """Remove this scene from the scene tree."""
        self.game.remove_scene(self)

    def call_recursively(self, event_name, *args, **kwargs):
        """Call a function on this scene given its name and parameters.

        Call call_recursively on children.
        """
        function = getattr(self, event_name, None)
        if function is not None:
            function(*args, **kwargs)
        for child in self.children:
            child.call_recursively(event_name, *args, **kwargs)

    def connect_signal(self, signal_name, function_obj):
        """Connect a signal so that it calls a function when it is emitted."""
        if not signal_name in self.signals:
            self.signals[signal_name] = []
        self.signals[signal_name].append(function_obj)

    def emit_signal(self, signal_name, *args, **kwargs):
        """Emit a signal, calling all connected functions.

        Optional parameters can also be passed to the functions.
        """
        if signal_name in self.signals:
            for function in self.signals[signal_name]:
                function(*args, **kwargs)

    def handle_input(self, keypress):
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
