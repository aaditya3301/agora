// Agora Supply Chain Simulator - Frontend JavaScript

class SimulationUI {
    constructor() {
        this.socket = null;
        this.canvas = null;
        this.ctx = null;
        this.locations = {};
        this.agents = {};
        this.isConnected = false;

        // Animation and visual state
        this.animationFrame = null;
        this.lastUpdateTime = 0;
        this.truckAnimations = new Map(); // Track truck movement animations
        this.inventoryDisplays = new Map(); // Track inventory displays
        this.statusIndicators = new Map(); // Track status indicators

        // Performance optimization
        this.frameSkipCounter = 0;
        this.maxFrameSkip = 2; // Skip frames for better performance
        this.lastDataUpdate = 0;
        this.updateThrottle = 100; // Minimum ms between data updates

        // Visual settings
        this.mapScale = 6; // Smaller scale to fit more locations
        this.mapOffset = { x: 50, y: 80 }; // More top margin to show factories
        this.agentSize = 12; // Size of agent indicators
        this.locationSize = 20; // Size of location indicators

        // Error handling
        this.errorCount = 0;
        this.maxErrors = 5;
        this.lastErrorTime = 0;

        this.init();
    }

    init() {
        // Initialize WebSocket connection
        this.initSocket();

        // Initialize canvas
        this.initCanvas();

        // Bind event listeners
        this.bindEvents();

        // Start animation loop
        this.startAnimationLoop();

        // Initial UI state
        this.updateSimulationStatus({
            is_running: false,
            is_paused: false,
            current_step: 0,
            simulation_time: 0.0,
            active_agents: 0
        });
    }

    initSocket() {
        console.log('Initializing WebSocket connection...');
        try {
            this.socket = io({
                timeout: 5000,
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000
            });
            console.log('Socket.IO initialized');

            this.socket.on('connect', () => {
                console.log('Connected to simulation server');
                this.isConnected = true;
                this.errorCount = 0; // Reset error count on successful connection
                this.updateConnectionStatus('connected');
                this.logActivity('Connected to simulation server', 'success');
                this.logActivity('Map Guide: Dashed lines show supply routes (factories to warehouses to stores)', 'info');
                this.logActivity('Light purple lines with arrows show active deliveries', 'info');
                this.logActivity('Hover over locations for detailed information', 'info');
            });

            this.socket.on('disconnect', (reason) => {
                console.log('Disconnected from simulation server:', reason);
                this.isConnected = false;
                this.updateConnectionStatus('disconnected');
                this.logActivity(`Disconnected: ${reason}`, 'warning');
            });

            this.socket.on('connect_error', (error) => {
                console.error('Connection error:', error);
                this.handleError('Connection failed', error);
            });

            this.socket.on('reconnect', (attemptNumber) => {
                console.log('Reconnected after', attemptNumber, 'attempts');
                this.updateConnectionStatus('connected');
                this.logActivity(`Reconnected after ${attemptNumber} attempts`, 'success');
            });

            this.socket.on('reconnect_error', (error) => {
                console.error('Reconnection failed:', error);
                this.updateConnectionStatus('disconnected');
                this.handleError('Reconnection failed', error);
            });
        } catch (error) {
            console.error('Failed to initialize socket:', error);
            this.handleError('Socket initialization failed', error);
        }

        this.socket.on('simulation_state', (data) => {
            this.updateSimulationStatus(data);
        });

        this.socket.on('agent_states', (data) => {
            this.updateAgentStates(data);
            this.updateInventoryDisplays(data);
            this.updateStatusIndicators(data);
        });

        this.socket.on('city_map', (data) => {
            this.updateCityMap(data);
        });

        this.socket.on('activity', (data) => {
            this.logActivity(data.message, data.type || 'info');
        });

        this.socket.on('metrics', (data) => {
            this.updateMetrics(data);
        });

        this.socket.on('error', (data) => {
            console.error('Simulation error:', data);
            this.logActivity(`Error: ${data.message}`, 'error');
        });

        this.socket.on('activity_update', (data) => {
            // Handle real-time activity updates for enhanced visual feedback
            this.handleActivityUpdate(data);
        });
    }

    initCanvas() {
        this.canvas = document.getElementById('cityMap');
        this.ctx = this.canvas.getContext('2d');

        // Set up canvas for high DPI displays
        const rect = this.canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;

        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.ctx.scale(dpr, dpr);

        // Initial draw
        this.drawCityMap();
    }

    bindEvents() {
        // Control buttons
        document.getElementById('startBtn').addEventListener('click', () => {
            this.startSimulation();
        });

        document.getElementById('pauseBtn').addEventListener('click', () => {
            this.pauseSimulation();
        });

        document.getElementById('stopBtn').addEventListener('click', () => {
            this.stopSimulation();
        });

        document.getElementById('resetBtn').addEventListener('click', () => {
            this.resetSimulation();
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            this.initCanvas();
        });

        // Add mouse hover for route information
        this.canvas.addEventListener('mousemove', (event) => {
            this.handleCanvasHover(event);
        });
    }

