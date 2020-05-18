"""Entity Component System."""

#from functools import lru_cache

def memoize(func):
    """Cache decorator."""
    cache = {}
    def wrapper(*args):
        """A wrapper for the function."""
        if args in cache:
            return cache[args]
        result = func(*args)
        cache[args] = result
        return result

    def cache_clear():
        """Clear the cache."""
        cache.clear()

    def cache_remove(component_type):
        """Remove a specific component type from the cache."""
        if component_type in cache:
            # This code only runs if keys of the cache are NOT LISTS, since component_type is also not a list.
            # however, if component_type is a list (i.e a list of component types), this code will run.
            del cache[component_type]
            return
        for key in list(cache):
            # For any key that depends on the component that has to be recached, remove the cache.
            if component_type in key:
                del cache[key]

    wrapper.cache_clear = cache_clear
    wrapper.cache_remove = cache_remove
    return wrapper

class TagManager:
    """Stores tags about the world."""
    def __init__(self):
        self.player = None


class System:
    """Contains logic acting on components."""
    def __init__(self):
        self.world: World
        self.game = None
        self.renderer = None
        self.priority = 0

    def process(self, **args):
        """Run a tick of the system."""
        raise NotImplementedError

class World:
    """The main Entity Component System

    Stores systems and components, as well as tags.
    """
    def __init__(self):
        """A World object keeps track of all Entities, Components, and Systems.

        A World contains a database of all Entity/Component assignments. It also
        handles calling the process method on any Systems assigned to it.
        """
        self.tags = TagManager()
        self._systems = []
        self._next_entity_id = 0
        self._components = {}
        self._entities = {}
        self._dead_entities = set()

    def clear_cache(self):
        """Not really sure what this one does."""
        self.get_component.cache_clear()
        self.get_components.cache_clear()

    def remove_cache(self, component_type):
        """Remove a specific component group from the cache because it has changed."""
        self.get_component.cache_remove(component_type)
        self.get_components.cache_remove(component_type)

    def clear_all(self):
        """Remove all Entities and Components from the World."""
        self._next_entity_id = 0
        self._dead_entities.clear()
        self._components.clear()
        self._entities.clear()
        self.clear_cache()

    def set_game_reference(self, level):
        """Set the game which the World and systems have a reference to."""
        for system in self._systems:
            system.game = level
            system.renderer = level.game.renderer


    def add_system(self, system_instance, priority=0):
        """Add a System instance to the World.

        :param system_instance: An instance of a System,
        subclassed from the System class
        :param priority: A higher number is processed first.
        """
        assert issubclass(system_instance.__class__, System)
        system_instance.priority = priority
        system_instance.world = self
        self._systems.append(system_instance)
        self._systems.sort(key=lambda proc: proc.priority, reverse=True)

    def remove_system(self, system_type):
        """Remove a System from the World, by type.

        :param system_type: The class type of the System to remove.
        """
        for system in self._systems:
            if isinstance(system, system_type):
                system.world = None
                self._systems.remove(system)

    def get_system(self, system_type):
        """Get a System instance, by type.

        This method returns a System instance by type. This could be
        useful in certain situations, such as wanting to call a method on a
        System, from within another System.

        :param system_type: The type of the System you wish to retrieve.
        :return: A System instance that has previously been added to the World.
        """
        for system in self._systems:
            if isinstance(system, system_type):
                return system

    def create_entity(self, *components):
        """Create a new Entity.

        This method returns an Entity ID, which is just a plain integer.
        You can optionally pass one or more Component instances to be
        assigned to the Entity.

        :param components: Optional components to be assigned to the
        entity on creation.
        :return: The next Entity ID in sequence.
        """
        self._next_entity_id += 1

        for component in components:
            self.add_component(self._next_entity_id, component)

        return self._next_entity_id

    def delete_entity(self, entity, immediate=False):
        """Delete an Entity from the World.

        Delete an Entity and all of it's assigned Component instances from
        the world. By default, Entity deletion is delayed until the next call
        to *World.process*. You can request immediate deletion, however, by
        passing the "immediate=True" parameter. This should generally not be
        done during Entity iteration (calls to World.get_component/s).

        Raises a KeyError if the given entity does not exist in the database.
        :param entity: The Entity ID you wish to delete.
        :param immediate: If True, delete the Entity immediately.
        """
        if immediate:
            for component_type in self._entities[entity]:
                self._components[component_type].discard(entity)

                if not self._components[component_type]:
                    del self._components[component_type]

                self.remove_cache(component_type)
            del self._entities[entity]



        else:
            self._dead_entities.add(entity)

    def entity_component(self, entity, component_type):
        """Retrieve a Component instance for a specific Entity.

        Retrieve a Component instance for a specific Entity. In some cases,
        it may be necessary to access a specific Component instance.
        For example: directly modifying a Component to handle user input.

        Raises a KeyError if the given Entity and Component do not exist.
        :param entity: The Entity ID to retrieve the Component for.
        :param component_type: The Component instance you wish to retrieve.
        :return: The Component instance requested for the given Entity ID.
        """
        return self._entities[entity][component_type]

    def entity_components(self, entity):
        """Retrieve all Components for a specific Entity, as a Tuple.

        Retrieve all Components for a specific Entity. The method is probably
        not appropriate to use in your Systems, but might be useful for
        saving state, or passing specific Components between World instances.
        Unlike most other methods, this returns all of the Components as a
        Tuple in one batch, instead of returning a Generator for iteration.

        Raises a KeyError if the given entity does not exist in the database.
        :param entity: The Entity ID to retrieve the Components for.
        :return: A tuple of all Component instances that have been
        assigned to the passed Entity ID.
        """
        return tuple(self._entities[entity].values())

    def has_component(self, entity, component_type):
        """Check if a specific Entity has a Component of a certain type.

        :param entity: The Entity you are querying.
        :param component_type: The type of Component to check for.
        :return: True if the Entity has a Component of this type,
        otherwise False
        """
        return component_type in self._entities[entity]

    def has_entity(self, entity):
        """Return true if ECS has entity."""
        if entity in self._entities:
            return True
        return False

    def add_component(self, entity, component_instance):
        """Add a new Component instance to an Entity.

        Add a Component instance to an Entiy. If a Component of the same type
        is already assigned to the Entity, it will be replaced.

        :param entity: The Entity to associate the Component with.
        :param component_instance: A Component instance.
        """
        component_type = type(component_instance)

        if component_type not in self._components:
            self._components[component_type] = set()

        self._components[component_type].add(entity)

        if entity not in self._entities:
            self._entities[entity] = {}

        self._entities[entity][component_type] = component_instance
        self.remove_cache(component_type)

    def remove_component(self, entity, component_type):
        """Remove a Component instance from an Entity, by type.

        A Component instance can be removed by providing it's type.
        For example: world.delete_component(enemy_a, Velocity) will remove
        the Velocity instance from the Entity enemy_a.

        Raises a KeyError if either the given entity or Component type does
        not exist in the database.
        :param entity: The Entity to remove the Component from.
        :param component_type: The type of the Component to remove.
        """
        self._components[component_type].discard(entity)

        if not self._components[component_type]:
            del self._components[component_type]

        del self._entities[entity][component_type]

        if not self._entities[entity]:
            del self._entities[entity]

        self.remove_cache(component_type)
        return entity

    def _get_component(self, component_type):
        """Get an iterator for Entity, Component pairs.

        :param component_type: The Component type to retrieve.
        :return: An iterator for (Entity, Component) tuples.
        """
        entity_db = self._entities

        for entity in self._components.get(component_type, []):
            yield entity, entity_db[entity][component_type]

    def _get_components(self, *component_types):
        """Get an iterator for Entity and multiple Component sets.

        :param component_types: Two or more Component types.
        :return: An iterator for Entity, (Component1, Component2, etc)
        tuples.
        """
        entity_db = self._entities
        comp_db = self._components

        try:
            for entity in set.intersection(*[comp_db[ct] for ct in component_types]):
                yield entity, [entity_db[entity][ct] for ct in component_types]
        except KeyError:
            pass

    @memoize
    def get_component(self, component_type):
        """Get a tuple for Entity, Component pairs."""
        return tuple(query for query in self._get_component(component_type))

    @memoize
    def get_components(self, *component_types):
        """Get a tuple for Entity and multiple Component sets."""
        # The reason to use this intermediary function for _get_components is because _get_components returns an iterator,
        # while this function converts it in to a list and caches it.
        return tuple(query for query in self._get_components(*component_types))

    def try_component(self, entity, component_type):
        """Try to get a single component type for an Entity.

        This method will return the requested Component if it exists, but
        will pass silently if it does not. This allows a way to access optional
        Components that may or may not exist.

        :param entity: The Entity ID to retrieve the Component for.
        :param component_type: The Component instance you wish to retrieve.
        :return: A iterator containg the single Component instance requested,
                    which is empty if the component doesn't exist.
        """
        if component_type in self._entities[entity]:
            yield self._entities[entity][component_type]
        else:
            return None

    def _clear_dead_entities(self):
        """Finalize deletion of any Entities that are marked dead.

        In the interest of performance, this method duplicates code from the
        `delete_entity` method. If that method is changed, those changes should
        be duplicated here as well.
        """
        for entity in self._dead_entities:

            for component_type in self._entities[entity]:
                self._components[component_type].discard(entity)

                if not self._components[component_type]:
                    del self._components[component_type]
                self.remove_cache(component_type)
            del self._entities[entity]

        self._dead_entities.clear()

    def _process(self, *args, **kwargs):
        for system in self._systems:
            system.process(*args, **kwargs)

    def process(self, *args, **kwargs):
        """Call the process method on all Systems, in order of their priority.

        Call the *process* method on all assigned Systems, respecting their
        optional priority setting. In addition, any Entities that were marked
        for deletion since the last call to *World.process*, will be deleted
        at the end of this method call.

        :param args: Optional arguments that will be passed through to the
        *process* method of all Systems.
        """
        self._process(*args, **kwargs)
        self._clear_dead_entities()
