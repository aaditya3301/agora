"""
Warehouse Agent implementation for the supply chain simulator.
"""
import time
import logging
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from models.message import Message
from models.order import Order
from models.location import Location

logger = logging.getLogger(__name__)


class WarehouseAgent(BaseAgent):
    """
    Warehouse agent that manages inventory, processes orders from stores, 
    dispatches trucks for deliveries, and places orders with factories.
    
    Responsibilities:
    - Receive and process orders from stores
    - Check inventory availability and dispatch trucks when stock is available
    - Place orders with factories when inventory is low
    - Track truck assignments and delivery status
    """
    
    def __init__(self, agent_id: str, location: Location, message_bus,
                 initial_inventory: Dict[str, int] = None,
                 reorder_threshold: int = 20,
                 reorder_quantity: int = 100,
                 max_trucks: int = 3):
        """
        Initialize Warehouse Agent.
        
        Args:
            agent_id: Unique identifier for this warehouse
            location: Location object for this warehouse
            message_bus: MessageBus instance for communication
            initial_inventory: Initial inventory levels {product_id: quantity}
            reorder_threshold: Inventory level that triggers factory orders
            reorder_quantity: Quantity to order from factory when restocking
            max_trucks: Maximum number of trucks this warehouse can manage
        """
        super().__init__(agent_id, location, message_bus)
        
        # Warehouse-specific state
        self.inventory = initial_inventory or {}
        self.reorder_threshold = reorder_threshold
        self.reorder_quantity = reorder_quantity
        self.max_trucks = max_trucks
        
        # Order management
        self.pending_store_orders = {}  # {order_id: Order} - orders from stores
        self.pending_factory_orders = {}  # {order_id: Order} - orders to factories
        self.processing_orders = {}  # {order_id: Order} - orders being processed
        
        # Truck management
        self.available_trucks = []  # List of available truck agent IDs
        self.assigned_trucks = {}  # {truck_id: order_id} - truck assignments
        
        # Performance tracking
        self.orders_processed = 0
        self.orders_fulfilled = 0
        self.orders_rejected = 0
        
        # Initialize available trucks (assuming truck IDs follow pattern)
        for i in range(1, max_trucks + 1):
            truck_id = f"truck_{self.agent_id}_{i}"
            self.available_trucks.append(truck_id)
        
        # Initialize state
        self._update_state()
        
        logger.info(f"Warehouse {self.agent_id} initialized with inventory: {self.inventory}")
        logger.info(f"Warehouse {self.agent_id} managing trucks: {self.available_trucks}")
    
    def step(self):
        """Execute one simulation step for the warehouse."""
        self.last_step_time = time.time()
        
        # Process any incoming messages first
        self.process_messages()
        
        # Check inventory levels and place factory orders if needed
        self._check_and_reorder_from_factory()
        
        # Process pending store orders
        self._process_pending_orders()
        
        # Record storage costs for inventory
        self._record_storage_costs()
        
        # Update state for monitoring
        self._update_state()
    
    def handle_message(self, message: Message):
        """
        Handle incoming messages.
        
        Args:
            message: Message to process
        """
        try:
            if message.message_type == "ORDER_REQUEST":
                self._handle_store_order(message)
            elif message.message_type == "DELIVERY_COMPLETE":
                self._handle_delivery_complete(message)
            elif message.message_type == "PRODUCTION_COMPLETE":
                self._handle_production_complete(message)
            elif message.message_type == "TRUCK_AVAILABLE":
                self._handle_truck_available(message)
            else:
                logger.warning(f"Warehouse {self.agent_id} received unknown message type: {message.message_type}")
        except Exception as e:
            logger.error(f"Error handling message in Warehouse {self.agent_id}: {e}")
    
    def _handle_store_order(self, message: Message):
        """
        Handle order request from a store.
        
        Args:
            message: Order request message from store
        """
        data = message.data
        order_id = data.get('order_id')
        product_id = data.get('product_id')
        quantity = data.get('quantity', 0)
        requester = data.get('requester')
        delivery_location = data.get('delivery_location')
        
        # Create order object
        order = Order(order_id, product_id, quantity, requester)
        order.delivery_location = delivery_location  # Add delivery location to order
        
        # Add to pending orders
        self.pending_store_orders[order_id] = order
        self.orders_processed += 1
        
        logger.info(f"Warehouse {self.agent_id} received order {order_id} for {quantity} units of {product_id} from {requester}")
    
    def _process_pending_orders(self):
        """Process pending store orders by checking inventory and dispatching trucks."""
        orders_to_remove = []
        
        for order_id, order in self.pending_store_orders.items():
            if self._can_fulfill_order(order):
                if self._dispatch_truck_for_order(order):
                    # Move order to processing
                    self.processing_orders[order_id] = order
                    order.update_status('processing')
                    orders_to_remove.append(order_id)
                    self.orders_fulfilled += 1
                    
                    # Reduce inventory
                    current_inventory = self.inventory.get(order.product_id, 0)
                    self.inventory[order.product_id] = current_inventory - order.quantity
                    
                    logger.info(f"Warehouse {self.agent_id} dispatched truck for order {order_id}")
                # If no truck available, order stays pending
            else:
                # Cannot fulfill order - reject it
                self._reject_order(order)
                orders_to_remove.append(order_id)
                self.orders_rejected += 1
        
        # Remove processed orders from pending
        for order_id in orders_to_remove:
            del self.pending_store_orders[order_id]
    
    def _can_fulfill_order(self, order: Order) -> bool:
        """
        Check if warehouse can fulfill the order based on inventory.
        
        Args:
            order: Order to check
            
        Returns:
            True if order can be fulfilled, False otherwise
        """
        available_quantity = self.inventory.get(order.product_id, 0)
        return available_quantity >= order.quantity
    
    def _dispatch_truck_for_order(self, order: Order) -> bool:
        """
        Dispatch a truck for delivery if one is available.
        
        Args:
            order: Order to dispatch truck for
            
        Returns:
            True if truck was dispatched, False if no trucks available
        """
        if not self.available_trucks:
            logger.warning(f"Warehouse {self.agent_id} has no available trucks for order {order.order_id}")
            return False
        
        # Get an available truck
        truck_id = self.available_trucks.pop(0)
        self.assigned_trucks[truck_id] = order.order_id
        
        # Send dispatch message to truck
        dispatch_data = {
            'order_id': order.order_id,
            'product_id': order.product_id,
            'quantity': order.quantity,
            'pickup_location': self.location.location_id,
            'delivery_location': order.delivery_location,
            'recipient': order.requester
        }
        
        self.send_message(truck_id, "DISPATCH_ORDER", dispatch_data)
        logger.info(f"Warehouse {self.agent_id} dispatched truck {truck_id} for order {order.order_id}")
        
        return True
    
    def _reject_order(self, order: Order):
        """
        Reject an order due to insufficient inventory.
        
        Args:
            order: Order to reject
        """
        rejection_data = {
            'order_id': order.order_id,
            'reason': f'Insufficient inventory. Available: {self.inventory.get(order.product_id, 0)}, Requested: {order.quantity}'
        }
        
        self.send_message(order.requester, "ORDER_REJECTED", rejection_data)
        logger.warning(f"Warehouse {self.agent_id} rejected order {order.order_id}: insufficient inventory")
    
    def _handle_delivery_complete(self, message: Message):
        """
        Handle delivery completion notification from truck.
        
        Args:
            message: Delivery completion message
        """
        data = message.data
        truck_id = message.sender
        order_id = data.get('order_id')
        
        # Mark truck as available again
        if truck_id in self.assigned_trucks:
            del self.assigned_trucks[truck_id]
            self.available_trucks.append(truck_id)
        
        # Update order status and notify store
        if order_id in self.processing_orders:
            order = self.processing_orders[order_id]
            order.update_status('delivered')
            
            # Notify store of delivery
            delivery_data = {
                'order_id': order_id,
                'product_id': order.product_id,
                'quantity': order.quantity
            }
            
            self.send_message(order.requester, "DELIVERY_NOTIFICATION", delivery_data)
            
            # Remove from processing orders
            del self.processing_orders[order_id]
            
            logger.info(f"Warehouse {self.agent_id} completed delivery for order {order_id}")
    
    def _check_and_reorder_from_factory(self):
        """Check inventory levels and place orders with factory if needed."""
        for product_id, quantity in self.inventory.items():
            if quantity <= self.reorder_threshold:
                # Check if we already have a pending factory order for this product
                pending_for_product = any(
                    order.product_id == product_id and order.status == 'pending'
                    for order in self.pending_factory_orders.values()
                )
                
                if not pending_for_product:
                    self._place_factory_order(product_id, self.reorder_quantity)
    
    def _place_factory_order(self, product_id: str, quantity: int):
        """
        Place an order with the factory.
        
        Args:
            product_id: Product to order
            quantity: Quantity to order
        """
        order_id = f"{self.agent_id}_factory_order_{int(time.time() * 1000)}"
        order = Order(order_id, product_id, quantity, self.agent_id)
        
        self.pending_factory_orders[order_id] = order
        
        # Send order to factory (assuming factory_1 for simplicity)
        factory_id = "factory_1"  # In a real system, this would be determined by routing logic
        
        factory_order_data = {
            'order_id': order_id,
            'product_id': product_id,
            'quantity': quantity,
            'requester': self.agent_id
        }
        
        self.send_message(factory_id, "FACTORY_ORDER", factory_order_data)
        logger.info(f"Warehouse {self.agent_id} placed factory order {order_id} for {quantity} units of {product_id}")
    
    def _handle_production_complete(self, message: Message):
        """
        Handle production completion notification from factory.
        
        Args:
            message: Production completion message
        """
        data = message.data
        order_id = data.get('order_id')
        product_id = data.get('product_id')
        quantity = data.get('quantity', 0)
        
        if order_id in self.pending_factory_orders:
            # Update inventory
            current_inventory = self.inventory.get(product_id, 0)
            self.inventory[product_id] = current_inventory + quantity
            
            # Mark factory order as delivered
            self.pending_factory_orders[order_id].update_status('delivered')
            del self.pending_factory_orders[order_id]
            
            logger.info(f"Warehouse {self.agent_id} received production: {quantity} units of {product_id}")
        else:
            logger.warning(f"Warehouse {self.agent_id} received production for unknown order: {order_id}")
    
    def _handle_truck_available(self, message: Message):
        """
        Handle truck becoming available (alternative to delivery complete).
        
        Args:
            message: Truck available message
        """
        truck_id = message.sender
        
        # Mark truck as available if it was assigned
        if truck_id in self.assigned_trucks:
            del self.assigned_trucks[truck_id]
        
        if truck_id not in self.available_trucks:
            self.available_trucks.append(truck_id)
            logger.info(f"Warehouse {self.agent_id} truck {truck_id} is now available")
    
    def _update_state(self):
        """Update agent state for monitoring."""
        self.update_state('inventory', self.inventory.copy())
        self.update_state('pending_store_orders', len(self.pending_store_orders))
        self.update_state('pending_factory_orders', len(self.pending_factory_orders))
        self.update_state('processing_orders', len(self.processing_orders))
        self.update_state('available_trucks', len(self.available_trucks))
        self.update_state('assigned_trucks', len(self.assigned_trucks))
        self.update_state('orders_processed', self.orders_processed)
        self.update_state('orders_fulfilled', self.orders_fulfilled)
        self.update_state('orders_rejected', self.orders_rejected)
    
    def get_inventory_level(self, product_id: str) -> int:
        """
        Get current inventory level for a product.
        
        Args:
            product_id: Product to check
            
        Returns:
            Current inventory level
        """
        return self.inventory.get(product_id, 0)
    
    def add_product(self, product_id: str, initial_quantity: int = 0):
        """
        Add a new product to the warehouse inventory.
        
        Args:
            product_id: Product to add
            initial_quantity: Initial inventory level
        """
        self.inventory[product_id] = initial_quantity
        logger.info(f"Warehouse {self.agent_id} added product {product_id} with {initial_quantity} units")
    
    def get_truck_status(self) -> Dict[str, Any]:
        """
        Get current truck status information.
        
        Returns:
            Dictionary with truck status information
        """
        return {
            'available_trucks': self.available_trucks.copy(),
            'assigned_trucks': self.assigned_trucks.copy(),
            'total_trucks': self.max_trucks
        }
    
    def _record_storage_costs(self):
        """Record storage costs for current inventory in performance tracker."""
        if hasattr(self, 'performance_tracker') and self.performance_tracker:
            for product_id, quantity in self.inventory.items():
                if quantity > 0:
                    storage_cost_per_unit = 0.05  # $0.05 per unit per time step (lower than stores)
                    self.performance_tracker.record_storage_cost(
                        self.agent_id, product_id, quantity, storage_cost_per_unit
                    )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this warehouse.
        
        Returns:
            Dictionary with performance metrics
        """
        total_inventory = sum(self.inventory.values())
        
        return {
            'orders_processed': self.orders_processed,
            'orders_fulfilled': self.orders_fulfilled,
            'orders_rejected': self.orders_rejected,
            'fulfillment_rate': self.orders_fulfilled / max(self.orders_processed, 1),
            'total_inventory': total_inventory,
            'pending_store_orders': len(self.pending_store_orders),
            'pending_factory_orders': len(self.pending_factory_orders),
            'processing_orders': len(self.processing_orders),
            'truck_utilization': len(self.assigned_trucks) / max(self.max_trucks, 1),
            'inventory_by_product': self.inventory.copy()
        }