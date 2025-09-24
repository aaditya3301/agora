"""
Agent Integration module for wiring all agent types into the simulation manager.
"""
import logging
from typing import Dict, List, Any, Optional
from agents.base_agent import BaseAgent
from agents.store_agent import StoreAgent
from agents.warehouse_agent import WarehouseAgent
from agents.factory_agent import FactoryAgent
from agents.truck_agent import TruckAgent
from agents.market_agent import MarketAgent
from agents.message_bus import MessageBus
from simulation.simulation_manager import SimulationManager
from simulation.city_map import CityMap
from models.location import Location

logger = logging.getLogger(__name__)


class AgentIntegration:
    """
    Handles integration of all agent types with the simulation manager.
    Provides methods for agent registration, configuration, and coordination.
    """
    
    def __init__(self, simulation_manager: SimulationManager, city_map: CityMap, message_bus: MessageBus):
        """
        Initialize agent integration.
        
        Args:
            simulation_manager: SimulationManager instance
            city_map: CityMap instance
            message_bus: MessageBus instance
        """
        self.simulation_manager = simulation_manager
        self.city_map = city_map
        self.message_bus = message_bus
        
        # Agent registries
        self.store_agents: Dict[str, StoreAgent] = {}
        self.warehouse_agents: Dict[str, WarehouseAgent] = {}
        self.factory_agents: Dict[str, FactoryAgent] = {}
        self.truck_agents: Dict[str, TruckAgent] = {}
        self.market_agents: Dict[str, MarketAgent] = {}
        
        logger.info("AgentIntegration initialized")
    
    def create_store_agent(self, agent_id: str, location_id: str, 
                          initial_inventory: Dict[str, int] = None,
                          reorder_threshold: int = 10,
                          reorder_quantity: int = 50) -> StoreAgent:
        """
        Create and register a store agent.
        
        Args:
            agent_id: Unique identifier for the store
            location_id: Location ID where the store is positioned
            initial_inventory: Initial inventory levels
            reorder_threshold: Inventory level that triggers reordering
            reorder_quantity: Quantity to order when restocking
            
        Returns:
            Created StoreAgent instance
            
        Raises:
            KeyError: If location doesn't exist
            ValueError: If agent_id already exists
        """
        if agent_id in self.store_agents:
            raise ValueError(f"Store agent '{agent_id}' already exists")
        
        location = self.city_map.get_location(location_id)
        if not location:
            raise KeyError(f"Location '{location_id}' not found")
        
        # Set default inventory if not provided
        if initial_inventory is None:
            initial_inventory = {"product_1": 25, "product_2": 20}
        
        # Create store agent
        store_agent = StoreAgent(
            agent_id=agent_id,
            location=location,
            message_bus=self.message_bus,
            initial_inventory=initial_inventory,
            reorder_threshold=reorder_threshold,
            reorder_quantity=reorder_quantity
        )
        
        # Register with simulation manager and local registry
        self.simulation_manager.register_agent(store_agent)
        self.store_agents[agent_id] = store_agent
        
        logger.info(f"Created and registered store agent: {agent_id} at {location.name}")
        return store_agent
    
    def create_warehouse_agent(self, agent_id: str, location_id: str,
                              initial_inventory: Dict[str, int] = None,
                              reorder_threshold: int = 20,
                              reorder_quantity: int = 100,
                              max_trucks: int = 3) -> WarehouseAgent:
        """
        Create and register a warehouse agent.
        
        Args:
            agent_id: Unique identifier for the warehouse
            location_id: Location ID where the warehouse is positioned
            initial_inventory: Initial inventory levels
            reorder_threshold: Inventory level that triggers factory orders
            reorder_quantity: Quantity to order from factory
            max_trucks: Maximum number of trucks to manage
            
        Returns:
            Created WarehouseAgent instance
            
        Raises:
            KeyError: If location doesn't exist
            ValueError: If agent_id already exists
        """
        if agent_id in self.warehouse_agents:
            raise ValueError(f"Warehouse agent '{agent_id}' already exists")
        
        location = self.city_map.get_location(location_id)
        if not location:
            raise KeyError(f"Location '{location_id}' not found")
        
        # Set default inventory if not provided
        if initial_inventory is None:
            initial_inventory = {"product_1": 50, "product_2": 40}
        
        # Create warehouse agent
        warehouse_agent = WarehouseAgent(
            agent_id=agent_id,
            location=location,
            message_bus=self.message_bus,
            initial_inventory=initial_inventory,
            reorder_threshold=reorder_threshold,
            reorder_quantity=reorder_quantity,
            max_trucks=max_trucks
        )
        
        # Register with simulation manager and local registry
        self.simulation_manager.register_agent(warehouse_agent)
        self.warehouse_agents[agent_id] = warehouse_agent
        
        logger.info(f"Created and registered warehouse agent: {agent_id} at {location.name}")
        return warehouse_agent
    
    def create_factory_agent(self, agent_id: str, location_id: str,
                            production_capacity: int = 2,
                            production_time: int = 3,
                            initial_inventory: Dict[str, int] = None) -> FactoryAgent:
        """
        Create and register a factory agent.
        
        Args:
            agent_id: Unique identifier for the factory
            location_id: Location ID where the factory is positioned
            production_capacity: Maximum concurrent production orders
            production_time: Time steps to complete production
            initial_inventory: Initial finished goods inventory
            
        Returns:
            Created FactoryAgent instance
            
        Raises:
            KeyError: If location doesn't exist
            ValueError: If agent_id already exists
        """
        if agent_id in self.factory_agents:
            raise ValueError(f"Factory agent '{agent_id}' already exists")
        
        location = self.city_map.get_location(location_id)
        if not location:
            raise KeyError(f"Location '{location_id}' not found")
        
        # Set default inventory if not provided
        if initial_inventory is None:
            initial_inventory = {"product_1": 30, "product_2": 25}
        
        # Create factory agent
        factory_agent = FactoryAgent(
            agent_id=agent_id,
            location=location,
            message_bus=self.message_bus,
            production_capacity=production_capacity,
            production_time=production_time,
            initial_inventory=initial_inventory
        )
        
        # Register with simulation manager and local registry
        self.simulation_manager.register_agent(factory_agent)
        self.factory_agents[agent_id] = factory_agent
        
        logger.info(f"Created and registered factory agent: {agent_id} at {location.name}")
        return factory_agent
    
    def create_truck_agent(self, agent_id: str, location_id: str,
                          speed: float = 10.0, capacity: int = 100) -> TruckAgent:
        """
        Create and register a truck agent.
        
        Args:
            agent_id: Unique identifier for the truck
            location_id: Starting location ID for the truck
            speed: Movement speed in distance units per time step
            capacity: Maximum cargo capacity
            
        Returns:
            Created TruckAgent instance
            
        Raises:
            KeyError: If location doesn't exist
            ValueError: If agent_id already exists
        """
        if agent_id in self.truck_agents:
            raise ValueError(f"Truck agent '{agent_id}' already exists")
        
        location = self.city_map.get_location(location_id)
        if not location:
            raise KeyError(f"Location '{location_id}' not found")
        
        # Create truck agent
        truck_agent = TruckAgent(
            agent_id=agent_id,
            location=location,
            message_bus=self.message_bus,
            city_map=self.city_map,
            speed=speed,
            capacity=capacity
        )
        
        # Register with simulation manager and local registry
        self.simulation_manager.register_agent(truck_agent)
        self.truck_agents[agent_id] = truck_agent
        
        logger.info(f"Created and registered truck agent: {agent_id} at {location.name}")
        return truck_agent
    
    def create_market_agent(self, agent_id: str, location_id: str,
                           store_ids: List[str] = None,
                           base_demand_rate: float = 1.0,
                           demand_variation: float = 0.5,
                           event_probability: float = 0.1) -> MarketAgent:
        """
        Create and register a market agent.
        
        Args:
            agent_id: Unique identifier for the market agent
            location_id: Location ID for the market agent
            store_ids: List of store IDs to manage demand for
            base_demand_rate: Base demand rate for stores
            demand_variation: Maximum variation in demand updates
            event_probability: Probability of special events per time step
            
        Returns:
            Created MarketAgent instance
            
        Raises:
            KeyError: If location doesn't exist
            ValueError: If agent_id already exists
        """
        if agent_id in self.market_agents:
            raise ValueError(f"Market agent '{agent_id}' already exists")
        
        location = self.city_map.get_location(location_id)
        if not location:
            raise KeyError(f"Location '{location_id}' not found")
        
        # Use all store agents if no specific list provided
        if store_ids is None:
            store_ids = list(self.store_agents.keys())
        
        # Create market agent
        market_agent = MarketAgent(
            agent_id=agent_id,
            location=location,
            message_bus=self.message_bus,
            store_ids=store_ids,
            base_demand_rate=base_demand_rate,
            demand_variation=demand_variation,
            event_probability=event_probability
        )
        
        # Register with simulation manager and local registry
        self.simulation_manager.register_agent(market_agent)
        self.market_agents[agent_id] = market_agent
        
        logger.info(f"Created and registered market agent: {agent_id} managing {len(store_ids)} stores")
        return market_agent
    
    def create_trucks_for_warehouse(self, warehouse_id: str, num_trucks: int = 3) -> List[TruckAgent]:
        """
        Create multiple truck agents for a specific warehouse.
        
        Args:
            warehouse_id: Warehouse agent ID to create trucks for
            num_trucks: Number of trucks to create
            
        Returns:
            List of created TruckAgent instances
            
        Raises:
            ValueError: If warehouse doesn't exist
        """
        if warehouse_id not in self.warehouse_agents:
            raise ValueError(f"Warehouse '{warehouse_id}' not found")
        
        warehouse = self.warehouse_agents[warehouse_id]
        warehouse_location_id = warehouse.location.location_id
        
        trucks = []
        for i in range(1, num_trucks + 1):
            truck_id = f"truck_{warehouse_id}_{i}"
            try:
                truck = self.create_truck_agent(truck_id, warehouse_location_id)
                trucks.append(truck)
            except ValueError:
                # Truck already exists, skip
                logger.warning(f"Truck {truck_id} already exists, skipping")
                continue
        
        logger.info(f"Created {len(trucks)} trucks for warehouse {warehouse_id}")
        return trucks
    
    def setup_default_supply_chain(self) -> Dict[str, List[str]]:
        """
        Set up a default supply chain configuration with all agent types.
        Creates a complete supply chain with factories, warehouses, stores, trucks, and market.
        
        Returns:
            Dictionary with lists of created agent IDs by type
        """
        # Ensure we have a sample city
        if len(self.city_map) == 0:
            self.city_map.create_sample_city()
        
        created_agents = {
            'factories': [],
            'warehouses': [],
            'stores': [],
            'trucks': [],
            'markets': []
        }
        
        # Create factory agents
        factory_locations = self.city_map.get_locations_by_type('factory')
        for i, location in enumerate(factory_locations, 1):
            factory_id = f"factory_{i}"
            try:
                self.create_factory_agent(factory_id, location.location_id)
                created_agents['factories'].append(factory_id)
            except ValueError:
                logger.warning(f"Factory {factory_id} already exists")
        
        # Create warehouse agents
        warehouse_locations = self.city_map.get_locations_by_type('warehouse')
        for i, location in enumerate(warehouse_locations, 1):
            warehouse_id = f"warehouse_{i}"
            try:
                self.create_warehouse_agent(warehouse_id, location.location_id)
                created_agents['warehouses'].append(warehouse_id)
                
                # Create trucks for this warehouse
                trucks = self.create_trucks_for_warehouse(warehouse_id, 3)
                created_agents['trucks'].extend([truck.agent_id for truck in trucks])
            except ValueError:
                logger.warning(f"Warehouse {warehouse_id} already exists")
        
        # Create store agents
        store_locations = self.city_map.get_locations_by_type('store')
        for i, location in enumerate(store_locations, 1):
            store_id = f"store_{i}"
            try:
                self.create_store_agent(store_id, location.location_id)
                created_agents['stores'].append(store_id)
            except ValueError:
                logger.warning(f"Store {store_id} already exists")
        
        # Create market agent to manage all stores
        if created_agents['stores']:
            # Use the first warehouse location for the market agent
            market_location_id = warehouse_locations[0].location_id if warehouse_locations else store_locations[0].location_id
            try:
                market_agent = self.create_market_agent(
                    "market_1", 
                    market_location_id, 
                    created_agents['stores']
                )
                created_agents['markets'].append(market_agent.agent_id)
            except ValueError:
                logger.warning("Market agent already exists")
        
        logger.info(f"Default supply chain setup complete: {created_agents}")
        return created_agents
    
    def get_all_agents(self) -> List[BaseAgent]:
        """
        Get all registered agents.
        
        Returns:
            List of all agent instances
        """
        all_agents = []
        all_agents.extend(self.store_agents.values())
        all_agents.extend(self.warehouse_agents.values())
        all_agents.extend(self.factory_agents.values())
        all_agents.extend(self.truck_agents.values())
        all_agents.extend(self.market_agents.values())
        return all_agents
    
    def get_agent_by_id(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an agent by its ID.
        
        Args:
            agent_id: Agent ID to search for
            
        Returns:
            Agent instance or None if not found
        """
        # Check all agent registries
        for registry in [self.store_agents, self.warehouse_agents, self.factory_agents, 
                        self.truck_agents, self.market_agents]:
            if agent_id in registry:
                return registry[agent_id]
        return None
    
    def get_agents_by_type(self, agent_type: str) -> List[BaseAgent]:
        """
        Get all agents of a specific type.
        
        Args:
            agent_type: Type of agents to retrieve ('store', 'warehouse', 'factory', 'truck', 'market')
            
        Returns:
            List of agents of the specified type
        """
        if agent_type == 'store':
            return list(self.store_agents.values())
        elif agent_type == 'warehouse':
            return list(self.warehouse_agents.values())
        elif agent_type == 'factory':
            return list(self.factory_agents.values())
        elif agent_type == 'truck':
            return list(self.truck_agents.values())
        elif agent_type == 'market':
            return list(self.market_agents.values())
        else:
            return []
    
    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the simulation.
        
        Args:
            agent_id: Agent ID to remove
            
        Returns:
            True if agent was removed, False if not found
        """
        agent = self.get_agent_by_id(agent_id)
        if not agent:
            return False
        
        # Unregister from simulation manager
        self.simulation_manager.unregister_agent(agent)
        
        # Remove from appropriate registry
        if agent_id in self.store_agents:
            del self.store_agents[agent_id]
        elif agent_id in self.warehouse_agents:
            del self.warehouse_agents[agent_id]
        elif agent_id in self.factory_agents:
            del self.factory_agents[agent_id]
        elif agent_id in self.truck_agents:
            del self.truck_agents[agent_id]
        elif agent_id in self.market_agents:
            del self.market_agents[agent_id]
        
        logger.info(f"Removed agent: {agent_id}")
        return True
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the integrated agents.
        
        Returns:
            Dictionary with integration statistics
        """
        return {
            'total_agents': len(self.get_all_agents()),
            'store_agents': len(self.store_agents),
            'warehouse_agents': len(self.warehouse_agents),
            'factory_agents': len(self.factory_agents),
            'truck_agents': len(self.truck_agents),
            'market_agents': len(self.market_agents),
            'simulation_registered_agents': len(self.simulation_manager.agents),
            'city_map_locations': len(self.city_map),
            'message_bus_stats': self.message_bus.get_stats()
        }
    
    def reset_all_agents(self):
        """Reset all agents to their initial state."""
        for agent in self.get_all_agents():
            agent.state.clear()
            agent.active = True
            agent.last_step_time = 0
        
        # Clear message bus
        self.message_bus.clear_all_queues()
        
        logger.info("All agents reset to initial state")