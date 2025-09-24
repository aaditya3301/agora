"""Location data model for the supply chain simulator."""

from typing import Literal


class Location:
    """Represents a location in the supply chain network."""
    
    def __init__(self, location_id: str, name: str, x: float, y: float, 
                 location_type: Literal['factory', 'warehouse', 'store']):
        """
        Initialize a Location.
        
        Args:
            location_id: Unique identifier for the location
            name: Human-readable name of the location
            x: X coordinate on the city map
            y: Y coordinate on the city map
            location_type: Type of location (factory, warehouse, or store)
        """
        if not location_id:
            raise ValueError("Location ID cannot be empty")
        if not name:
            raise ValueError("Location name cannot be empty")
        if location_type not in ['factory', 'warehouse', 'store']:
            raise ValueError("Location type must be 'factory', 'warehouse', or 'store'")
        
        self.location_id = location_id
        self.name = name
        self.x = x
        self.y = y
        self.location_type = location_type
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate straight-line distance to another location."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def __str__(self) -> str:
        return f"{self.name} ({self.location_type}) at ({self.x}, {self.y})"
    
    def __repr__(self) -> str:
        return f"Location('{self.location_id}', '{self.name}', {self.x}, {self.y}, '{self.location_type}')"