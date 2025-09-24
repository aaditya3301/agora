"""
Flask web application for Agora Supply Chain Simulator.
Provides web interface and WebSocket communication for real-time simulation updates.
"""
import os
import sys
import logging
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import time

# Add parent directory to path to import simulation modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.simulation_manager import SimulationManager
from simulation.city_map import CityMap
from agents.message_bus import MessageBus
from simulation.performance_tracker import PerformanceTracker
from simulation.agent_integration import AgentIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'agora-supply-chain-simulator'

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Global simulation components
simulation_manager = None
city_map = None
message_bus = None
performance_tracker = None
agent_integration = None
simulation_thread = None
simulation_running = False


def initialize_simulation():
    """Initialize simulation components with error handling."""
    global simulation_manager, city_map, message_bus, performance_tracker, agent_integration
    
    try:
        # Create message bus
        message_bus = MessageBus()
        logger.info("Message bus created")
        
        # Create city map with sample locations
        city_map = CityMap()
        city_map.create_sample_city()  # Use the built-in sample city creation
        logger.info(f"City map created with {len(city_map.locations)} locations")
        
        # Create performance tracker
        performance_tracker = PerformanceTracker()
        logger.info("Performance tracker created")
        
        # Create simulation manager
        simulation_manager = SimulationManager(city_map, message_bus, time_step_duration=1.5)  # Faster for demo
        logger.info("Simulation manager created")
        
        # Create agent integration system
        agent_integration = AgentIntegration(simulation_manager, city_map, message_bus)
        logger.info("Agent integration system created")
        
        logger.info("All simulation components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize simulation components: {e}")
        raise


def create_sample_agents():
    """Create sample agents for demonstration using the agent integration system."""
    try:
        if not agent_integration:
            logger.error("Agent integration not initialized")
            return
        
        # Use the agent integration system to create a complete supply chain
        created_agents = agent_integration.setup_default_supply_chain()
        
        if not created_agents:
            logger.warning("No agents were created")
            return
        
        logger.info(f"Created complete supply chain with {len(agent_integration.get_all_agents())} agents")
        logger.info(f"Agent breakdown: {created_agents}")
        
        # Connect performance tracker to all agents
        all_agents = agent_integration.get_all_agents()
        for agent in all_agents:
            agent.performance_tracker = performance_tracker
        
        # Validate agent setup
        active_agents = sum(1 for agent in all_agents if agent.is_active())
        logger.info(f"Agent validation: {active_agents}/{len(all_agents)} agents are active")
        logger.info(f"Performance tracker connected to {len(all_agents)} agents")
        
    except Exception as e:
        logger.error(f"Failed to create sample agents: {e}")
        # Continue without agents rather than crashing


def simulation_loop():
    """Main simulation loop running in separate thread with error handling."""
    global simulation_running
    
    error_count = 0
    max_errors = 10
    
    while simulation_running and simulation_manager and error_count < max_errors:
        try:
            if simulation_manager.is_running and not simulation_manager.is_paused:
                # Execute simulation step with error handling
                step_success = simulation_manager.step()
                
                if not step_success:
                    logger.warning("Simulation step failed, continuing...")
                    error_count += 1
                    time.sleep(0.5)  # Brief pause on failure
                    continue
                
                # Emit updates to connected clients with enhanced data
                simulation_state = simulation_manager.get_simulation_state()
                agent_states = simulation_manager.get_agent_states()
                
                # Validate data before emitting
                if simulation_state and agent_states is not None:
                    socketio.emit('simulation_state', simulation_state)
                    socketio.emit('agent_states', agent_states)
                    
                    # Emit performance metrics if available
                    if performance_tracker:
                        try:
                            metrics = performance_tracker.get_current_metrics()
                            if metrics:
                                # Add additional summary data
                                metrics['simulation_duration'] = simulation_state.get('simulation_time', 0.0)
                                metrics['total_events'] = metrics.get('sales_events', 0) + metrics.get('stockout_events', 0)
                                metrics['agent_count'] = simulation_state.get('active_agents', 0)
                                
                                socketio.emit('metrics', metrics)
                                logger.debug(f"Emitted metrics: revenue={metrics.get('total_revenue', 0):.2f}, orders={metrics.get('orders_fulfilled', 0)}")
                        except Exception as e:
                            logger.warning(f"Failed to get performance metrics: {e}")
                    
                    # Emit real-time activity updates
                    socketio.emit('activity_update', {
                        'timestamp': time.time(),
                        'active_agents': simulation_state.get('active_agents', 0),
                        'current_step': simulation_state.get('current_step', 0)
                    })
                    
                    # Reset error count on successful step
                    error_count = 0
                else:
                    logger.warning("Invalid simulation state data")
                    error_count += 1
            
            # Sleep for a short time to prevent excessive CPU usage
            time.sleep(0.1)
            
        except Exception as e:
            error_count += 1
            logger.error(f"Error in simulation loop (attempt {error_count}/{max_errors}): {e}")
            
            # Emit error to clients
            socketio.emit('error', {
                'message': f'Simulation error: {str(e)}',
                'recoverable': error_count < max_errors
            })
            
            # Brief pause before retry
            time.sleep(1.0)
    
    if error_count >= max_errors:
        logger.error("Maximum simulation errors reached, stopping simulation")
        socketio.emit('error', {
            'message': 'Simulation stopped due to repeated errors',
            'recoverable': False
        })
        simulation_running = False


