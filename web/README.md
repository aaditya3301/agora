# Agora Supply Chain Simulator - Web Interface

This web interface provides real-time visualization and control for the Agora Supply Chain Simulator.

## Features

- **Real-time Visualization**: Interactive city map showing locations and agent activities
- **Simulation Controls**: Start, pause, stop, and reset simulation
- **Agent Monitoring**: Live status updates for all agents in the system
- **Performance Metrics**: Real-time tracking of revenue, costs, and efficiency
- **Activity Log**: Detailed log of simulation events and agent actions

## Getting Started

### Prerequisites

Install the required dependencies:

```bash
pip install -r ../requirements.txt
```

### Running the Web Interface

1. **Using the startup script (recommended):**
   ```bash
   python run_web_interface.py
   ```

2. **Direct execution:**
   ```bash
   cd web
   python app.py
   ```

3. **Open your browser** and navigate to: `http://localhost:5000`

## Interface Components

### Control Panel
- **Start Simulation**: Begin or resume the simulation
- **Pause**: Temporarily pause the simulation
- **Stop**: Stop the simulation completely
- **Reset**: Reset simulation to initial state with fresh agents

### City Map
- Visual representation of the supply chain network
- **Green circles**: Factories
- **Orange circles**: Warehouses  
- **Red circles**: Stores
- **Small colored dots**: Agent indicators
- **Dashed lines**: Potential routes between locations

### Information Panel

#### Simulation Status
- Current simulation state (Running/Paused/Stopped)
- Step counter and simulation time
- Number of active agents

#### Agent List
- Real-time status of all agents
- Color-coded by agent type
- Active/Inactive status indicators

#### Performance Metrics
- Total revenue generated
- Storage costs incurred
- Lost sales due to stockouts

### Activity Log
- Real-time log of simulation events
- Color-coded message types (info, warning, error, success)
- Automatically scrolls to show latest activity

## Technical Details

### Architecture
- **Frontend**: HTML5, CSS3, JavaScript with Socket.IO
- **Backend**: Flask with Flask-SocketIO for WebSocket communication
- **Real-time Updates**: WebSocket-based communication for live data

### WebSocket Events

#### Client to Server
- `start_simulation`: Start or resume simulation
- `pause_simulation`: Pause the simulation
- `stop_simulation`: Stop the simulation
- `reset_simulation`: Reset to initial state

#### Server to Client
- `simulation_state`: Current simulation status and metrics
- `agent_states`: List of all agents and their states
- `city_map`: Location data for map visualization
- `activity`: Activity log messages
- `metrics`: Performance metrics updates
- `error`: Error messages

## Customization

### Adding New Locations
Modify the `initialize_simulation()` function in `app.py` to add custom locations:

```python
new_location = Location("custom_id", "Custom Name", x, y, "location_type")
city_map.add_location(new_location)
```

### Styling
Edit `static/css/style.css` to customize the appearance of the interface.

### Agent Visualization
Modify the drawing functions in `static/js/simulation.js` to change how agents and locations are displayed on the map.

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in `app.py` or kill the process using port 5000
2. **Module import errors**: Ensure you're running from the correct directory and all dependencies are installed
3. **WebSocket connection failed**: Check firewall settings and ensure the server is running

### Debug Mode
To enable debug mode, change the last line in `app.py`:
```python
socketio.run(app, debug=True, host='0.0.0.0', port=5000)
```

## Performance Notes

- The interface is optimized for up to 30 agents for smooth visualization
- Canvas rendering is optimized for high-DPI displays
- Activity log is limited to 100 entries to prevent memory issues
- Simulation updates are throttled to prevent UI flooding