# Genesis is used to handle the genetic and evolutionary aspects of the simulation

from typing import Dict, List, Any
from .entity import Entity
from .component import Component

class ECS:
    """Container for all entities and components"""
    
    def __init__(self):
        self.entities: Dict[int, Entity] = {}
        self.components: Dict[str, Dict[int, Component]] = {}
        self.systems: List[Any] = []
        self.systems_by_name: Dict[str, Any] = {}  # For easy lookup
        
    def create_entity(self) -> int:
        """Create a new entity and return its ID"""
        entity = Entity()
        self.entities[entity.id] = entity
        return entity.id
        
    def delete_entity(self, entity_id: int):
        """Remove an entity and all its components"""
        if entity_id in self.entities:
            # Remove all components for this entity
            for component_type in list(self.components.keys()):
                if entity_id in self.components[component_type]:
                    del self.components[component_type][entity_id]
            
            # Remove the entity
            del self.entities[entity_id]
            
    def add_component(self, entity_id: int, component_type: str, component: Component):
        """Add a component to an entity"""
        # Ensure the component type exists in our components dictionary
        if component_type not in self.components:
            self.components[component_type] = {}
        
        # Assign the component to the entity
        component.entity_id = entity_id
        self.components[component_type][entity_id] = component
        
        # Also add to entity's components dict
        if entity_id in self.entities:
            self.entities[entity_id].add_component(component_type, component)
            
    def get_component(self, entity_id: int, component_type: str) -> Component:
        """Get a specific component for an entity"""
        if component_type in self.components and entity_id in self.components[component_type]:
            return self.components[component_type][entity_id]
        return None
        
    def get_components_by_type(self, component_type: str) -> Dict[int, Component]:
        """Get all components of a specific type"""
        return self.components.get(component_type, {})
        
    def add_system(self, system):
        """Add a system to the world"""
        self.systems.append(system)
        
        # Store system by class name for easy lookup
        system_name = system.__class__.__name__.lower().replace('system', '')
        self.systems_by_name[system_name] = system
        
    def get_system(self, name: str):
        """Get a system by name"""
        return self.systems_by_name.get(name)
        
    def update(self, dt: float):
        """Update all systems"""
        for system in self.systems:
            system.update(dt)