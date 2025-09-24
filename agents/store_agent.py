"""
Store Agent implementation for the supply chain simulator.
"""
import time
import logging
from typing import Dict, Any
from agents.base_agent import BaseAgent
from models.message import Message
from models.order import Order
from models.location import Location

logger = logging.getLogger(__name__)


class StoreAgent(BaseAgent):
    """
    Store agent that manages inventory, serves customers, and places orders to warehouses.
    
    Responsibilities:
    - Monitor inventory levels and place orders when stock is low
    - Process customer demand and decrease inventory
    - Receive deliveries and update inventory levels
    """
    
    def __init__(self, agent_id: str, location: Location, message_bus, 
                 initial_inventory: Dict[str, int] = None, 
                 reorder_threshold: int = 10,
                 reorder_quantity: int = 50):
        """
        Initialize Store Agent.
        
        Args:
            agent_id: Unique identifier for this store
            location: Location object for this store
            message_bus: MessageBus instance for communication
            initial_inventory: Initial inventory levels {product_id: quantity}
            reorder_threshold: Inventory level that triggers reordering
            reorder_quantity: Quantity to order when restocking
        """
        super().__init__(agent_id, location, message_bus)
        
        # Store-specific state
        self.inventory = initial_inventory or {}
        self.reorder_threshold = reorder_threshold
        self.reorder_quantity = reorder_quantity
        self.pending_orders = {}  # {order_id: Order}
        self.demand_rate = 1.0  # Base demand rate (customers per time step)
        self.sales_revenue = 0.0
        self.lost_sales = 0  # Track stockouts
        
        # Initialize state
        self.update_state('inventory', self.inventory.copy())
        self.update_state('pending_orders', len(self.pending_orders))
        self.update_state('demand_rate', self.demand_rate)
        self.update_state('sales_revenue', self.sales_revenue)
        self.update_state('lost_sales', self.lost_sales)
        
        logger.info(f"Store {self.agent_id} initialized with inventory: {self.inventory}")
    
    def step(self):
        """Execute one simulation step for the store."""
        self.last_step_time = time.time()
        
        # Process any incoming messages first
        self.process_messages()
        
        # Process customer demand
        self._process_customer_demand()
        
        # Check inventory levels and place orders if needed
        self._check_and_reorder()
        
        # Update state for monitoring
        self._update_state()
    
    def handle_message(self, message: Message):
        """
        Handle incoming messages.
        
        Args:
            message: Message to process
        """
        try:
            if message.message_type == "DELIVERY_NOTIFICATION":
                self._handle_delivery(message)
            elif message.message_type == "DEMAND_UPDATE":
                self._handle_demand_update(message)
            elif message.message_type == "ORDER_REJECTED":
                self._handle_order_rejection(message)
            else:
                logger.warning(f"Store {self.agent_id} received unknown message type: {message.message_type}")
        except Exception as e:
            logger.error(f"Error handling message in Store {self.agent_id}: {e}")
    
    def _process_customer_demand(self):
        """Process customer demand and update inventory."""
        # Simple demand simulation - customers buy products based on demand rate
        import random
        for product_id in list(self.inventory.keys()):
            # Calculate demand for this product (simple random variation around demand rate)
            # Use a simple approach: demand_rate +/- random variation
            variation = random.uniform(-0.5, 0.5)
            demand = max(0, int(self.demand_rate + variation))
            
            if demand > 0:
                available = self.inventory.get(product_id, 0)
                sold = min(demand, available)
                lost = demand - sold
                
                if sold > 0:
                    self.inventory[product_id] = available - sold
                    # Assume $10 per unit for revenue calculation
                    unit_price = 10.0
                    revenue = sold * unit_price
                    self.sales_revenue += revenue
                    
                    # Record sale in performance tracker if available
                    if hasattr(self, 'performance_tracker') and self.performance_tracker:
                        self.performance_tracker.record_sale(
                            self.agent_id, product_id, sold, unit_price
                        )
                    
                    logger.debug(f"Store {self.agent_id} sold {sold} units of {product_id}")
                
                if lost > 0:
                    self.lost_sales += lost
                    lost_revenue = lost * 10.0  # Same unit price
                    
                    # Record stockout in performance tracker if available
                    if hasattr(self, 'performance_tracker') and self.performance_tracker:
                        self.performance_tracker.record_stockout(
                            self.agent_id, product_id, lost, lost_revenue
                        )
                    
                    logger.warning(f"Store {self.agent_id} lost {lost} sales of {product_id} due to stockout")
        
        # Record storage costs for remaining inventory
        if hasattr(self, 'performance_tracker') and self.performance_tracker:
            for product_id, quantity in self.inventory.items():
                if quantity > 0:
                    storage_cost_per_unit = 0.1  # $0.10 per unit per time step
                    self.performance_tracker.record_storage_cost(
                        self.agent_id, product_id, quantity, storage_cost_per_unit
                    )
    
    def _check_and_reorder(self):
        """Check inventory levels and place orders if below threshold."""
        for product_id, quantity in self.inventory.items():
            if quantity <= self.reorder_threshold:
                # Check if we already have a pending order for this product
                pending_for_product = any(
                    order.product_id == product_id and order.status == 'pending'
                    for order in self.pending_orders.values()
                )
                
                if not pending_for_product:
                    self._place_order(product_id, self.reorder_quantity)
    
    def _place_order(self, product_id: str, quantity: int):
        """
        Place an order to the warehouse.
        
        Args:
            product_id: Product to order
            quantity: Quantity to order
        """
        order_id = f"{self.agent_id}_order_{int(time.time() * 1000)}"
        order = Order(order_id, product_id, quantity, self.agent_id)
        
        self.pending_orders[order_id] = order
        
        # Distribute orders between warehouses for better utilization
        # Use simple round-robin based on store number
        import re
        store_num_match = re.search(r'store_(\d+)', self.agent_id)
        if store_num_match:
            store_num = int(store_num_match.group(1))
            # Alternate between warehouse_1 and warehouse_2
            warehouse_id = f"warehouse_{1 + (store_num % 2)}"
        else:
            warehouse_id = "warehouse_1"  # Default fallback
        
        order_data = {
            'order_id': order_id,
            'product_id': product_id,
            'quantity': quantity,
            'requester': self.agent_id,
            'delivery_location': self.location.location_id
        }
        
        self.send_message(warehouse_id, "ORDER_REQUEST", order_data)
        logger.info(f"Store {self.agent_id} placed order {order_id} for {quantity} units of {product_id} to {warehouse_id}")
    
    def _handle_delivery(self, message: Message):
        """
        Handle delivery notification from warehouse.
        
        Args:
            message: Delivery notification message
        """
        data = message.data
        order_id = data.get('order_id')
        product_id = data.get('product_id')
        quantity = data.get('quantity', 0)
        
        if order_id in self.pending_orders:
            # Update inventory
            current_inventory = self.inventory.get(product_id, 0)
            self.inventory[product_id] = current_inventory + quantity
            
            # Mark order as delivered
            self.pending_orders[order_id].update_status('delivered')
            
            logger.info(f"Store {self.agent_id} received delivery: {quantity} units of {product_id}")
        else:
            logger.warning(f"Store {self.agent_id} received delivery for unknown order: {order_id}")
    
    def _handle_demand_update(self, message: Message):
        """
        Handle demand update from market agent.
        
        Args:
            message: Demand update message
        """
        data = message.data
        new_demand_rate = data.get('demand_rate', self.demand_rate)
        
        self.demand_rate = max(0, new_demand_rate)  # Ensure non-negative
        logger.info(f"Store {self.agent_id} updated demand rate to {self.demand_rate}")
    
    def _handle_order_rejection(self, message: Message):
        """
        Handle order rejection from warehouse.
        
        Args:
            message: Order rejection message
        """
        data = message.data
        order_id = data.get('order_id')
        reason = data.get('reason', 'Unknown')
        
        if order_id in self.pending_orders:
            self.pending_orders[order_id].update_status('cancelled')
            logger.warning(f"Store {self.agent_id} order {order_id} rejected: {reason}")
    
    def _update_state(self):
        """Update agent state for monitoring."""
        self.update_state('inventory', self.inventory.copy())
        self.update_state('pending_orders', len(self.pending_orders))
        self.update_state('demand_rate', self.demand_rate)
        self.update_state('sales_revenue', self.sales_revenue)
        self.update_state('lost_sales', self.lost_sales)
    
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
        Add a new product to the store's inventory.
        
        Args:
            product_id: Product to add
            initial_quantity: Initial inventory level
        """
        self.inventory[product_id] = initial_quantity
        logger.info(f"Store {self.agent_id} added product {product_id} with {initial_quantity} units")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this store.
        
        Returns:
            Dictionary with performance metrics
        """
        total_inventory = sum(self.inventory.values())
        pending_order_count = len([o for o in self.pending_orders.values() if o.status == 'pending'])
        
        return {
            'sales_revenue': self.sales_revenue,
            'lost_sales': self.lost_sales,
            'total_inventory': total_inventory,
            'pending_orders': pending_order_count,
            'demand_rate': self.demand_rate,
            'inventory_by_product': self.inventory.copy()
        }