@app.route('/')
def index():
    """Serve the main simulation interface."""
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info('Client connected')
    
    # Send initial state to newly connected client
    if simulation_manager:
        emit('simulation_state', simulation_manager.get_simulation_state())
        emit('agent_states', simulation_manager.get_agent_states())
        
        # Send city map data
        locations_data = {
            'locations': {loc_id: {
                'location_id': loc.location_id,
                'name': loc.name,
                'x': loc.x,
                'y': loc.y,
                'location_type': loc.location_type
            } for loc_id, loc in city_map.locations.items()}
        }
        emit('city_map', locations_data)
        
        # Send performance metrics
        if performance_tracker:
            emit('metrics', performance_tracker.get_current_metrics())


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info('Client disconnected')


@socketio.on('start_simulation')
def handle_start_simulation():
    """Handle start simulation request with error handling."""
    global simulation_thread, simulation_running
    
    try:
        if not simulation_manager:
            emit('error', {'message': 'Simulation not initialized', 'recoverable': False})
            return
        
        if simulation_manager.is_running and simulation_manager.is_paused:
            # Resume paused simulation
            simulation_manager.resume_simulation()
            emit('activity', {'message': 'Simulation resumed', 'type': 'success'})
        else:
            # Start new simulation
            simulation_manager.start_simulation()
            
            # Start simulation thread if not already running
            if not simulation_running:
                simulation_running = True
                simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
                simulation_thread.start()
            
            emit('activity', {'message': 'Simulation started', 'type': 'success'})
        
        # Send updated state
        state = simulation_manager.get_simulation_state()
        if state:
            emit('simulation_state', state)
        
    except Exception as e:
        logger.error(f"Error starting simulation: {e}")
        emit('error', {'message': f'Failed to start simulation: {str(e)}', 'recoverable': True})


@socketio.on('pause_simulation')
def handle_pause_simulation():
    """Handle pause simulation request."""
    if not simulation_manager:
        emit('error', {'message': 'Simulation not initialized'})
        return
    
    simulation_manager.pause_simulation()
    emit('activity', {'message': 'Simulation paused', 'type': 'info'})
    emit('simulation_state', simulation_manager.get_simulation_state())


@socketio.on('stop_simulation')
def handle_stop_simulation():
    """Handle stop simulation request."""
    global simulation_running
    
    if not simulation_manager:
        emit('error', {'message': 'Simulation not initialized'})
        return
    
    simulation_manager.stop_simulation()
    simulation_running = False
    
    emit('activity', {'message': 'Simulation stopped', 'type': 'warning'})
    emit('simulation_state', simulation_manager.get_simulation_state())


@socketio.on('reset_simulation')
def handle_reset_simulation():
    """Handle reset simulation request with error handling."""
    global simulation_running
    
    try:
        if not simulation_manager or not agent_integration:
            emit('error', {'message': 'Simulation not initialized', 'recoverable': False})
            return
        
        # Stop current simulation
        simulation_running = False
        simulation_manager.stop_simulation()
        
        # Reset simulation state
        simulation_manager.reset_simulation()
        
        # Reset all agents using integration system
        agent_integration.reset_all_agents()
        
        # Reset performance tracker
        if performance_tracker:
            performance_tracker.reset()
        
        emit('activity', {'message': 'Simulation reset successfully', 'type': 'info'})
        
        # Send updated states
        state = simulation_manager.get_simulation_state()
        agent_states = simulation_manager.get_agent_states()
        
        if state:
            emit('simulation_state', state)
        if agent_states is not None:
            emit('agent_states', agent_states)
        
        # Send empty metrics
        if performance_tracker:
            emit('metrics', performance_tracker.get_current_metrics())
        
    except Exception as e:
        logger.error(f"Error resetting simulation: {e}")
        emit('error', {'message': f'Failed to reset simulation: {str(e)}', 'recoverable': True})


if __name__ == '__main__':
    # Initialize simulation components
    initialize_simulation()
    
    # Create sample agents for demonstration
    create_sample_agents()
    
    # Start the web application
    logger.info("Starting Agora Supply Chain Simulator web interface...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)