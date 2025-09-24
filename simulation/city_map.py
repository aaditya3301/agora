"""
City Map class to manage locations and distances in the supply chain simulation.
"""
import math
import logging
from typing import Dict, List, Optional, Tuple
from models.location import Location

logger = logging.getLogger(__name__)


class CityMap:
    """
    Manages locations and distances in the city for the supply chain simulation.
    Provides methods for location management, distance calculations, and pathfinding.
    """
    
    def __init__(self):
        """Initialize an empty city map."""
        self.locations: Dict[str, Location] = {}
        self._distance_cache: Dict[Tuple[str, str], float] = {}
        
        logger.info("CityMap initialized")
    
    def add_location(self, location: Location):
        """
        Add a location to the city map.
        
        Args:
            location: Location object to add
            
        Raises:
            ValueError: If location with same ID already exists
        """
        if location.location_id in self.locations:
            raise ValueError(f"Location with ID '{location.location_id}' already exists")
        
        self.locations[location.location_id] = location
        # Clear distance cache since we added a new location
        self._distance_cache.clear()
        
        logger.info(f"Added location: {location}")
    
    def remove_location(self, location_id: str):
        """
        Remove a location from the city map.
        
        Args:
            location_id: ID of the location to remove
            
        Raises:
            KeyError: If location doesn't exist
        """
        if location_id not in self.locations:
            raise KeyError(f"Location '{location_id}' not found")
        
        removed_location = self.locations.pop(location_id)
        # Clear distance cache since we removed a location
        self._distance_cache.clear()
        
        logger.info(f"Removed location: {removed_location}")
    
    def get_location(self, location_id: str) -> Optional[Location]:
        """
        Get a location by its ID.
        
        Args:
            location_id: ID of the location to retrieve
            
        Returns:
            Location object or None if not found
        """
        return self.locations.get(location_id)
    
    def get_all_locations(self) -> List[Location]:
        """
        Get all locations in the city map.
        
        Returns:
            List of all Location objects
        """
        return list(self.locations.values())
    
    def get_locations_by_type(self, location_type: str) -> List[Location]:
        """
        Get all locations of a specific type.
        
        Args:
            location_type: Type of locations to retrieve ('factory', 'warehouse', 'store')
            
        Returns:
            List of Location objects of the specified type
        """
        return [loc for loc in self.locations.values() if loc.location_type == location_type]
    
    def calculate_distance(self, location_id1: str, location_id2: str) -> float:
        """
        Calculate straight-line distance between two locations.
        Uses caching for performance optimization.
        
        Args:
            location_id1: ID of first location
            location_id2: ID of second location
            
        Returns:
            Distance between locations
            
        Raises:
            KeyError: If either location doesn't exist
        """
        if location_id1 not in self.locations:
            raise KeyError(f"Location '{location_id1}' not found")
        if location_id2 not in self.locations:
            raise KeyError(f"Location '{location_id2}' not found")
        
        # Same location
        if location_id1 == location_id2:
            return 0.0
        
        # Check cache (order-independent)
        cache_key = tuple(sorted([location_id1, location_id2]))
        if cache_key in self._distance_cache:
            return self._distance_cache[cache_key]
        
        # Calculate distance
        loc1 = self.locations[location_id1]
        loc2 = self.locations[location_id2]
        distance = loc1.distance_to(loc2)
        
        # Cache the result
        self._distance_cache[cache_key] = distance
        
        return distance
    
    def find_nearest_location(self, location_id: str, location_type: Optional[str] = None) -> Optional[Location]:
        """
        Find the nearest location to a given location, optionally filtered by type.
        
        Args:
            location_id: ID of the reference location
            location_type: Optional type filter ('factory', 'warehouse', 'store')
            
        Returns:
            Nearest Location object or None if no valid locations found
            
        Raises:
            KeyError: If reference location doesn't exist
        """
        if location_id not in self.locations:
            raise KeyError(f"Location '{location_id}' not found")
        
        candidates = self.locations.values()
        if location_type:
            candidates = [loc for loc in candidates if loc.location_type == location_type]
        
        # Exclude the reference location itself
        candidates = [loc for loc in candidates if loc.location_id != location_id]
        
        if not candidates:
            return None
        
        # Find the nearest
        nearest = min(candidates, key=lambda loc: self.calculate_distance(location_id, loc.location_id))
        return nearest
    
    def find_locations_within_radius(self, location_id: str, radius: float, 
                                   location_type: Optional[str] = None) -> List[Location]:
        """
        Find all locations within a given radius of a reference location.
        
        Args:
            location_id: ID of the reference location
            radius: Maximum distance from reference location
            location_type: Optional type filter ('factory', 'warehouse', 'store')
            
        Returns:
            List of Location objects within the radius
            
        Raises:
            KeyError: If reference location doesn't exist
        """
        if location_id not in self.locations:
            raise KeyError(f"Location '{location_id}' not found")
        
        candidates = self.locations.values()
        if location_type:
            candidates = [loc for loc in candidates if loc.location_type == location_type]
        
        # Exclude the reference location itself
        candidates = [loc for loc in candidates if loc.location_id != location_id]
        
        # Filter by radius
        within_radius = []
        for loc in candidates:
            distance = self.calculate_distance(location_id, loc.location_id)
            if distance <= radius:
                within_radius.append(loc)
        
        return within_radius
    
    def get_map_bounds(self) -> Tuple[float, float, float, float]:
        """
        Get the bounding box of all locations in the map.
        
        Returns:
            Tuple of (min_x, min_y, max_x, max_y) or (0, 0, 0, 0) if no locations
        """
        if not self.locations:
            return (0.0, 0.0, 0.0, 0.0)
        
        locations = list(self.locations.values())
        min_x = min(loc.x for loc in locations)
        max_x = max(loc.x for loc in locations)
        min_y = min(loc.y for loc in locations)
        max_y = max(loc.y for loc in locations)
        
        return (min_x, min_y, max_x, max_y)
    
    def get_map_center(self) -> Tuple[float, float]:
        """
        Get the center point of all locations in the map.
        
        Returns:
            Tuple of (center_x, center_y) or (0, 0) if no locations
        """
        if not self.locations:
            return (0.0, 0.0)
        
        min_x, min_y, max_x, max_y = self.get_map_bounds()
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        return (center_x, center_y)
    
    def create_sample_city(self):
        """
        Create a sample city layout for testing and demonstration.
        Adds a few factories, warehouses, and stores in a simple grid pattern.
        """
        # Clear existing locations
        self.locations.clear()
        self._distance_cache.clear()
        
        # Add factories (top row)
        self.add_location(Location("factory_1", "Electronics Factory", 10, 90, "factory"))
        self.add_location(Location("factory_2", "Textile Factory", 50, 90, "factory"))
        
        # Add warehouses (middle row)
        self.add_location(Location("warehouse_1", "North Warehouse", 20, 50, "warehouse"))
        self.add_location(Location("warehouse_2", "South Warehouse", 40, 50, "warehouse"))
        
        # Add stores (bottom rows)
        self.add_location(Location("store_1", "Downtown Store", 10, 20, "store"))
        self.add_location(Location("store_2", "Mall Store", 30, 20, "store"))
        self.add_location(Location("store_3", "Suburb Store", 50, 20, "store"))
        self.add_location(Location("store_4", "Corner Store", 15, 10, "store"))
        self.add_location(Location("store_5", "Plaza Store", 45, 10, "store"))
        
        logger.info("Sample city created with 2 factories, 2 warehouses, and 5 stores")
    
    def get_map_stats(self) -> Dict[str, int]:
        """
        Get statistics about the city map.
        
        Returns:
            Dictionary with location counts by type
        """
        stats = {
            'total_locations': len(self.locations),
            'factories': len(self.get_locations_by_type('factory')),
            'warehouses': len(self.get_locations_by_type('warehouse')),
            'stores': len(self.get_locations_by_type('store')),
            'cached_distances': len(self._distance_cache)
        }
        return stats
    
    def clear_distance_cache(self):
        """Clear the distance calculation cache."""
        self._distance_cache.clear()
        logger.debug("Distance cache cleared")
    
    def __str__(self) -> str:
        """String representation of the city map."""
        stats = self.get_map_stats()
        return f"CityMap({stats['total_locations']} locations: {stats['factories']} factories, {stats['warehouses']} warehouses, {stats['stores']} stores)"
    
    def __len__(self) -> int:
        """Return the number of locations in the map."""
        return len(self.locations)