"""
Factory Agent implementation for the supply chain simulator.
"""
import time
import logging
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from models.message import Message
from models.order import Order
from models.location import Location

logger = logging.getLogger(__name__)


class FactoryAgent(BaseAgent):
    """
    Factory agent that manages production queue, schedules production,
    and notifies warehouses when production is complete.
    
    Responsibilities:
    - Receive orders from warehouses and add them to production queue
    - Schedule and manage production based on capacity constraints
    - Notify warehouses when production is complete and update inventory
    - Queue additional orders when production capacity is reached
    """
    
    def __init__(self, agent_id: str, location: Location, message_bus,
                 production_capacity: int = 2,
                 production_time: int = 3,
                 initial_inventory: Dict[str, int] = None):
        """
        Initialize Factory Agent.
        
        Args:
            agent_id: Unique identifier for this factory
            location: Location object for this factory
            message_bus: MessageBus instance for communication
            production_capacity: Maximum number of orders that can be produced simultaneously
            production_time: Time steps required to complete production of one order
            initial_inventory: Initial finished goods inventory {product_id: quantity}
        """
        super().__init__(agent_id, location, message_bus)
        
        # Factory-specific configuration
        self.production_capacity = production_capacity
        self.production_time = production_time
        
        # Inventory management
        self.finished_goods_inventory = initial_inventory or {}
        
        # Production queue and scheduling
        self.production_queue = []  # List of Order objects waiting for production
        self.active_production = {}  # {order_id: {'order': Order, 'completion_time': int}}
        self.current_time_step = 0
        
        # Performance tracking
        self.orders_received = 0
        self.orders_completed = 0
        self.total_production_time = 0
        
        # Initialize state
        self._update_state()
        
        logger.info(f"Factory {self.agent_id} initialized with capacity: {self.production_capacity}, "
                   f"production time: {self.production_time} steps")
        logger.info(f"Factory {self.agent_id} initial inventory: {self.finished_goods_inventory}")
    
    def step(self):
        """Execute one simulation step for the factory."""
        self.last_step_time = time.time()
        self.current_time_step += 1
        
        # Process any incoming messages first
        self.process_messages()
        
        # Check for completed production
        self._check_production_completion()
        
        # Start new production if capacity allows
        self._start_new_production()
        
        # Update state for monitoring
        self._update_state()
    
    def handle_message(self, message: Message):
        """
        Handle incoming messages.
        
        Args:
            message: Message to process
        """
        try:
            if message.message_type == "FACTORY_ORDER":
                self._handle_factory_order(message)
            else:
                logger.warning(f"Factory {self.agent_id} received unknown message type: {message.message_type}")
        except Exception as e:
            logger.error(f"Error handling message in Factory {self.agent_id}: {e}")
    
    def _handle_factory_order(self, message: Message):
        """
        Handle production order from warehouse.
        
        Args:
            message: Factory order message from warehouse
        """
        data = message.data
        order_id = data.get('order_id')
        product_id = data.get('product_id')
        quantity = data.get('quantity', 0)
        requester = data.get('requester')
        
        # Validate order data
        if not all([order_id, product_id, quantity > 0, requester]):
            logger.error(f"Factory {self.agent_id} received invalid order data: {data}")
            return
        
        # Create order object
        order = Order(order_id, product_id, quantity, requester)
        
        # Check if we have finished goods in inventory to fulfill immediately
        available_inventory = self.finished_goods_inventory.get(product_id, 0)
        
        if available_inventory >= quantity:
            # Fulfill from inventory immediately
            self._fulfill_from_inventory(order)
        else:
            # Add to production queue
            self.production_queue.append(order)
            self.orders_received += 1
            
            logger.info(f"Factory {self.agent_id} queued order {order_id} for {quantity} units of {product_id}")
            logger.info(f"Factory {self.agent_id} production queue length: {len(self.production_queue)}")
    
    def _fulfill_from_inventory(self, order: Order):
        """
        Fulfill order immediately from finished goods inventory.
        
        Args:
            order: Order to fulfill
        """
        # Reduce inventory
        current_inventory = self.finished_goods_inventory.get(order.product_id, 0)
        self.finished_goods_inventory[order.product_id] = current_inventory - order.quantity
        
        # Notify warehouse immediately
        self._notify_production_complete(order)
        
        logger.info(f"Factory {self.agent_id} fulfilled order {order.order_id} from inventory")
    
    def _check_production_completion(self):
        """Check for completed production and notify warehouses."""
        completed_orders = []
        
        for order_id, production_info in self.active_production.items():
            if self.current_time_step >= production_info['completion_time']:
                completed_orders.append(order_id)
        
        # Process completed orders
        for order_id in completed_orders:
            production_info = self.active_production[order_id]
            order = production_info['order']
            
            # Add to finished goods inventory
            current_inventory = self.finished_goods_inventory.get(order.product_id, 0)
            self.finished_goods_inventory[order.product_id] = current_inventory + order.quantity
            
            # Notify warehouse of completion
            self._notify_production_complete(order)
            
            # Remove from active production
            del self.active_production[order_id]
            
            # Update performance metrics
            self.orders_completed += 1
            production_duration = production_info['completion_time'] - production_info.get('start_time', 0)
            self.total_production_time += production_duration
            
            logger.info(f"Factory {self.agent_id} completed production of order {order_id}")
    
    def _start_new_production(self):
        """Start new production orders if capacity allows."""
        # Check if we have capacity and queued orders
        available_capacity = self.production_capacity - len(self.active_production)
        
        while available_capacity > 0 and self.production_queue:
            # Get next order from queue
            order = self.production_queue.pop(0)
            
            # Start production
            completion_time = self.current_time_step + self.production_time
            
            self.active_production[order.order_id] = {
                'order': order,
                'start_time': self.current_time_step,
                'completion_time': completion_time
            }
            
            order.update_status('processing')
            available_capacity -= 1
            
            logger.info(f"Factory {self.agent_id} started production of order {order.order_id}, "
                       f"completion expected at time step {completion_time}")
    
    def _notify_production_complete(self, order: Order):
        """
        Notify warehouse that production is complete.
        
        Args:
            order: Completed order
        """
        completion_data = {
            'order_id': order.order_id,
            'product_id': order.product_id,
            'quantity': order.quantity
        }
        
        self.send_message(order.requester, "PRODUCTION_COMPLETE", completion_data)
        order.update_status('delivered')
        
        logger.info(f"Factory {self.agent_id} notified {order.requester} of completed order {order.order_id}")
    
    def _update_state(self):
        """Update agent state for monitoring."""
        self.update_state('finished_goods_inventory', self.finished_goods_inventory.copy())
        self.update_state('production_queue_length', len(self.production_queue))
        self.update_state('active_production_count', len(self.active_production))
        self.update_state('production_capacity', self.production_capacity)
        self.update_state('current_time_step', self.current_time_step)
        self.update_state('orders_received', self.orders_received)
        self.update_state('orders_completed', self.orders_completed)
        
        # Calculate capacity utilization
        utilization = len(self.active_production) / max(self.production_capacity, 1)
        self.update_state('capacity_utilization', utilization)
    
    def get_production_status(self) -> Dict[str, Any]:
        """
        Get current production status information.
        
        Returns:
            Dictionary with production status information
        """
        queue_orders = [
            {
                'order_id': order.order_id,
                'product_id': order.product_id,
                'quantity': order.quantity,
                'requester': order.requester
            }
            for order in self.production_queue
        ]
        
        active_orders = {}
        for order_id, production_info in self.active_production.items():
            order = production_info['order']
            active_orders[order_id] = {
                'product_id': order.product_id,
                'quantity': order.quantity,
                'requester': order.requester,
                'completion_time': production_info['completion_time'],
                'remaining_time': max(0, production_info['completion_time'] - self.current_time_step)
            }
        
        return {
            'production_queue': queue_orders,
            'active_production': active_orders,
            'capacity_utilization': len(self.active_production) / max(self.production_capacity, 1),
            'available_capacity': self.production_capacity - len(self.active_production)
        }
    
    def get_inventory_level(self, product_id: str) -> int:
        """
        Get current finished goods inventory level for a product.
        
        Args:
            product_id: Product to check
            
        Returns:
            Current inventory level
        """
        return self.finished_goods_inventory.get(product_id, 0)
    
    def add_product_to_inventory(self, product_id: str, quantity: int):
        """
        Add finished goods to inventory (for testing or initial setup).
        
        Args:
            product_id: Product to add
            quantity: Quantity to add
        """
        current_inventory = self.finished_goods_inventory.get(product_id, 0)
        self.finished_goods_inventory[product_id] = current_inventory + quantity
        logger.info(f"Factory {self.agent_id} added {quantity} units of {product_id} to inventory")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this factory.
        
        Returns:
            Dictionary with performance metrics
        """
        avg_production_time = (
            self.total_production_time / max(self.orders_completed, 1)
            if self.orders_completed > 0 else 0
        )
        
        total_inventory = sum(self.finished_goods_inventory.values())
        
        return {
            'orders_received': self.orders_received,
            'orders_completed': self.orders_completed,
            'orders_in_queue': len(self.production_queue),
            'orders_in_production': len(self.active_production),
            'completion_rate': self.orders_completed / max(self.orders_received, 1),
            'average_production_time': avg_production_time,
            'capacity_utilization': len(self.active_production) / max(self.production_capacity, 1),
            'total_finished_goods': total_inventory,
            'finished_goods_by_product': self.finished_goods_inventory.copy()
        }
    
    def set_production_parameters(self, capacity: Optional[int] = None, 
                                production_time: Optional[int] = None):
        """
        Update production parameters (for testing or configuration changes).
        
        Args:
            capacity: New production capacity
            production_time: New production time in steps
        """
        if capacity is not None and capacity > 0:
            self.production_capacity = capacity
            logger.info(f"Factory {self.agent_id} production capacity updated to {capacity}")
        
        if production_time is not None and production_time > 0:
            self.production_time = production_time
            logger.info(f"Factory {self.agent_id} production time updated to {production_time} steps")