"""
Message Bus implementation for agent communication using publish-subscribe pattern.
"""
from typing import Dict, List, Callable, Any
from collections import defaultdict
import logging
from models.message import Message

logger = logging.getLogger(__name__)


class MessageBus:
    """
    Central message bus for agent communication using publish-subscribe pattern.
    Handles message routing between agents and maintains message queues.
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._agent_queues: Dict[str, List[Message]] = defaultdict(list)
        self._max_queue_size = 100  # Prevent memory issues
        
    def subscribe(self, agent_id: str, message_handler: Callable[[Message], None]):
        """
        Subscribe an agent to receive messages.
        
        Args:
            agent_id: Unique identifier for the agent
            message_handler: Function to handle incoming messages
        """
        self._subscribers[agent_id].append(message_handler)
        logger.debug(f"Agent {agent_id} subscribed to message bus")
    
    def unsubscribe(self, agent_id: str):
        """
        Unsubscribe an agent from receiving messages.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        if agent_id in self._subscribers:
            del self._subscribers[agent_id]
        if agent_id in self._agent_queues:
            del self._agent_queues[agent_id]
        logger.debug(f"Agent {agent_id} unsubscribed from message bus")
    
    def publish(self, message: Message):
        """
        Publish a message to the intended recipient.
        
        Args:
            message: Message object to be delivered
        """
        recipient = message.recipient
        
        # Add to recipient's queue
        if len(self._agent_queues[recipient]) >= self._max_queue_size:
            # FIFO dropping of oldest messages to prevent overflow
            dropped_message = self._agent_queues[recipient].pop(0)
            logger.warning(f"Dropped message for {recipient}: queue overflow")
        
        self._agent_queues[recipient].append(message)
        logger.debug(f"Message queued for {recipient}: {message.message_type}")
    
    def deliver_messages(self, agent_id: str) -> List[Message]:
        """
        Deliver all queued messages for a specific agent.
        
        Args:
            agent_id: Agent to deliver messages to
            
        Returns:
            List of messages for the agent
        """
        messages = self._agent_queues[agent_id].copy()
        self._agent_queues[agent_id].clear()
        
        if messages:
            logger.debug(f"Delivering {len(messages)} messages to {agent_id}")
        
        return messages
    
    def get_queue_size(self, agent_id: str) -> int:
        """
        Get the number of queued messages for an agent.
        
        Args:
            agent_id: Agent to check queue size for
            
        Returns:
            Number of queued messages
        """
        return len(self._agent_queues[agent_id])
    
    def clear_all_queues(self):
        """Clear all message queues. Useful for simulation reset."""
        self._agent_queues.clear()
        logger.info("All message queues cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the message bus state.
        
        Returns:
            Dictionary with message bus statistics
        """
        return {
            'total_subscribers': len(self._subscribers),
            'total_queued_messages': sum(len(queue) for queue in self._agent_queues.values()),
            'queue_sizes': {agent_id: len(queue) for agent_id, queue in self._agent_queues.items()},
            'max_queue_size': self._max_queue_size
        }