    // WebSocket communication methods
    startSimulation() {
        if (this.isConnected) {
            this.socket.emit('start_simulation');
            this.logActivity('Starting simulation...', 'info');
        }
    }

    pauseSimulation() {
        if (this.isConnected) {
            this.socket.emit('pause_simulation');
            this.logActivity('Pausing simulation...', 'info');
        }
    }

    stopSimulation() {
        if (this.isConnected) {
            this.socket.emit('stop_simulation');
            this.logActivity('Stopping simulation...', 'info');
        }
    }

    resetSimulation() {
        if (this.isConnected) {
            this.socket.emit('reset_simulation');
            this.logActivity('Resetting simulation...', 'info');
        }
    }

    // Animation methods
    startAnimationLoop() {
        const animate = (currentTime) => {
            if (currentTime - this.lastUpdateTime > 50) { // Update at ~20 FPS
                this.drawCityMap();
                this.lastUpdateTime = currentTime;
            }
            this.animationFrame = requestAnimationFrame(animate);
        };
        this.animationFrame = requestAnimationFrame(animate);
    }

    handleError(message, error) {
        console.error(`${message}:`, error);
        this.logActivity(`${message}: ${error.message || error}`, 'error');
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.className = `connection-status ${status}`;
            switch (status) {
                case 'connected':
                    statusElement.textContent = 'Connected';
                    break;
                case 'disconnected':
                    statusElement.textContent = 'Disconnected';
                    break;
                case 'reconnecting':
                    statusElement.textContent = 'Reconnecting...';
                    break;
                default:
                    statusElement.textContent = 'Unknown';
            }
        }
    }

    showErrorBanner(message) {
        const errorBanner = document.getElementById('errorBanner');
        if (errorBanner) {
            errorBanner.textContent = message;
            errorBanner.classList.add('show');
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                errorBanner.classList.remove('show');
            }, 5000);
        }
    }

    handleCanvasHover(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Check if hovering over a location
        const hoveredLocation = this.getLocationAtPosition(x, y);
        if (hoveredLocation) {
            this.showLocationTooltip(hoveredLocation, event.clientX, event.clientY);
        } else {
            this.hideTooltip();
        }
    }

    getLocationAtPosition(x, y) {
        for (const location of Object.values(this.locations)) {
            const locX = location.x * this.mapScale + this.mapOffset.x;
            const locY = location.y * this.mapScale + this.mapOffset.y;
            const distance = Math.sqrt((x - locX) ** 2 + (y - locY) ** 2);
            
            if (distance <= this.locationSize + 5) {
                return location;
            }
        }
        return null;
    }

    showLocationTooltip(location, mouseX, mouseY) {
        let tooltip = document.getElementById('locationTooltip');
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'locationTooltip';
            tooltip.style.cssText = `
                position: fixed;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 12px;
                pointer-events: none;
                z-index: 1000;
                max-width: 200px;
            `;
            document.body.appendChild(tooltip);
        }

        // Get agents at this location
        const agentsHere = Object.values(this.agents).filter(
            agent => agent.location_id === location.location_id
        );

        let content = `<strong>${location.name}</strong><br>`;
        content += `Type: ${location.location_type}<br>`;
        
        if (agentsHere.length > 0) {
            content += `Agents: ${agentsHere.length}<br>`;
            
            // Show inventory if available
            const storeAgent = agentsHere.find(a => this.getAgentType(a) === 'store');
            if (storeAgent && storeAgent.state && storeAgent.state.inventory) {
                const totalInventory = Object.values(storeAgent.state.inventory).reduce((sum, qty) => sum + qty, 0);
                content += `Inventory: ${totalInventory} units`;
            }
            
            const warehouseAgent = agentsHere.find(a => this.getAgentType(a) === 'warehouse');
            if (warehouseAgent && warehouseAgent.state && warehouseAgent.state.inventory) {
                const totalInventory = Object.values(warehouseAgent.state.inventory).reduce((sum, qty) => sum + qty, 0);
                content += `Stock: ${totalInventory} units`;
            }
        }

        tooltip.innerHTML = content;
        tooltip.style.left = (mouseX + 10) + 'px';
        tooltip.style.top = (mouseY - 10) + 'px';
        tooltip.style.display = 'block';
    }

    hideTooltip() {
        const tooltip = document.getElementById('locationTooltip');
        if (tooltip) {
            tooltip.style.display = 'none';
        }
    }

    stopAnimationLoop() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
    }

    handleActivityUpdate(data) {
        // Add visual feedback for activity updates
        const timestamp = new Date(data.timestamp * 1000).toLocaleTimeString();

        // Update step counter with animation
        const stepElement = document.getElementById('simStep');
        if (stepElement && data.current_step) {
            stepElement.textContent = data.current_step;
            stepElement.classList.add('pulse');
            setTimeout(() => stepElement.classList.remove('pulse'), 1000);
        }

        // Update active agents counter with animation
        const agentsElement = document.getElementById('activeAgents');
        if (agentsElement && data.active_agents !== undefined) {
            agentsElement.textContent = data.active_agents;
            agentsElement.classList.add('fade-in');
            setTimeout(() => agentsElement.classList.remove('fade-in'), 500);
        }
    }

    // UI update methods
    updateSimulationStatus(data) {
        const status = data.is_running ? (data.is_paused ? 'Paused' : 'Running') : 'Stopped';
        document.getElementById('simStatus').textContent = status;
        document.getElementById('simStep').textContent = data.current_step || 0;
        document.getElementById('simTime').textContent = `${(data.simulation_time || 0).toFixed(1)}s`;
        document.getElementById('activeAgents').textContent = data.active_agents || 0;
        
        // Update status dot
        const statusDot = document.getElementById('statusDot');
        if (statusDot) {
            statusDot.className = 'status-dot';
            if (data.is_running && !data.is_paused) {
                statusDot.classList.add('running');
            } else if (data.is_paused) {
                statusDot.classList.add('paused');
            } else {
                statusDot.classList.add('stopped');
            }
        }
        
        // Update agent count display
        const agentCount = document.getElementById('agentCount');
        if (agentCount) {
            const count = data.active_agents || 0;
            agentCount.textContent = `${count} agent${count !== 1 ? 's' : ''}`;
        }

        // Update button states
        const startBtn = document.getElementById('startBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const stopBtn = document.getElementById('stopBtn');

        if (data.is_running) {
            startBtn.disabled = true;
            pauseBtn.disabled = data.is_paused;
            stopBtn.disabled = false;

            if (data.is_paused) {
                startBtn.disabled = false;
                startBtn.textContent = 'Resume';
            } else {
                startBtn.textContent = 'Start Simulation';
            }
        } else {
            startBtn.disabled = false;
            startBtn.textContent = 'Start Simulation';
            pauseBtn.disabled = true;
            stopBtn.disabled = true;
        }
    }

    updateAgentStates(agents) {
        const previousAgents = { ...this.agents };
        this.agents = {};
        const agentsList = document.getElementById('agentsList');
        agentsList.innerHTML = '';

        agents.forEach(agent => {
            this.agents[agent.agent_id] = agent;

            // Check for truck movement to create animations
            if (agent.agent_type === 'truck' && previousAgents[agent.agent_id]) {
                this.updateTruckAnimation(agent, previousAgents[agent.agent_id]);
            }

            // Create enhanced agent list item with more details
            const agentElement = document.createElement('div');
            agentElement.className = `agent-item ${this.getAgentType(agent)}`;
            agentElement.innerHTML = this.createAgentListHTML(agent);

            agentsList.appendChild(agentElement);
        });
    }

    updateInventoryDisplays(agents) {
        agents.forEach(agent => {
            if (agent.state && (agent.state.inventory || agent.state.cargo)) {
                this.inventoryDisplays.set(agent.agent_id, {
                    inventory: agent.state.inventory || {},
                    cargo: agent.state.cargo || {},
                    location: agent.location_id
                });
            }
        });
    }

    updateStatusIndicators(agents) {
        agents.forEach(agent => {
            this.statusIndicators.set(agent.agent_id, {
                status: agent.state?.status || 'unknown',
                active: agent.active,
                location: agent.location_id,
                agentType: this.getAgentType(agent)
            });
        });
    }

    updateTruckAnimation(currentAgent, previousAgent) {
        // Create smooth movement animation for trucks
        if (currentAgent.state && currentAgent.state.status &&
            (currentAgent.state.status.includes('moving') || currentAgent.state.movement_progress !== undefined)) {

            const animation = {
                agentId: currentAgent.agent_id,
                fromLocation: previousAgent.location_id,
                toLocation: currentAgent.state.destination_location_id,
                progress: currentAgent.state.movement_progress || 0,
                status: currentAgent.state.status,
                cargo: currentAgent.state.cargo || {}
            };

            this.truckAnimations.set(currentAgent.agent_id, animation);
        } else {
            // Remove animation if truck is no longer moving
            this.truckAnimations.delete(currentAgent.agent_id);
        }
    }

    createAgentListHTML(agent) {
        const agentType = this.getAgentType(agent);
        const status = agent.state?.status || 'unknown';
        const isActive = agent.active ? 'active' : 'inactive';

        let details = '';

        // Add type-specific details
        if (agentType === 'store' && agent.state?.inventory) {
            const totalInventory = Object.values(agent.state.inventory).reduce((sum, qty) => sum + qty, 0);
            details = `<div class="agent-detail">Inventory: ${totalInventory}</div>`;
        } else if (agentType === 'warehouse' && agent.state?.inventory) {
            const totalInventory = Object.values(agent.state.inventory).reduce((sum, qty) => sum + qty, 0);
            details = `<div class="agent-detail">Stock: ${totalInventory}</div>`;
        } else if (agentType === 'factory' && agent.state?.production_queue) {
            const queueLength = agent.state.production_queue.length || 0;
            details = `<div class="agent-detail">Queue: ${queueLength}</div>`;
        } else if (agentType === 'truck' && agent.state) {
            const cargo = agent.state.current_cargo_weight || 0;
            const capacity = agent.state.capacity || 100;
            details = `<div class="agent-detail">Cargo: ${cargo}/${capacity}</div>`;
        }

        return `
            <div class="agent-header">
                <span class="agent-name">${agent.agent_id}</span>
                <span class="agent-status ${isActive}">${isActive}</span>
            </div>
            <div class="agent-info">
                <div class="agent-detail">Status: ${status}</div>
                ${details}
            </div>
        `;
    }

    getAgentType(agent) {
        // Extract agent type from agent_id or use provided type
        if (agent.agent_type) return agent.agent_type;

        const id = agent.agent_id.toLowerCase();
        if (id.includes('store')) return 'store';
        if (id.includes('warehouse')) return 'warehouse';
        if (id.includes('factory')) return 'factory';
        if (id.includes('truck')) return 'truck';
        if (id.includes('market')) return 'market';

        return 'unknown';
    }

    updateCityMap(mapData) {
        this.locations = mapData.locations || {};
        this.drawCityMap();
    }

    updateMetrics(metrics) {
        document.getElementById('totalRevenue').textContent =
            `$${(metrics.total_revenue || 0).toFixed(2)}`;
        document.getElementById('storageCosts').textContent =
            `$${(metrics.storage_costs || 0).toFixed(2)}`;
        document.getElementById('lostSales').textContent =
            `$${(metrics.lost_sales || 0).toFixed(2)}`;
        // Update additional metrics if elements exist
        const netProfitElement = document.getElementById('netProfit');
        if (netProfitElement) {
            netProfitElement.textContent = `$${(metrics.net_profit || 0).toFixed(2)}`;
        }

        const ordersFulfilledElement = document.getElementById('ordersFulfilled');
        if (ordersFulfilledElement) {
            ordersFulfilledElement.textContent = metrics.orders_fulfilled || 0;
        }

        const ordersLostElement = document.getElementById('ordersLost');
        if (ordersLostElement) {
            ordersLostElement.textContent = metrics.orders_lost || 0;
        }

        const fulfillmentRateElement = document.getElementById('fulfillmentRate');
        if (fulfillmentRateElement) {
            fulfillmentRateElement.textContent = `${(metrics.fulfillment_rate || 100).toFixed(1)}%`;
        }

        const efficiencyScoreElement = document.getElementById('efficiencyScore');
        if (efficiencyScoreElement) {
            efficiencyScoreElement.textContent = `${(metrics.efficiency_score || 0).toFixed(1)}/100`;
        }

        // Update summary statistics
        const simulationDurationElement = document.getElementById('simulationDuration');
        if (simulationDurationElement) {
            simulationDurationElement.textContent = `${(metrics.simulation_duration || 0).toFixed(1)}s`;
        }

        const totalEventsElement = document.getElementById('totalEvents');
        if (totalEventsElement) {
            totalEventsElement.textContent = (metrics.sales_events || 0) + (metrics.stockout_events || 0);
        }

        const stockoutEventsElement = document.getElementById('stockoutEvents');
        if (stockoutEventsElement) {
            stockoutEventsElement.textContent = metrics.stockout_events || 0;
        }

        const agentCountElement = document.getElementById('agentCount');
        if (agentCountElement) {
            agentCountElement.textContent = metrics.agent_count || 0;
        }

        // Update agent performance display
        this.updateAgentPerformance(metrics);

        // Update financial chart
        this.updateFinancialChart(metrics);

        // Apply color coding to metrics
        this.applyMetricColorCoding(metrics);
    }

    updateAgentPerformance(metrics) {
        const container = document.getElementById('agentPerformance');
        if (!container) return;

        container.innerHTML = '';

        if (metrics.agent_revenues) {
            const agentPerformances = [];

            // Calculate net profit for each agent
            Object.keys(metrics.agent_revenues).forEach(agentId => {
                const revenue = metrics.agent_revenues[agentId] || 0;
                const costs = metrics.agent_storage_costs[agentId] || 0;
                const netProfit = revenue - costs;

                agentPerformances.push({
                    agentId,
                    revenue,
                    costs,
                    netProfit
                });
            });

            // Sort by net profit descending
            agentPerformances.sort((a, b) => b.netProfit - a.netProfit);

            // Display top performing agents
            agentPerformances.slice(0, 8).forEach(agent => {
                const item = document.createElement('div');
                item.className = `agent-performance-item ${agent.netProfit >= 0 ? 'profitable' : 'loss'}`;

                const valueClass = agent.netProfit >= 0 ? 'positive' : 'negative';

                item.innerHTML = `
                    <span class="agent-performance-name">${agent.agentId}</span>
                    <span class="agent-performance-value ${valueClass}">$${agent.netProfit.toFixed(2)}</span>
                `;

                container.appendChild(item);
            });
        }

        if (container.children.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: #7f8c8d; font-style: italic;">No performance data available</div>';
        }
    }

    updateFinancialChart(metrics) {
        const canvas = document.getElementById('financialChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Simple bar chart showing revenue, costs, and profit
        const revenue = metrics.total_revenue || 0;
        const costs = metrics.storage_costs || 0;
        const lostSales = metrics.lost_sales || 0;
        const netProfit = metrics.net_profit || 0;

        const maxValue = Math.max(revenue, costs, lostSales, Math.abs(netProfit)) || 1;
        const barWidth = 45;
        const barSpacing = 60;
        const chartHeight = 80;
        const chartTop = 15;

        // Draw bars
        const bars = [
            { label: 'Revenue', value: revenue, color: '#27ae60' },
            { label: 'Costs', value: costs, color: '#e74c3c' },
            { label: 'Lost Sales', value: lostSales, color: '#f39c12' },
            { label: 'Net Profit', value: netProfit, color: netProfit >= 0 ? '#3498db' : '#e74c3c' }
        ];

        bars.forEach((bar, index) => {
            const x = 10 + index * barSpacing;
            const barHeight = Math.abs(bar.value) / maxValue * chartHeight;
            const y = bar.value >= 0 ? chartTop + chartHeight - barHeight : chartTop + chartHeight;

            // Draw bar
            ctx.fillStyle = bar.color;
            ctx.fillRect(x, y, barWidth, barHeight);

            // Draw value label
            ctx.fillStyle = '#2c3e50';
            ctx.font = 'bold 12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(`$${bar.value.toFixed(0)}`, x + barWidth / 2, y - 8);

            // Draw category label
            ctx.font = '9px Arial';
            ctx.fillStyle = '#495057';
            const shortLabel = bar.label.replace('Lost Sales', 'Lost').replace('Net Profit', 'Profit');
            ctx.fillText(shortLabel, x + barWidth / 2, chartTop + chartHeight + 12);
        });

        // Draw zero line
        ctx.strokeStyle = '#7f8c8d';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, chartTop + chartHeight);
        ctx.lineTo(canvas.width, chartTop + chartHeight);
        ctx.stroke();
    }

    applyMetricColorCoding(metrics) {
        // Color code net profit
        const netProfitElement = document.getElementById('netProfit');
        if (netProfitElement) {
            const netProfit = metrics.net_profit || 0;
            netProfitElement.className = `value ${netProfit >= 0 ? 'positive' : 'negative'}`;
        }

        // Color code fulfillment rate
        const fulfillmentElement = document.getElementById('fulfillmentRate');
        if (fulfillmentElement) {
            const fulfillmentRate = metrics.fulfillment_rate || 100;
            if (fulfillmentRate >= 95) {
                fulfillmentElement.className = 'value positive';
            } else if (fulfillmentRate >= 80) {
                fulfillmentElement.className = 'value neutral';
            } else {
                fulfillmentElement.className = 'value negative';
            }
        }

        // Color code efficiency score
        const efficiencyElement = document.getElementById('efficiencyScore');
        if (efficiencyElement) {
            const efficiencyScore = metrics.efficiency_score || 0;
            if (efficiencyScore >= 80) {
                efficiencyElement.className = 'value positive';
            } else if (efficiencyScore >= 60) {
                efficiencyElement.className = 'value neutral';
            } else {
                efficiencyElement.className = 'value negative';
            }
        }

        // Add performance indicators
        this.addPerformanceIndicators(metrics);
    }

    addPerformanceIndicators(metrics) {
        // Add performance indicator to efficiency score
        const efficiencyElement = document.getElementById('efficiencyScore');
        if (!efficiencyElement) return;

        const existingIndicator = efficiencyElement.parentNode.querySelector('.performance-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }

        const efficiencyScore = metrics.efficiency_score || 0;
        const indicator = document.createElement('span');
        indicator.className = 'performance-indicator';

        if (efficiencyScore >= 80) {
            indicator.classList.add('excellent');
        } else if (efficiencyScore >= 60) {
            indicator.classList.add('good');
        } else {
            indicator.classList.add('poor');
        }

        efficiencyElement.parentNode.appendChild(indicator);
    }

    logActivity(message, type = 'info') {
        const logContainer = document.getElementById('activityLog');
        const timestamp = new Date().toLocaleTimeString();

        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.innerHTML = `
            <span class="log-timestamp">[${timestamp}]</span>
            <span class="log-message">${message}</span>
        `;

        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;

        // Limit log entries to prevent memory issues
        while (logContainer.children.length > 100) {
            logContainer.removeChild(logContainer.firstChild);
        }
    }

    // Canvas drawing methods
    drawCityMap() {
        const ctx = this.ctx;
        const canvas = this.canvas;

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw background grid
        this.drawGrid();

        // Draw connections/routes first (background)
        this.drawRoutes();

        // Draw locations
        this.drawLocations();

        // Draw truck movement paths
        this.drawTruckPaths();

        // Draw agents (including animated trucks)
        this.drawAgents();

        // Draw inventory indicators
        this.drawInventoryIndicators();

        // Draw status indicators
        this.drawStatusIndicators();

        // Draw delivery animations
        this.drawDeliveryAnimations();
    }

    drawGrid() {
        const ctx = this.ctx;
        const canvas = this.canvas;
        const gridSize = 50;

        ctx.strokeStyle = '#ecf0f1';
        ctx.lineWidth = 1;

        // Vertical lines
        for (let x = 0; x <= canvas.width; x += gridSize) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }

        // Horizontal lines
        for (let y = 0; y <= canvas.height; y += gridSize) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }
    }

    drawLocations() {
        const ctx = this.ctx;

        Object.values(this.locations).forEach(location => {
            const x = location.x * this.mapScale + this.mapOffset.x;
            const y = location.y * this.mapScale + this.mapOffset.y;

            // Draw location shadow
            ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
            ctx.beginPath();
            ctx.arc(x + 2, y + 2, this.locationSize, 0, 2 * Math.PI);
            ctx.fill();

            // Draw location based on type
            ctx.fillStyle = this.getLocationColor(location.location_type);
            ctx.beginPath();
            ctx.arc(x, y, this.locationSize, 0, 2 * Math.PI);
            ctx.fill();

            // Draw location border
            ctx.strokeStyle = '#2c3e50';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Draw location icon
            ctx.fillStyle = 'white';
            ctx.font = 'bold 14px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            const icon = this.getLocationIcon(location.location_type);
            ctx.fillText(icon, x, y);

            // Draw location label
            ctx.fillStyle = '#2c3e50';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            ctx.fillText(location.name, x, y + this.locationSize + 5);
        });
    }

    drawAgents() {
        const ctx = this.ctx;

        Object.values(this.agents).forEach(agent => {
            const agentType = this.getAgentType(agent);

            // Handle truck agents with animation
            if (agentType === 'truck' && this.truckAnimations.has(agent.agent_id)) {
                this.drawAnimatedTruck(agent);
            } else {
                this.drawStaticAgent(agent);
            }
        });
    }

    drawStaticAgent(agent) {
        const ctx = this.ctx;
        const location = this.locations[agent.location_id];
        if (!location) return;

        const x = location.x * this.mapScale + this.mapOffset.x;
        const y = location.y * this.mapScale + this.mapOffset.y;
        const agentType = this.getAgentType(agent);

        // Calculate agent position around location
        const agentOffset = this.getAgentOffset(agent.agent_id, agentType);
        const agentX = x + agentOffset.x;
        const agentY = y + agentOffset.y;

        // Draw agent shadow
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.beginPath();
        ctx.arc(agentX + 1, agentY + 1, this.agentSize, 0, 2 * Math.PI);
        ctx.fill();

        // Draw agent body
        ctx.fillStyle = this.getAgentColor(agentType);
        ctx.beginPath();
        ctx.arc(agentX, agentY, this.agentSize, 0, 2 * Math.PI);
        ctx.fill();

        // Draw agent border
        ctx.strokeStyle = agent.active ? '#27ae60' : '#e74c3c';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Draw agent icon
        ctx.fillStyle = 'white';
        ctx.font = 'bold 10px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const icon = this.getAgentIcon(agentType);
        ctx.fillText(icon, agentX, agentY);
    }

    drawAnimatedTruck(agent) {
        const ctx = this.ctx;
        const animation = this.truckAnimations.get(agent.agent_id);
        if (!animation) return;

        const fromLocation = this.locations[animation.fromLocation];
        const toLocation = this.locations[animation.toLocation];

        if (!fromLocation || !toLocation) {
            // Fallback to static drawing
            this.drawStaticAgent(agent);
            return;
        }

        // Calculate interpolated position
        const progress = Math.max(0, Math.min(1, animation.progress));
        const fromX = fromLocation.x * this.mapScale + this.mapOffset.x;
        const fromY = fromLocation.y * this.mapScale + this.mapOffset.y;
        const toX = toLocation.x * this.mapScale + this.mapOffset.x;
        const toY = toLocation.y * this.mapScale + this.mapOffset.y;

        const currentX = fromX + (toX - fromX) * progress;
        const currentY = fromY + (toY - fromY) * progress;

        // Draw truck shadow
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.beginPath();
        ctx.arc(currentX + 2, currentY + 2, this.agentSize + 2, 0, 2 * Math.PI);
        ctx.fill();

        // Draw truck body
        ctx.fillStyle = this.getAgentColor('truck');
        ctx.beginPath();
        ctx.arc(currentX, currentY, this.agentSize + 2, 0, 2 * Math.PI);
        ctx.fill();

        // Draw truck border
        ctx.strokeStyle = '#2c3e50';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Draw truck icon
        ctx.fillStyle = 'white';
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('T', currentX, currentY);

        // Draw cargo indicator if truck has cargo
        if (animation.cargo && Object.keys(animation.cargo).length > 0) {
            ctx.fillStyle = '#f39c12';
            ctx.beginPath();
            ctx.arc(currentX + 8, currentY - 8, 4, 0, 2 * Math.PI);
            ctx.fill();
        }

        // Draw movement trail
        this.drawMovementTrail(fromX, fromY, currentX, currentY);
    }

    drawRoutes() {
        const ctx = this.ctx;

        // Draw meaningful supply chain connections only
        const locations = Object.values(this.locations);
        const factories = locations.filter(loc => loc.location_type === 'factory');
        const warehouses = locations.filter(loc => loc.location_type === 'warehouse');
        const stores = locations.filter(loc => loc.location_type === 'store');

        // Draw factory → warehouse connections
        ctx.strokeStyle = '#95a5a6';
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);

        factories.forEach(factory => {
            warehouses.forEach(warehouse => {
                this.drawConnection(factory, warehouse, '#95a5a6', 1);
            });
        });

        // Draw warehouse → store connections (more prominent)
        ctx.strokeStyle = '#7f8c8d';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 3]);

        warehouses.forEach(warehouse => {
            stores.forEach(store => {
                this.drawConnection(warehouse, store, '#7f8c8d', 1);
            });
        });

        ctx.setLineDash([]);
    }

    drawConnection(loc1, loc2, color, width) {
        const ctx = this.ctx;
        const x1 = loc1.x * this.mapScale + this.mapOffset.x;
        const y1 = loc1.y * this.mapScale + this.mapOffset.y;
        const x2 = loc2.x * this.mapScale + this.mapOffset.x;
        const y2 = loc2.y * this.mapScale + this.mapOffset.y;

        ctx.strokeStyle = color;
        ctx.lineWidth = width;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
    }

    getLocationColor(type) {
        const colors = {
            'factory': '#27ae60',
            'warehouse': '#f39c12',
            'store': '#e74c3c',
            'default': '#95a5a6'
        };
        return colors[type] || colors.default;
    }

    drawTruckPaths() {
        const ctx = this.ctx;

        this.truckAnimations.forEach((animation, truckId) => {
            const fromLocation = this.locations[animation.fromLocation];
            const toLocation = this.locations[animation.toLocation];

            if (!fromLocation || !toLocation) return;

            const fromX = fromLocation.x * this.mapScale + this.mapOffset.x;
            const fromY = fromLocation.y * this.mapScale + this.mapOffset.y;
            const toX = toLocation.x * this.mapScale + this.mapOffset.x;
            const toY = toLocation.y * this.mapScale + this.mapOffset.y;

            // Draw active delivery path - lighter and simpler
            ctx.strokeStyle = 'rgba(155, 89, 182, 0.6)'; // More transparent purple
            ctx.lineWidth = 2; // Thinner line
            ctx.setLineDash([6, 3]); // Shorter dashes
            ctx.beginPath();
            ctx.moveTo(fromX, fromY);
            ctx.lineTo(toX, toY);
            ctx.stroke();
            ctx.setLineDash([]);

            // Draw direction arrow
            this.drawDeliveryArrow(fromX, fromY, toX, toY);

            // Draw cargo indicator - smaller and simpler
            if (animation.cargo && Object.keys(animation.cargo).length > 0) {
                const midX = (fromX + toX) / 2;
                const midY = (fromY + toY) / 2;
                
                ctx.fillStyle = 'rgba(243, 156, 18, 0.8)'; // More transparent
                ctx.beginPath();
                ctx.arc(midX, midY, 4, 0, 2 * Math.PI); // Smaller circle
                ctx.fill();
                
                ctx.fillStyle = 'white';
                ctx.font = '6px Arial'; // Smaller font
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText('C', midX, midY);
            }
        });
    }

    drawDeliveryArrow(fromX, fromY, toX, toY) {
        const ctx = this.ctx;
        const angle = Math.atan2(toY - fromY, toX - fromX);
        const arrowLength = 15;
        const arrowAngle = Math.PI / 6;

        // Position arrow 80% along the path
        const arrowX = fromX + (toX - fromX) * 0.8;
        const arrowY = fromY + (toY - fromY) * 0.8;

        ctx.strokeStyle = 'rgba(155, 89, 182, 0.7)'; // Lighter arrow
        ctx.lineWidth = 2; // Thinner arrow
        ctx.beginPath();
        
        // Arrow head
        ctx.moveTo(arrowX, arrowY);
        ctx.lineTo(
            arrowX - arrowLength * Math.cos(angle - arrowAngle),
            arrowY - arrowLength * Math.sin(angle - arrowAngle)
        );
        ctx.moveTo(arrowX, arrowY);
        ctx.lineTo(
            arrowX - arrowLength * Math.cos(angle + arrowAngle),
            arrowY - arrowLength * Math.sin(angle + arrowAngle)
        );
        ctx.stroke();
    }

    drawInventoryIndicators() {
        const ctx = this.ctx;

        this.inventoryDisplays.forEach((display, agentId) => {
            const location = this.locations[display.location];
            if (!location) return;

            const x = location.x * this.mapScale + this.mapOffset.x;
            const y = location.y * this.mapScale + this.mapOffset.y;

            // Calculate total inventory
            const inventory = display.inventory || {};
            const totalInventory = Object.values(inventory).reduce((sum, qty) => sum + qty, 0);

            if (totalInventory > 0) {
                // Draw inventory indicator
                ctx.fillStyle = 'rgba(52, 152, 219, 0.8)';
                ctx.beginPath();
                ctx.arc(x + 25, y - 25, 8, 0, 2 * Math.PI);
                ctx.fill();

                // Draw inventory count
                ctx.fillStyle = 'white';
                ctx.font = 'bold 10px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(totalInventory.toString(), x + 25, y - 25);
            }
        });
    }

    drawStatusIndicators() {
        const ctx = this.ctx;

        this.statusIndicators.forEach((indicator, agentId) => {
            const location = this.locations[indicator.location];
            if (!location) return;

            const x = location.x * this.mapScale + this.mapOffset.x;
            const y = location.y * this.mapScale + this.mapOffset.y;

            // Draw status indicator based on agent type and status
            const statusColor = this.getStatusColor(indicator.status, indicator.agentType);
            if (statusColor) {
                ctx.fillStyle = statusColor;
                ctx.beginPath();
                ctx.arc(x - 25, y - 25, 6, 0, 2 * Math.PI);
                ctx.fill();

                // Add pulsing effect for active status
                if (indicator.status === 'active' || indicator.status.includes('processing')) {
                    const pulseRadius = 6 + Math.sin(Date.now() / 200) * 2;
                    ctx.strokeStyle = statusColor;
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.arc(x - 25, y - 25, pulseRadius, 0, 2 * Math.PI);
                    ctx.stroke();
                }
            }
        });
    }

    drawDeliveryAnimations() {
        const ctx = this.ctx;
        const currentTime = Date.now();

        // This would be enhanced to show delivery completion animations
        // For now, we'll show a simple effect when trucks complete deliveries
        this.truckAnimations.forEach((animation, truckId) => {
            if (animation.progress >= 0.95) { // Near completion
                const toLocation = this.locations[animation.toLocation];
                if (!toLocation) return;

                const x = toLocation.x * this.mapScale + this.mapOffset.x;
                const y = toLocation.y * this.mapScale + this.mapOffset.y;

                // Draw delivery completion effect
                const effectRadius = 30 + Math.sin(currentTime / 100) * 5;
                ctx.strokeStyle = 'rgba(39, 174, 96, 0.6)';
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.arc(x, y, effectRadius, 0, 2 * Math.PI);
                ctx.stroke();
            }
        });
    }

    drawMovementTrail(fromX, fromY, currentX, currentY) {
        const ctx = this.ctx;

        // Draw fading trail behind moving truck
        const trailLength = 20;
        const dx = currentX - fromX;
        const dy = currentY - fromY;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance > 0) {
            const unitX = dx / distance;
            const unitY = dy / distance;

            for (let i = 0; i < trailLength; i++) {
                const trailX = currentX - unitX * i * 2;
                const trailY = currentY - unitY * i * 2;
                const alpha = (trailLength - i) / trailLength * 0.3;

                ctx.fillStyle = `rgba(155, 89, 182, ${alpha})`;
                ctx.beginPath();
                ctx.arc(trailX, trailY, 2, 0, 2 * Math.PI);
                ctx.fill();
            }
        }
    }

    getAgentOffset(agentId, agentType) {
        // Calculate offset position for agents around locations to avoid overlap
        const hash = agentId.split('').reduce((a, b) => {
            a = ((a << 5) - a) + b.charCodeAt(0);
            return a & a;
        }, 0);

        const angle = (hash % 8) * (Math.PI / 4);
        const radius = 30;

        return {
            x: Math.cos(angle) * radius,
            y: Math.sin(angle) * radius
        };
    }

    getLocationIcon(type) {
        const icons = {
            'factory': '🏭',
            'warehouse': '🏢',
            'store': '🏪',
            'default': '📍'
        };
        return icons[type] || icons.default;
    }

    getAgentIcon(type) {
        const icons = {
            'store': 'S',
            'warehouse': 'W',
            'factory': 'F',
            'truck': 'T',
            'market': 'M',
            'default': 'A'
        };
        return icons[type] || icons.default;
    }

    getStatusColor(status, agentType) {
        if (!status) return null;

        const statusLower = status.toLowerCase();

        // Common status colors
        if (statusLower.includes('active') || statusLower.includes('running')) {
            return 'rgba(39, 174, 96, 0.8)'; // Green
        }
        if (statusLower.includes('processing') || statusLower.includes('producing')) {
            return 'rgba(243, 156, 18, 0.8)'; // Orange
        }
        if (statusLower.includes('moving') || statusLower.includes('loading')) {
            return 'rgba(155, 89, 182, 0.8)'; // Purple
        }
        if (statusLower.includes('waiting') || statusLower.includes('idle')) {
            return 'rgba(149, 165, 166, 0.8)'; // Gray
        }
        if (statusLower.includes('error') || statusLower.includes('failed')) {
            return 'rgba(231, 76, 60, 0.8)'; // Red
        }

        return null;
    }

    getLocationColor(type) {
        const colors = {
            'factory': '#27ae60',
            'warehouse': '#f39c12',
            'store': '#e74c3c',
            'default': '#95a5a6'
        };
        return colors[type] || colors.default;
    }

    getAgentColor(type) {
        const colors = {
            'store': '#e74c3c',
            'warehouse': '#f39c12',
            'factory': '#27ae60',
            'truck': '#9b59b6',
            'market': '#34495e',
            'default': '#95a5a6'
        };
        return colors[type] || colors.default;
    }
}

// Tab functionality for analysis section
function showTab(tabName) {
    // Hide all tab panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab panel
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // Add active class to clicked button
    event.target.classList.add('active');
}

// Initialize the simulation UI when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing SimulationUI...');
    try {
        new SimulationUI();
        console.log('SimulationUI initialized successfully');
    } catch (error) {
        console.error('Failed to initialize SimulationUI:', error);
    }
});