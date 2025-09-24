"""
Truck Agent implementation for the supply chain simulator.
"""
import time
import logging
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from models.message import Message
from models.location import Location

logger = logging.getLogger(__name__)


class TruckAgent(BaseAgent):
    """
    Truck agent that handles movement and cargo management for deliveries.
    
    Responsibilities:
    - Move between pickup and delivery locations
    - Load and unload cargo at appropriate locations
    - Track current position and destination
    - Notify relevant agents when deliveries are complete
    """
    
    def __init__(self, agent_id: str, location: Location, message_bus,
                 city_map, speed: float = 10.0, capacity: int = 100):
        """
        Initialize Truck Agent.
        
        Args:
            agent_id: Unique identifier for this truck
            location: Starting location for this truck
            message_bus: MessageBus instance for communication
            city_map: CityMap instance for location and distance calculations
            speed: Movement speed in distance units per time step
            capacity: Maximum cargo capacity
        """
        super().__init__(agent_id, location, message_bus)
        
        self.city_map = city_map
        self.speed = speed
        self.capacity = capacity
        
        # Truck state
        self.current_location_id = location.location_id
        self.destination_location_id = None
        self.status = 'available'  # 'available', 'moving_to_pickup', 'loading', 'moving_to_delivery', 'unloading'
        
        # Cargo management
        self.cargo = {}  # {product_id: quantity}
        self.current_cargo_weight = 0
        
        # Current assignment
        self.current_order = None
        self.pickup_location_id = None
        self.delivery_location_id = None
        self.dispatcher_id = None  # Who assigned this delivery
        
        # Movement tracking
        self.movement_progress = 0.0  # Progress towards destination (0.0 to 1.0)
        self.total_distance = 0.0
        self.remaining_distance = 0.0
        
        # Performance tracking
        self.deliveries_completed = 0
        self.total_distance_traveled = 0.0
        self.total_cargo_delivered = 0
        
        # Initialize state
        self._update_state()
        
        logger.info(f"Truck {self.agent_id} initialized at {self.location.name} with speed {self.speed} and capacity {self.capacity}")
    
    def step(self):
        """Execute one simulation step for the truck."""
        self.last_step_time = time.time()
        
        # Process any incoming messages first
        self.process_messages()
        
        # Execute behavior based on current status
        if self.status == 'moving_to_pickup':
            self._move_towards_destination()
            if self._has_reached_destination():
                self._arrive_at_pickup()
        
        elif self.status == 'loading':
            self._complete_loading()
        
        elif self.status == 'moving_to_delivery':
            self._move_towards_destination()
            if self._has_reached_destination():
                self._arrive_at_delivery()
        
        elif self.status == 'unloading':
            self._complete_unloading()
        
        # Update state for monitoring
        self._update_state()
    
    def handle_message(self, message: Message):
        """
        Handle incoming messages.
        
        Args:
            message: Message to process
        """
        try:
            if message.message_type == "DISPATCH_ORDER":
                self._handle_dispatch_order(message)
            else:
                logger.warning(f"Truck {self.agent_id} received unknown message type: {message.message_type}")
        except Exception as e:
            logger.error(f"Error handling message in Truck {self.agent_id}: {e}")
    
    def _handle_dispatch_order(self, message: Message):
        """
        Handle dispatch order from warehouse.
        
        Args:
            message: Dispatch order message
        """
        if self.status != 'available':
            logger.warning(f"Truck {self.agent_id} received dispatch order but is not available (status: {self.status})")
            return
        
        data = message.data
        order_id = data.get('order_id')
        product_id = data.get('product_id')
        quantity = data.get('quantity', 0)
        pickup_location = data.get('pickup_location')
        delivery_location = data.get('delivery_location')
        recipient = data.get('recipient')
        
        # Validate dispatch order
        if not all([order_id, product_id, pickup_location, delivery_location, recipient]):
            logger.error(f"Truck {self.agent_id} received invalid dispatch order: missing required fields")
            return
        
        if quantity > self.capacity:
            logger.error(f"Truck {self.agent_id} cannot handle order {order_id}: quantity {quantity} exceeds capacity {self.capacity}")
            return
        
        # Accept the dispatch order
        self.current_order = {
            'order_id': order_id,
            'product_id': product_id,
            'quantity': quantity,
            'recipient': recipient
        }
        
        self.pickup_location_id = pickup_location
        self.delivery_location_id = delivery_location
        self.dispatcher_id = message.sender
        
        # Start moving to pickup location
        if self.current_location_id == pickup_location:
            # Already at pickup location
            self._arrive_at_pickup()
        else:
            self._start_movement_to_pickup()
        
        logger.info(f"Truck {self.agent_id} accepted dispatch order {order_id} from {self.dispatcher_id}")
    
    def _start_movement_to_pickup(self):
        """Start movement towards pickup location."""
        self.destination_location_id = self.pickup_location_id
        self.status = 'moving_to_pickup'
        self.movement_progress = 0.0
        
        # Calculate distance
        try:
            self.total_distance = self.city_map.calculate_distance(
                self.current_location_id, 
                self.destination_location_id
            )
            self.remaining_distance = self.total_distance
        except KeyError as e:
            logger.error(f"Truck {self.agent_id} cannot calculate distance: {e}")
            self._reset_to_available()
            return
        
        logger.info(f"Truck {self.agent_id} starting movement to pickup at {self.pickup_location_id} (distance: {self.total_distance:.1f})")
    
    def _start_movement_to_delivery(self):
        """Start movement towards delivery location."""
        self.destination_location_id = self.delivery_location_id
        self.status = 'moving_to_delivery'
        self.movement_progress = 0.0
        
        # Calculate distance
        try:
            self.total_distance = self.city_map.calculate_distance(
                self.current_location_id, 
                self.destination_location_id
            )
            self.remaining_distance = self.total_distance
        except KeyError as e:
            logger.error(f"Truck {self.agent_id} cannot calculate distance: {e}")
            self._reset_to_available()
            return
        
        logger.info(f"Truck {self.agent_id} starting movement to delivery at {self.delivery_location_id} (distance: {self.total_distance:.1f})")
    
    def _move_towards_destination(self):
        """Move towards the current destination."""
        if self.total_distance <= 0:
            return
        
        # Calculate movement for this step
        distance_this_step = min(self.speed, self.remaining_distance)
        self.remaining_distance -= distance_this_step
        self.movement_progress = 1.0 - (self.remaining_distance / self.total_distance)
        self.total_distance_traveled += distance_this_step
        
        logger.debug(f"Truck {self.agent_id} moved {distance_this_step:.1f} units, {self.remaining_distance:.1f} remaining")
    
    def _has_reached_destination(self) -> bool:
        """Check if truck has reached its destination."""
        return self.remaining_distance <= 0.01  # Small tolerance for floating point precision
    
    def _arrive_at_pickup(self):
        """Handle arrival at pickup location."""
        self.current_location_id = self.pickup_location_id
        self.status = 'loading'
        self.movement_progress = 1.0
        self.remaining_distance = 0.0
        
        # Update location object
        pickup_location = self.city_map.get_location(self.pickup_location_id)
        if pickup_location:
            self.location = pickup_location
        
        logger.info(f"Truck {self.agent_id} arrived at pickup location {self.pickup_location_id}")
    
    def _complete_loading(self):
        """Complete loading cargo at pickup location."""
        if not self.current_order:
            logger.error(f"Truck {self.agent_id} trying to load but has no current order")
            self._reset_to_available()
            return
        
        # Load cargo
        product_id = self.current_order['product_id']
        quantity = self.current_order['quantity']
        
        self.cargo[product_id] = self.cargo.get(product_id, 0) + quantity
        self.current_cargo_weight += quantity  # Simplified weight calculation
        
        # Send pickup complete notification
        pickup_data = {
            'order_id': self.current_order['order_id'],
            'product_id': product_id,
            'quantity': quantity
        }
        
        self.send_message(self.dispatcher_id, "PICKUP_COMPLETE", pickup_data)
        
        # Start movement to delivery location
        if self.current_location_id == self.delivery_location_id:
            # Already at delivery location
            self._arrive_at_delivery()
        else:
            self._start_movement_to_delivery()
        
        logger.info(f"Truck {self.agent_id} loaded {quantity} units of {product_id}")
    
    def _arrive_at_delivery(self):
        """Handle arrival at delivery location."""
        self.current_location_id = self.delivery_location_id
        self.status = 'unloading'
        self.movement_progress = 1.0
        self.remaining_distance = 0.0
        
        # Update location object
        delivery_location = self.city_map.get_location(self.delivery_location_id)
        if delivery_location:
            self.location = delivery_location
        
        logger.info(f"Truck {self.agent_id} arrived at delivery location {self.delivery_location_id}")
    
    def _complete_unloading(self):
        """Complete unloading cargo at delivery location."""
        if not self.current_order:
            logger.error(f"Truck {self.agent_id} trying to unload but has no current order")
            self._reset_to_available()
            return
        
        # Unload cargo
        product_id = self.current_order['product_id']
        quantity = self.current_order['quantity']
        
        if product_id in self.cargo and self.cargo[product_id] >= quantity:
            self.cargo[product_id] -= quantity
            if self.cargo[product_id] == 0:
                del self.cargo[product_id]
            
            self.current_cargo_weight -= quantity
            self.total_cargo_delivered += quantity
            self.deliveries_completed += 1
        else:
            logger.error(f"Truck {self.agent_id} cannot unload {quantity} units of {product_id}: insufficient cargo")
        
        # Send delivery complete notification to dispatcher
        delivery_data = {
            'order_id': self.current_order['order_id'],
            'product_id': product_id,
            'quantity': quantity,
            'delivery_location': self.delivery_location_id
        }
        
        self.send_message(self.dispatcher_id, "DELIVERY_COMPLETE", delivery_data)
        
        # Send delivery notification to recipient
        recipient_data = {
            'order_id': self.current_order['order_id'],
            'product_id': product_id,
            'quantity': quantity
        }
        
        self.send_message(self.current_order['recipient'], "DELIVERY_NOTIFICATION", recipient_data)
        
        # Store recipient for logging before reset
        recipient = self.current_order['recipient']
        
        # Reset to available status
        self._reset_to_available()
        
        logger.info(f"Truck {self.agent_id} completed delivery of {quantity} units of {product_id} to {recipient}")
    
    def _reset_to_available(self):
        """Reset truck to available status."""
        self.status = 'available'
        self.current_order = None
        self.pickup_location_id = None
        self.delivery_location_id = None
        self.destination_location_id = None
        self.dispatcher_id = None
        self.movement_progress = 0.0
        self.total_distance = 0.0
        self.remaining_distance = 0.0
        
        # Notify dispatcher that truck is available
        if self.dispatcher_id:
            self.send_message(self.dispatcher_id, "TRUCK_AVAILABLE", {})
        
        logger.info(f"Truck {self.agent_id} is now available")
    
    def _update_state(self):
        """Update agent state for monitoring."""
        self.update_state('status', self.status)
        self.update_state('current_location_id', self.current_location_id)
        self.update_state('destination_location_id', self.destination_location_id)
        self.update_state('movement_progress', self.movement_progress)
        self.update_state('remaining_distance', self.remaining_distance)
        self.update_state('cargo', self.cargo.copy())
        self.update_state('current_cargo_weight', self.current_cargo_weight)
        self.update_state('current_order', self.current_order)
        self.update_state('deliveries_completed', self.deliveries_completed)
        self.update_state('total_distance_traveled', self.total_distance_traveled)
        self.update_state('total_cargo_delivered', self.total_cargo_delivered)
        self.update_state('capacity', self.capacity)
        self.update_state('interpolated_position', self.get_interpolated_position())
    
    def get_current_location(self) -> Location:
        """
        Get the current location object.
        
        Returns:
            Current Location object
        """
        return self.city_map.get_location(self.current_location_id) or self.location
    
    def get_interpolated_position(self) -> Dict[str, Any]:
        """
        Get interpolated position for smooth animation.
        
        Returns:
            Dictionary with position information
        """
        if self.status in ['moving_to_pickup', 'moving_to_delivery'] and self.destination_location_id:
            current_loc = self.city_map.get_location(self.current_location_id)
            dest_loc = self.city_map.get_location(self.destination_location_id)
            
            if current_loc and dest_loc:
                # Calculate interpolated position
                progress = self.movement_progress
                x = current_loc.x + (dest_loc.x - current_loc.x) * progress
                y = current_loc.y + (dest_loc.y - current_loc.y) * progress
                
                return {
                    'x': x,
                    'y': y,
                    'from_location': self.current_location_id,
                    'to_location': self.destination_location_id,
                    'progress': progress,
                    'is_moving': True
                }
        
        # Return current location if not moving
        current_loc = self.get_current_location()
        return {
            'x': current_loc.x,
            'y': current_loc.y,
            'from_location': self.current_location_id,
            'to_location': None,
            'progress': 1.0,
            'is_moving': False
        }
    
    def is_available(self) -> bool:
        """
        Check if truck is available for new assignments.
        
        Returns:
            True if truck is available, False otherwise
        """
        return self.status == 'available'
    
    def get_cargo_capacity_remaining(self) -> int:
        """
        Get remaining cargo capacity.
        
        Returns:
            Remaining capacity
        """
        return self.capacity - self.current_cargo_weight
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this truck.
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            'deliveries_completed': self.deliveries_completed,
            'total_distance_traveled': self.total_distance_traveled,
            'total_cargo_delivered': self.total_cargo_delivered,
            'current_cargo_weight': self.current_cargo_weight,
            'capacity_utilization': self.current_cargo_weight / self.capacity if self.capacity > 0 else 0,
            'status': self.status,
            'is_available': self.is_available(),
            'remaining_capacity': self.get_cargo_capacity_remaining()
        }