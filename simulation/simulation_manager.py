"""
Simulation Manager to orchestrate time steps and coordinate agent actions.
"""
import time
import logging
from typing import List, Dict, Any, Optional
from agents.base_agent import BaseAgent
from agents.message_bus import MessageBus
from simulation.city_map import CityMap

logger = logging.getLogger(__name__)


class SimulationManager:
    """
    Orchestrates the simulation by managing time steps and coordinating agent actions.
    Handles the main simulation loop and provides control over simulation state.
    """
    
    def __init__(self, city_map: CityMap, message_bus: MessageBus, time_step_duration: float = 1.0):
        """
        Initialize the simulation manager.
        
        Args:
            city_map: CityMap instance managing locations and distances
            message_bus: MessageBus instance for agent communication
            time_step_duration: Duration of each simulation step in seconds
        """
        self.city_map = city_map
        self.message_bus = message_bus
        self.time_step_duration = time_step_duration
        
        self.agents: List[BaseAgent] = []
        self.current_step = 0
        self.simulation_time = 0.0
        self.is_running = False
        self.is_paused = False
        self.start_time = None
        
        logger.info(f"SimulationManager initialized with {time_step_duration}s time steps")
    
    def register_agent(self, agent: BaseAgent):
        """
        Register an agent to participate in the simulation.
        
        Args:
            agent: BaseAgent instance to register
        """
        if agent not in self.agents:
            self.agents.append(agent)
            logger.info(f"Registered agent {agent.agent_id} at {agent.location.name}")
        else:
            logger.warning(f"Agent {agent.agent_id} already registered")
    
    def unregister_agent(self, agent: BaseAgent):
        """
        Unregister an agent from the simulation.
        
        Args:
            agent: BaseAgent instance to unregister
        """
        if agent in self.agents:
            self.agents.remove(agent)
            agent.deactivate()
            logger.info(f"Unregistered agent {agent.agent_id}")
        else:
            logger.warning(f"Agent {agent.agent_id} not found for unregistration")
    
    def start_simulation(self):
        """Start the simulation."""
        if self.is_running:
            logger.warning("Simulation is already running")
            return
        
        self.is_running = True
        self.is_paused = False
        self.start_time = time.time()
        self.current_step = 0
        self.simulation_time = 0.0
        
        logger.info(f"Simulation started with {len(self.agents)} agents")
    
    def pause_simulation(self):
        """Pause the simulation."""
        if not self.is_running:
            logger.warning("Cannot pause: simulation is not running")
            return
        
        self.is_paused = True
        logger.info("Simulation paused")
    
    def resume_simulation(self):
        """Resume a paused simulation."""
        if not self.is_running:
            logger.warning("Cannot resume: simulation is not running")
            return
        
        self.is_paused = False
        logger.info("Simulation resumed")
    
    def stop_simulation(self):
        """Stop the simulation."""
        self.is_running = False
        self.is_paused = False
        
        # Deactivate all agents
        for agent in self.agents:
            agent.deactivate()
        
        # Clear message queues
        self.message_bus.clear_all_queues()
        
        logger.info(f"Simulation stopped after {self.current_step} steps")
    
    def step(self):
        """
        Execute one simulation step.
        
        Returns:
            True if step was executed, False if simulation is not running or paused
        """
        if not self.is_running or self.is_paused:
            return False
        
        step_start_time = time.time()
        
        # Process messages for all agents first
        for agent in self.agents:
            if agent.is_active():
                try:
                    agent.process_messages()
                except Exception as e:
                    logger.error(f"Error processing messages for {agent.agent_id}: {e}")
        
        # Execute agent steps
        active_agents = 0
        for agent in self.agents:
            if agent.is_active():
                try:
                    agent.step()
                    agent.last_step_time = self.simulation_time
                    active_agents += 1
                except Exception as e:
                    logger.error(f"Error in step for {agent.agent_id}: {e}")
                    # Consider deactivating problematic agents
                    agent.deactivate()
        
        # Update simulation state
        self.current_step += 1
        self.simulation_time += self.time_step_duration
        
        step_duration = time.time() - step_start_time
        
        logger.debug(f"Step {self.current_step} completed in {step_duration:.3f}s with {active_agents} active agents")
        
        # Stop simulation if no active agents remain
        if active_agents == 0:
            logger.warning("No active agents remaining, stopping simulation")
            self.stop_simulation()
            return False
        
        return True
    
    def run_for_steps(self, num_steps: int):
        """
        Run the simulation for a specific number of steps.
        
        Args:
            num_steps: Number of steps to execute
        """
        if not self.is_running:
            self.start_simulation()
        
        for _ in range(num_steps):
            if not self.step():
                break
            
            # Sleep to maintain time step duration
            time.sleep(max(0, self.time_step_duration - 0.1))  # Leave some buffer for processing
    
    def run_for_time(self, duration_seconds: float):
        """
        Run the simulation for a specific duration.
        
        Args:
            duration_seconds: How long to run the simulation in seconds
        """
        if not self.is_running:
            self.start_simulation()
        
        end_time = time.time() + duration_seconds
        
        while time.time() < end_time and self.is_running:
            if not self.step():
                break
            
            # Sleep to maintain time step duration
            time.sleep(max(0, self.time_step_duration - 0.1))
    
    def get_simulation_state(self) -> Dict[str, Any]:
        """
        Get current simulation state information.
        
        Returns:
            Dictionary with simulation state data
        """
        active_agents = sum(1 for agent in self.agents if agent.is_active())
        
        return {
            'current_step': self.current_step,
            'simulation_time': self.simulation_time,
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'total_agents': len(self.agents),
            'active_agents': active_agents,
            'time_step_duration': self.time_step_duration,
            'real_time_elapsed': time.time() - self.start_time if self.start_time else 0,
            'message_bus_stats': self.message_bus.get_stats()
        }
    
    def get_agent_states(self) -> List[Dict[str, Any]]:
        """
        Get state information for all registered agents.
        
        Returns:
            List of agent state dictionaries
        """
        return [agent.get_agent_info() for agent in self.agents]
    
    def reset_simulation(self):
        """Reset the simulation to initial state."""
        self.stop_simulation()
        self.current_step = 0
        self.simulation_time = 0.0
        self.start_time = None
        
        # Clear all agent states
        for agent in self.agents:
            agent.state.clear()
            agent.active = True
            agent.last_step_time = 0
        
        logger.info("Simulation reset to initial state")