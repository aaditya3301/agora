"""Message data model for agent communication."""

from typing import Any, Dict
import time


class Message:
    """Represents a message between agents in the simulation."""
    
    def __init__(self, sender: str, recipient: str, message_type: str, 
                 data: Dict[str, Any], timestamp: float = None):
        """
        Initialize a Message.
        
        Args:
            sender: ID of the agent sending the message
            recipient: ID of the agent receiving the message
            message_type: Type of message (e.g., 'ORDER_REQUEST', 'DELIVERY_NOTIFICATION')
            data: Dictionary containing message payload
            timestamp: When the message was created (defaults to current time)
        """
        if not sender:
            raise ValueError("Sender cannot be empty")
        if not recipient:
            raise ValueError("Recipient cannot be empty")
        if not message_type:
            raise ValueError("Message type cannot be empty")
        if data is None:
            raise ValueError("Data cannot be None")
        
        self.sender = sender
        self.recipient = recipient
        self.message_type = message_type
        self.data = data
        self.timestamp = timestamp if timestamp is not None else time.time()
    
    def __str__(self) -> str:
        return f"Message from {self.sender} to {self.recipient}: {self.message_type}"
    
    def __repr__(self) -> str:
        return f"Message('{self.sender}', '{self.recipient}', '{self.message_type}', {self.data}, {self.timestamp})"