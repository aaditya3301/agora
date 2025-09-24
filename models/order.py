"""Order data model for the supply chain simulator."""

from typing import Literal
import time


class Order:
    """Represents an order in the supply chain."""
    
    def __init__(self, order_id: str, product_id: str, quantity: int, 
                 requester: str, timestamp: float = None):
        """
        Initialize an Order.
        
        Args:
            order_id: Unique identifier for the order
            product_id: ID of the product being ordered
            quantity: Number of units ordered
            requester: ID of the agent placing the order
            timestamp: When the order was created (defaults to current time)
        """
        if not order_id:
            raise ValueError("Order ID cannot be empty")
        if not product_id:
            raise ValueError("Product ID cannot be empty")
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if not requester:
            raise ValueError("Requester cannot be empty")
        
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity
        self.requester = requester
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.status: Literal['pending', 'processing', 'shipped', 'delivered', 'cancelled'] = 'pending'
    
    def update_status(self, new_status: Literal['pending', 'processing', 'shipped', 'delivered', 'cancelled']):
        """Update the order status."""
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        self.status = new_status
    
    def __str__(self) -> str:
        return f"Order {self.order_id}: {self.quantity}x {self.product_id} for {self.requester} ({self.status})"
    
    def __repr__(self) -> str:
        return f"Order('{self.order_id}', '{self.product_id}', {self.quantity}, '{self.requester}', {self.timestamp})"