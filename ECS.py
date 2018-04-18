'''Entity Component System.'''

class TagManager:
    '''Stores tags about the world.'''
    def __init__(self):
        self.player = None
        self.focus = None


class System:
    '''Contains logic acting on components.'''
    def __init__(self):
        self.world = None
        self.game = None

    def update(self, **args):
        '''Run a tick of the system.'''
        raise NotImplementedError

class World:
    '''The main Entity Component System

    Stores systems and components, as well as tags.
    '''
    def __init__(self, game):
        self.tags = TagManager()
        self._game = game
        self._next_entity_id = 0
        self._components = {}
        self._entities = {}
        self._systems = []
        self._dead_entities = set()

    def clear_all(self):
        '''Clear all entities from the world.'''
        self._next_entity_id = 0
        self._dead_entities.clear()
        self._components.clear()
        self._entities.clear()


    def add_system(self, system_instance, priority=0):
        '''Add a system instance to the world.'''
        assert issubclass(system_instance.__class__, System)
        system_instance.priority = priority
        system_instance.world = self
        system_instance.game = self._game
        self._systems.append(system_instance)
        self._systems.sort(key=lambda sys: sys.priority, reverse=True)

    def remove_system(self, system_type):
        '''Remove system of a specific type from the world.'''
        for system in self._systems:
            if isinstance(system, system_type):
                system.world = None
                self._systems.remove(system)

    def get_system(self, system_type):
        '''Return system of a specific type.'''
        for system in self._systems:
            if isinstance(system, system_type):
                return system
        raise ValueError

    def create_entity(self, *components):
        '''Create an entity which is added to the world.

        The component parameters will be assigned to the new entity.
        '''
        self._next_entity_id += 1

        for component in components:
            self.add_component(self._next_entity_id, component)

        return self._next_entity_id

    def delete_entity(self, entity, instant=False):
        '''Delete an entity, either instantly or at the end of the cycle.'''
        if instant:
            for component_type in self._entities[entity]:
                del self._components[component_type][entity]

                if not self._components[component_type]:
                    del self._components[component_type]

            del self._entities[entity]

        else:
            self._dead_entities.add(entity)

    def entity_component(self, entity, component_type):
        '''Get an entity's component of a specific type.'''
        return self._components[component_type][entity]

    def entity_components(self, entity):
        '''Get all components belonging to an entity.'''
        return (self._components[comp][entity] for comp in self._entities[entity])

    def has_component(self, entity, component_type):
        '''Return true if entity has a component of a specific type/'''
        return component_type in self._entities[entity]

    def add_component(self, entity, component):
        '''Add a component instance to an entity.'''
        component_type = type(component)

        if component_type not in self._components:
            self._components[component_type] = {}

        self._components[component_type][entity] = component

        if entity not in self._entities:
            self._entities[entity] = set()
        self._entities[entity].add(component_type)

    def remove_component(self, entity, component_type):
        '''Remove from an entity a component of a specific type.'''

        del self._components[component_type][entity]

        if not self._components[component_type]:
            del self._components[component_type]

        self._entities[entity].discard(component_type)

        if not self._entities[entity]:
            del self._entities[entity]

        return entity

    def get_component(self, component_type):
        '''Get all components of a specific type.'''
        try:
            comp_db = self._components[component_type].items()
        except KeyError:
            raise StopIteration

        for entity, component in comp_db:
            yield entity, component


    def get_components(self, *component_types):
        '''Get all entity components in which the entity has a component of every type.'''
        type_set = set(component_types)
        entity_db = list(self._entities.items())
        comp_db = self._components

        for entity, comps in entity_db:
            if type_set.issubset(comps):
                yield entity, tuple(comp_db[comp][entity] for comp in component_types)


    def update(self, **args):
        '''Run a tick of the ECS.'''
        if self._dead_entities:
            for entity in self._dead_entities:
                self.delete_entity(entity, instant=True)
            self._dead_entities.clear()

        for system in self._systems:
            system.update(**args)
