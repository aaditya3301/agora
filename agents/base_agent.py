"""
Base Agent abstract class with common agent behaviors.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time
import logging
from models.message import Message
from models.location import Location

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the supply chain simulation.
    Provides common functionality for message handling, location management,
    and simulation step execution.
    """
    
    def __init__(self, agent_id: str, location: Location, message_bus):
        """
        Initialize base agent with common properties.
        
        Args:
            agent_id: Unique identifier for this agent
            location: Location object representing agent's position
            message_bus: MessageBus instance for communication
        """
        self.agent_id = agent_id
        self.location = location
        self.message_bus = message_bus
        self.state: Dict[str, Any] = {}
        self.last_step_time = 0
        self.active = True
        
        # Subscribe to message bus
        self.message_bus.subscribe(self.agent_id, self.handle_message)
        logger.info(f"Agent {self.agent_id} initialized at location {self.location.name}")
    
    @abstractmethod
    def step(self):
        """
        Execute one simulation step. Must be implemented by subclasses.
        This method is called once per simulation time step.
        """
        pass
    
    @abstractmethod
    def handle_message(self, message: Message):
        """
        Process incoming messages. Must be implemented by subclasses.
        
        Args:
            message: Message object to process
        """
        pass
    
    def send_message(self, recipient: str, message_type: str, data: Dict[str, Any]):
        """
        Send a message to another agent via the message bus.
        
        Args:
            recipient: Agent ID of the message recipient
            message_type: Type of message being sent
            data: Message payload data
        """
        message = Message(
            sender=self.agent_id,
            recipient=recipient,
            message_type=message_type,
            data=data,
            timestamp=time.time()
        )
        
        self.message_bus.publish(message)
        logger.debug(f"{self.agent_id} sent {message_type} to {recipient}")
    
    def process_messages(self):
        """
        Process all queued messages for this agent.
        Called during each simulation step.
        """
        messages = self.message_bus.deliver_messages(self.agent_id)
        for message in messages:
            try:
                self.handle_message(message)
            except Exception as e:
                logger.error(f"Error processing message in {self.agent_id}: {e}")
                # Continue processing other messages despite errors
    
    def update_state(self, key: str, value: Any):
        """
        Update agent state with validation.
        
        Args:
            key: State key to update
            value: New value for the state key
        """
        old_value = self.state.get(key)
        self.state[key] = value
        logger.debug(f"{self.agent_id} state updated: {key} = {value} (was {old_value})")
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get agent state value.
        
        Args:
            key: State key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            State value or default
        """
        return self.state.get(key, default)
    
    def deactivate(self):
        """
        Deactivate this agent (stops participating in simulation).
        """
        self.active = False
        self.message_bus.unsubscribe(self.agent_id)
        logger.info(f"Agent {self.agent_id} deactivated")
    
    def is_active(self) -> bool:
        """
        Check if agent is active and participating in simulation.
        
        Returns:
            True if agent is active, False otherwise
        """
        return self.active
    
    def get_location_id(self) -> str:
        """
        Get the location ID where this agent is positioned.
        
        Returns:
            Location ID string
        """
        return self.location.location_id
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get basic information about this agent.
        
        Returns:
            Dictionary with agent information
        """
        return {
            'agent_id': self.agent_id,
            'agent_type': self.__class__.__name__.lower().replace('agent', ''),
            'location': self.location.name,
            'location_id': self.location.location_id,
            'active': self.active,
            'is_active': self.active,  # For compatibility
            'state': self.state.copy(),
            'last_step_time': self.last_step_time
        }
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}({self.agent_id}@{self.location.name})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return f"{self.__class__.__name__}(id='{self.agent_id}', location='{self.location.name}', active={self.active})"