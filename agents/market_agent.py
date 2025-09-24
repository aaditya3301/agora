"""
Market Agent implementation for the supply chain simulator.
"""
import time
import random
import logging
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from models.message import Message
from models.location import Location

logger = logging.getLogger(__name__)


class MarketAgent(BaseAgent):
    """
    Market agent that generates dynamic demand patterns and market events.
    
    Responsibilities:
    - Periodically update demand at different stores
    - Notify affected store agents when demand changes
    - Create demand spikes or drops when special events occur
    """
    
    def __init__(self, agent_id: str, location: Location, message_bus,
                 store_ids: List[str] = None,
                 base_demand_rate: float = 1.0,
                 demand_variation: float = 0.5,
                 event_probability: float = 0.1):
        """
        Initialize Market Agent.
        
        Args:
            agent_id: Unique identifier for this market agent
            location: Location object for this market agent
            message_bus: MessageBus instance for communication
            store_ids: List of store agent IDs to manage demand for
            base_demand_rate: Base demand rate for stores
            demand_variation: Maximum variation in demand updates (+/-)
            event_probability: Probability of special events per time step
        """
        super().__init__(agent_id, location, message_bus)
        
        # Market-specific state
        self.store_ids = store_ids or []
        self.base_demand_rate = max(base_demand_rate, 2.0)  # Ensure minimum demand for demo
        self.demand_variation = demand_variation
        self.event_probability = max(event_probability, 0.15)  # Increase event probability for demo
        
        # Track current demand rates for each store
        self.store_demand_rates = {store_id: self.base_demand_rate for store_id in self.store_ids}
        
        # Event tracking
        self.active_events = {}  # {event_id: event_data}
        self.event_counter = 0
        self.last_demand_update = 0
        self.demand_update_interval = 3  # Update demand every 3 time steps for more activity
        
        # Initialize state
        self.update_state('store_demand_rates', self.store_demand_rates.copy())
        self.update_state('active_events', len(self.active_events))
        self.update_state('base_demand_rate', self.base_demand_rate)
        self.update_state('demand_variation', self.demand_variation)
        self.update_state('event_probability', self.event_probability)
        
        logger.info(f"Market {self.agent_id} initialized managing {len(self.store_ids)} stores")
    
    def step(self):
        """Execute one simulation step for the market agent."""
        self.last_step_time = time.time()
        
        # Process any incoming messages first
        self.process_messages()
        
        # Check for special events
        self._check_and_trigger_events()
        
        # Update active events
        self._update_active_events()
        
        # Periodically update demand rates
        if self._should_update_demand():
            self._update_demand_patterns()
        
        # Update state for monitoring
        self._update_state()
    
    def handle_message(self, message: Message):
        """
        Handle incoming messages.
        
        Args:
            message: Message to process
        """
        try:
            if message.message_type == "REGISTER_STORE":
                self._handle_store_registration(message)
            elif message.message_type == "UNREGISTER_STORE":
                self._handle_store_unregistration(message)
            else:
                logger.warning(f"Market {self.agent_id} received unknown message type: {message.message_type}")
        except Exception as e:
            logger.error(f"Error handling message in Market {self.agent_id}: {e}")
    
    def _should_update_demand(self) -> bool:
        """
        Check if it's time to update demand patterns.
        
        Returns:
            True if demand should be updated
        """
        current_time = time.time()
        return (current_time - self.last_demand_update) >= self.demand_update_interval
    
    def _update_demand_patterns(self):
        """Update demand patterns for all managed stores."""
        self.last_demand_update = time.time()
        
        for store_id in self.store_ids:
            # Generate new demand rate with variation
            variation = random.uniform(-self.demand_variation, self.demand_variation)
            new_demand_rate = max(0.1, self.base_demand_rate + variation)  # Minimum 0.1 to avoid zero demand
            
            # Apply event modifiers if any active events affect this store
            event_modifier = self._get_event_modifier(store_id)
            new_demand_rate *= event_modifier
            
            # Update stored demand rate
            old_demand_rate = self.store_demand_rates.get(store_id, self.base_demand_rate)
            self.store_demand_rates[store_id] = new_demand_rate
            
            # Notify store of demand change
            self._notify_store_demand_change(store_id, new_demand_rate)
            
            logger.debug(f"Market {self.agent_id} updated demand for {store_id}: {old_demand_rate:.2f} -> {new_demand_rate:.2f}")
    
    def _notify_store_demand_change(self, store_id: str, new_demand_rate: float):
        """
        Notify a store of demand rate change.
        
        Args:
            store_id: Store to notify
            new_demand_rate: New demand rate
        """
        demand_data = {
            'demand_rate': new_demand_rate,
            'timestamp': time.time(),
            'source': 'market_update'
        }
        
        self.send_message(store_id, "DEMAND_UPDATE", demand_data)
        logger.debug(f"Market {self.agent_id} notified {store_id} of demand change: {new_demand_rate:.2f}")
    
    def _check_and_trigger_events(self):
        """Check for and trigger special market events."""
        if random.random() < self.event_probability:
            self._trigger_random_event()
    
    def _trigger_random_event(self):
        """Trigger a random market event."""
        event_types = ['demand_spike', 'demand_drop', 'regional_event']
        event_type = random.choice(event_types)
        
        self.event_counter += 1
        event_id = f"event_{self.event_counter}"
        
        if event_type == 'demand_spike':
            self._trigger_demand_spike(event_id)
        elif event_type == 'demand_drop':
            self._trigger_demand_drop(event_id)
        elif event_type == 'regional_event':
            self._trigger_regional_event(event_id)
    
    def _trigger_demand_spike(self, event_id: str):
        """
        Trigger a demand spike event.
        
        Args:
            event_id: Unique identifier for this event
        """
        # Select random stores to affect (1-3 stores)
        affected_stores = random.sample(self.store_ids, min(random.randint(1, 3), len(self.store_ids)))
        
        # Create event data
        event_data = {
            'type': 'demand_spike',
            'affected_stores': affected_stores,
            'multiplier': random.uniform(1.5, 3.0),  # 1.5x to 3x demand
            'duration': random.randint(3, 8),  # 3-8 time steps
            'remaining_duration': random.randint(3, 8),
            'start_time': time.time()
        }
        
        self.active_events[event_id] = event_data
        
        # Immediately notify affected stores
        for store_id in affected_stores:
            current_demand = self.store_demand_rates.get(store_id, self.base_demand_rate)
            spiked_demand = current_demand * event_data['multiplier']
            self.store_demand_rates[store_id] = spiked_demand
            self._notify_store_demand_change(store_id, spiked_demand)
        
        logger.info(f"Market {self.agent_id} triggered demand spike {event_id} affecting {len(affected_stores)} stores")
    
    def _trigger_demand_drop(self, event_id: str):
        """
        Trigger a demand drop event.
        
        Args:
            event_id: Unique identifier for this event
        """
        # Select random stores to affect (1-2 stores)
        affected_stores = random.sample(self.store_ids, min(random.randint(1, 2), len(self.store_ids)))
        
        # Create event data
        event_data = {
            'type': 'demand_drop',
            'affected_stores': affected_stores,
            'multiplier': random.uniform(0.2, 0.7),  # 20% to 70% of normal demand
            'duration': random.randint(4, 10),  # 4-10 time steps
            'remaining_duration': random.randint(4, 10),
            'start_time': time.time()
        }
        
        self.active_events[event_id] = event_data
        
        # Immediately notify affected stores
        for store_id in affected_stores:
            current_demand = self.store_demand_rates.get(store_id, self.base_demand_rate)
            dropped_demand = current_demand * event_data['multiplier']
            self.store_demand_rates[store_id] = dropped_demand
            self._notify_store_demand_change(store_id, dropped_demand)
        
        logger.info(f"Market {self.agent_id} triggered demand drop {event_id} affecting {len(affected_stores)} stores")
    
    def _trigger_regional_event(self, event_id: str):
        """
        Trigger a regional event affecting multiple stores.
        
        Args:
            event_id: Unique identifier for this event
        """
        # Affect most or all stores
        affected_stores = self.store_ids.copy()
        
        # Random event type (positive or negative)
        is_positive = random.choice([True, False])
        multiplier = random.uniform(1.2, 2.0) if is_positive else random.uniform(0.3, 0.8)
        
        # Create event data
        event_data = {
            'type': 'regional_event',
            'affected_stores': affected_stores,
            'multiplier': multiplier,
            'duration': random.randint(5, 12),  # 5-12 time steps
            'remaining_duration': random.randint(5, 12),
            'start_time': time.time(),
            'is_positive': is_positive
        }
        
        self.active_events[event_id] = event_data
        
        # Immediately notify affected stores
        for store_id in affected_stores:
            current_demand = self.store_demand_rates.get(store_id, self.base_demand_rate)
            modified_demand = current_demand * event_data['multiplier']
            self.store_demand_rates[store_id] = modified_demand
            self._notify_store_demand_change(store_id, modified_demand)
        
        event_type = "positive" if is_positive else "negative"
        logger.info(f"Market {self.agent_id} triggered {event_type} regional event {event_id} affecting all stores")
    
    def _update_active_events(self):
        """Update active events and remove expired ones."""
        expired_events = []
        
        for event_id, event_data in self.active_events.items():
            event_data['remaining_duration'] -= 1
            
            if event_data['remaining_duration'] <= 0:
                expired_events.append(event_id)
        
        # Remove expired events and restore normal demand
        for event_id in expired_events:
            event_data = self.active_events[event_id]
            self._end_event(event_id, event_data)
            del self.active_events[event_id]
    
    def _end_event(self, event_id: str, event_data: Dict[str, Any]):
        """
        End an active event and restore normal demand.
        
        Args:
            event_id: Event identifier
            event_data: Event data dictionary
        """
        affected_stores = event_data['affected_stores']
        
        # Restore normal demand rates for affected stores
        for store_id in affected_stores:
            # Calculate normal demand (base + small random variation)
            variation = random.uniform(-self.demand_variation * 0.5, self.demand_variation * 0.5)
            normal_demand = max(0.1, self.base_demand_rate + variation)
            
            self.store_demand_rates[store_id] = normal_demand
            self._notify_store_demand_change(store_id, normal_demand)
        
        logger.info(f"Market {self.agent_id} ended event {event_id} ({event_data['type']})")
    
    def _get_event_modifier(self, store_id: str) -> float:
        """
        Get the combined event modifier for a store.
        
        Args:
            store_id: Store to check
            
        Returns:
            Combined multiplier from all active events affecting this store
        """
        modifier = 1.0
        
        for event_data in self.active_events.values():
            if store_id in event_data['affected_stores']:
                modifier *= event_data['multiplier']
        
        return modifier
    
    def _handle_store_registration(self, message: Message):
        """
        Handle store registration request.
        
        Args:
            message: Registration message
        """
        data = message.data
        store_id = data.get('store_id')
        
        if store_id and store_id not in self.store_ids:
            self.store_ids.append(store_id)
            self.store_demand_rates[store_id] = self.base_demand_rate
            logger.info(f"Market {self.agent_id} registered store {store_id}")
    
    def _handle_store_unregistration(self, message: Message):
        """
        Handle store unregistration request.
        
        Args:
            message: Unregistration message
        """
        data = message.data
        store_id = data.get('store_id')
        
        if store_id and store_id in self.store_ids:
            self.store_ids.remove(store_id)
            self.store_demand_rates.pop(store_id, None)
            logger.info(f"Market {self.agent_id} unregistered store {store_id}")
    
    def _update_state(self):
        """Update agent state for monitoring."""
        self.update_state('store_demand_rates', self.store_demand_rates.copy())
        self.update_state('active_events', len(self.active_events))
        self.update_state('managed_stores', len(self.store_ids))
        self.update_state('base_demand_rate', self.base_demand_rate)
        self.update_state('demand_variation', self.demand_variation)
        self.update_state('event_probability', self.event_probability)
    
    def add_store(self, store_id: str):
        """
        Add a store to be managed by this market agent.
        
        Args:
            store_id: Store agent ID to add
        """
        if store_id not in self.store_ids:
            self.store_ids.append(store_id)
            self.store_demand_rates[store_id] = self.base_demand_rate
            logger.info(f"Market {self.agent_id} added store {store_id}")
    
    def remove_store(self, store_id: str):
        """
        Remove a store from management by this market agent.
        
        Args:
            store_id: Store agent ID to remove
        """
        if store_id in self.store_ids:
            self.store_ids.remove(store_id)
            self.store_demand_rates.pop(store_id, None)
            logger.info(f"Market {self.agent_id} removed store {store_id}")
    
    def get_store_demand_rate(self, store_id: str) -> float:
        """
        Get current demand rate for a specific store.
        
        Args:
            store_id: Store to check
            
        Returns:
            Current demand rate for the store
        """
        return self.store_demand_rates.get(store_id, self.base_demand_rate)
    
    def get_active_events(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about currently active events.
        
        Returns:
            Dictionary of active events
        """
        import copy
        return copy.deepcopy(self.active_events)
    
    def force_event(self, event_type: str, affected_stores: List[str] = None):
        """
        Force trigger a specific event type (for testing/demo purposes).
        
        Args:
            event_type: Type of event to trigger ('demand_spike', 'demand_drop', 'regional_event')
            affected_stores: Specific stores to affect (optional)
        """
        self.event_counter += 1
        event_id = f"forced_event_{self.event_counter}"
        
        if affected_stores is None:
            affected_stores = random.sample(self.store_ids, min(2, len(self.store_ids)))
        
        if event_type == 'demand_spike':
            self._trigger_demand_spike(event_id)
        elif event_type == 'demand_drop':
            self._trigger_demand_drop(event_id)
        elif event_type == 'regional_event':
            self._trigger_regional_event(event_id)
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this market agent.
        
        Returns:
            Dictionary with performance metrics
        """
        total_events_triggered = self.event_counter
        active_event_count = len(self.active_events)
        average_demand_rate = sum(self.store_demand_rates.values()) / len(self.store_demand_rates) if self.store_demand_rates else 0
        
        return {
            'managed_stores': len(self.store_ids),
            'total_events_triggered': total_events_triggered,
            'active_events': active_event_count,
            'average_demand_rate': average_demand_rate,
            'base_demand_rate': self.base_demand_rate,
            'demand_variation': self.demand_variation,
            'event_probability': self.event_probability,
            'store_demand_rates': self.store_demand_rates.copy(),
            'active_event_details': self.active_events.copy()
        }