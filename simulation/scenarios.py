"""
End-to-end simulation scenarios for testing complete supply chain flows.
Provides different demand patterns and scenario configurations.
"""
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import random

from simulation.simulation_manager import SimulationManager
from simulation.agent_integration import AgentIntegration
from simulation.city_map import CityMap
from simulation.performance_tracker import PerformanceTracker
from agents.message_bus import MessageBus

logger = logging.getLogger(__name__)


class DemandPattern(Enum):
    """Different demand pattern types for scenarios."""
    STEADY = "steady"
    INCREASING = "increasing"
    DECREASING = "decreasing"
    SPIKE = "spike"
    SEASONAL = "seasonal"
    RANDOM = "random"


@dataclass
class ScenarioConfig:
    """Configuration for a simulation scenario."""
    name: str
    description: str
    duration_steps: int
    demand_pattern: DemandPattern
    demand_intensity: float = 1.0  # Multiplier for base demand
    event_probability: float = 0.1  # Probability of special events
    initial_inventory_multiplier: float = 1.0  # Multiplier for initial inventory
    expected_outcomes: Dict[str, Any] = None  # Expected results for validation
    
    def __post_init__(self):
        if self.expected_outcomes is None:
            self.expected_outcomes = {}


class ScenarioRunner:
    """Runs end-to-end simulation scenarios and collects results."""
    
    def __init__(self):
        """Initialize the scenario runner."""
        self.results_history: List[Dict[str, Any]] = []
        self.current_scenario: Optional[ScenarioConfig] = None
        
    def setup_scenario(self, config: ScenarioConfig) -> Dict[str, Any]:
        """
        Set up a simulation scenario with the given configuration.
        
        Args:
            config: Scenario configuration
            
        Returns:
            Dictionary with simulation components
        """
        self.current_scenario = config
        
        # Create simulation components
        city_map = CityMap()
        message_bus = MessageBus()
        performance_tracker = PerformanceTracker()
        sim_manager = SimulationManager(city_map, message_bus, time_step_duration=0.5)
        agent_integration = AgentIntegration(sim_manager, city_map, message_bus)
        
        # Create sample city
        city_map.create_sample_city()
        
        # Set up agents with scenario-specific configurations
        self._setup_agents_for_scenario(agent_integration, config)
        
        logger.info(f"Scenario '{config.name}' setup complete")
        
        return {
            'sim_manager': sim_manager,
            'agent_integration': agent_integration,
            'city_map': city_map,
            'message_bus': message_bus,
            'performance_tracker': performance_tracker,
            'config': config
        }
    
    def _setup_agents_for_scenario(self, agent_integration: AgentIntegration, config: ScenarioConfig):
        """Set up agents with scenario-specific parameters."""
        # Adjust initial inventory based on scenario
        inventory_multiplier = config.initial_inventory_multiplier
        
        # Create factories with adjusted inventory
        factory_inventory = {
            "product_1": int(30 * inventory_multiplier),
            "product_2": int(25 * inventory_multiplier)
        }
        
        # Create warehouses with adjusted inventory
        warehouse_inventory = {
            "product_1": int(50 * inventory_multiplier),
            "product_2": int(40 * inventory_multiplier)
        }
        
        # Create stores with adjusted inventory
        store_inventory = {
            "product_1": int(25 * inventory_multiplier),
            "product_2": int(20 * inventory_multiplier)
        }
        
        # Set up default supply chain with adjusted parameters
        created_agents = agent_integration.setup_default_supply_chain()
        
        # Adjust agent parameters based on scenario
        for store_id in created_agents['stores']:
            store_agent = agent_integration.store_agents[store_id]
            # Adjust reorder thresholds based on demand intensity
            store_agent.reorder_threshold = max(5, int(10 * config.demand_intensity))
            store_agent.reorder_quantity = max(25, int(50 * config.demand_intensity))
        
        # Configure market agent with scenario-specific demand pattern
        if created_agents['markets']:
            market_agent = agent_integration.market_agents[created_agents['markets'][0]]
            market_agent.base_demand_rate = config.demand_intensity
            market_agent.event_probability = config.event_probability
            
            # Set demand pattern-specific behavior
            self._configure_market_for_pattern(market_agent, config.demand_pattern)
    
    def _configure_market_for_pattern(self, market_agent, pattern: DemandPattern):
        """Configure market agent for specific demand pattern."""
        if pattern == DemandPattern.STEADY:
            market_agent.demand_variation = 0.1  # Low variation
        elif pattern == DemandPattern.INCREASING:
            market_agent.demand_variation = 0.3
            # Market agent will need custom logic for increasing trend
        elif pattern == DemandPattern.DECREASING:
            market_agent.demand_variation = 0.3
            # Market agent will need custom logic for decreasing trend
        elif pattern == DemandPattern.SPIKE:
            market_agent.demand_variation = 0.5
            market_agent.event_probability = 0.3  # Higher chance of events
        elif pattern == DemandPattern.SEASONAL:
            market_agent.demand_variation = 0.4
        elif pattern == DemandPattern.RANDOM:
            market_agent.demand_variation = 0.8  # High variation
    
    def run_scenario(self, scenario_components: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a complete scenario simulation.
        
        Args:
            scenario_components: Components from setup_scenario
            
        Returns:
            Dictionary with scenario results
        """
        sim_manager = scenario_components['sim_manager']
        performance_tracker = scenario_components['performance_tracker']
        config = scenario_components['config']
        
        logger.info(f"Starting scenario '{config.name}' for {config.duration_steps} steps")
        
        # Record initial state
        initial_state = self._capture_simulation_state(scenario_components)
        
        # Run simulation
        sim_manager.start_simulation()
        
        # Collect metrics during simulation
        step_metrics = []
        for step in range(config.duration_steps):
            if not sim_manager.step():
                logger.warning(f"Simulation stopped early at step {step}")
                break
            
            # Collect metrics every 10 steps
            if step % 10 == 0:
                metrics = self._collect_step_metrics(scenario_components, step)
                step_metrics.append(metrics)
        
        # Stop simulation and collect final results
        sim_manager.stop_simulation()
        final_metrics = performance_tracker.end_simulation()
        final_state = self._capture_simulation_state(scenario_components)
        
        # Compile results
        results = {
            'scenario_name': config.name,
            'config': config,
            'initial_state': initial_state,
            'final_state': final_state,
            'final_metrics': final_metrics,
            'step_metrics': step_metrics,
            'success': self._evaluate_scenario_success(config, final_metrics),
            'summary': performance_tracker.get_summary_report()
        }
        
        # Store results
        self.results_history.append(results)
        
        logger.info(f"Scenario '{config.name}' completed. Success: {results['success']}")
        return results
    
    def _capture_simulation_state(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Capture current simulation state for analysis."""
        sim_manager = components['sim_manager']
        agent_integration = components['agent_integration']
        
        # Get agent states
        agent_states = {}
        for agent_type in ['stores', 'warehouses', 'factories', 'trucks', 'markets']:
            agents = agent_integration.get_agents_by_type(agent_type.rstrip('s'))
            agent_states[agent_type] = [agent.get_agent_info() for agent in agents]
        
        return {
            'simulation_state': sim_manager.get_simulation_state(),
            'agent_states': agent_states,
            'integration_stats': agent_integration.get_integration_stats()
        }
    
    def _collect_step_metrics(self, components: Dict[str, Any], step: int) -> Dict[str, Any]:
        """Collect metrics at a specific simulation step."""
        sim_manager = components['sim_manager']
        performance_tracker = components['performance_tracker']
        
        return {
            'step': step,
            'simulation_time': sim_manager.simulation_time,
            'active_agents': sum(1 for agent in sim_manager.agents if agent.is_active()),
            'current_metrics': performance_tracker.get_overall_metrics(),
            'message_bus_stats': components['message_bus'].get_stats()
        }
    
    def _evaluate_scenario_success(self, config: ScenarioConfig, final_metrics) -> bool:
        """Evaluate if scenario met success criteria."""
        expected = config.expected_outcomes
        
        # Default success criteria if none specified
        if not expected:
            # Basic success: simulation completed without major failures
            return (final_metrics.total_orders_fulfilled > 0 and 
                   final_metrics.fulfillment_rate > 50.0)
        
        # Check specific expected outcomes
        success = True
        
        if 'min_revenue' in expected:
            success &= final_metrics.total_revenue >= expected['min_revenue']
        
        if 'min_fulfillment_rate' in expected:
            success &= final_metrics.fulfillment_rate >= expected['min_fulfillment_rate']
        
        if 'max_lost_sales' in expected:
            success &= final_metrics.total_lost_sales <= expected['max_lost_sales']
        
        if 'min_efficiency' in expected:
            success &= final_metrics.efficiency_score >= expected['min_efficiency']
        
        return success
    
    def get_scenario_results(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """Get results for a specific scenario."""
        for result in self.results_history:
            if result['scenario_name'] == scenario_name:
                return result
        return None
    
    def compare_scenarios(self, scenario_names: List[str]) -> Dict[str, Any]:
        """Compare results across multiple scenarios."""
        scenarios = []
        for name in scenario_names:
            result = self.get_scenario_results(name)
            if result:
                scenarios.append(result)
        
        if not scenarios:
            return {'error': 'No scenarios found for comparison'}
        
        # Extract key metrics for comparison
        comparison = {
            'scenarios': [],
            'summary': {
                'total_scenarios': len(scenarios),
                'successful_scenarios': sum(1 for s in scenarios if s['success']),
                'avg_revenue': 0,
                'avg_fulfillment_rate': 0,
                'avg_efficiency': 0
            }
        }
        
        total_revenue = 0
        total_fulfillment = 0
        total_efficiency = 0
        
        for scenario in scenarios:
            metrics = scenario['final_metrics']
            scenario_summary = {
                'name': scenario['scenario_name'],
                'success': scenario['success'],
                'revenue': metrics.total_revenue,
                'fulfillment_rate': metrics.fulfillment_rate,
                'efficiency_score': metrics.efficiency_score,
                'net_profit': metrics.net_profit
            }
            comparison['scenarios'].append(scenario_summary)
            
            total_revenue += metrics.total_revenue
            total_fulfillment += metrics.fulfillment_rate
            total_efficiency += metrics.efficiency_score
        
        # Calculate averages
        count = len(scenarios)
        comparison['summary']['avg_revenue'] = total_revenue / count
        comparison['summary']['avg_fulfillment_rate'] = total_fulfillment / count
        comparison['summary']['avg_efficiency'] = total_efficiency / count
        
        return comparison


def create_standard_scenarios() -> List[ScenarioConfig]:
    """Create a set of standard test scenarios."""
    scenarios = [
        ScenarioConfig(
            name="steady_demand",
            description="Steady demand pattern with normal operations",
            duration_steps=100,
            demand_pattern=DemandPattern.STEADY,
            demand_intensity=1.0,
            expected_outcomes={
                'min_revenue': 100.0,
                'min_fulfillment_rate': 80.0,
                'min_efficiency': 60.0
            }
        ),
        
        ScenarioConfig(
            name="high_demand_spike",
            description="Sudden spike in demand to test supply chain resilience",
            duration_steps=80,
            demand_pattern=DemandPattern.SPIKE,
            demand_intensity=2.0,
            event_probability=0.3,
            expected_outcomes={
                'min_revenue': 150.0,
                'min_fulfillment_rate': 60.0,  # Lower due to spike
                'max_lost_sales': 100.0
            }
        ),
        
        ScenarioConfig(
            name="low_inventory_stress",
            description="Test supply chain with low initial inventory",
            duration_steps=120,
            demand_pattern=DemandPattern.STEADY,
            demand_intensity=1.2,
            initial_inventory_multiplier=0.3,
            expected_outcomes={
                'min_fulfillment_rate': 50.0,  # Lower due to inventory constraints
                'min_efficiency': 40.0
            }
        ),
        
        ScenarioConfig(
            name="random_demand_chaos",
            description="Highly variable random demand pattern",
            duration_steps=150,
            demand_pattern=DemandPattern.RANDOM,
            demand_intensity=1.5,
            event_probability=0.2,
            expected_outcomes={
                'min_revenue': 80.0,
                'min_fulfillment_rate': 55.0,
                'min_efficiency': 45.0
            }
        ),
        
        ScenarioConfig(
            name="long_term_operation",
            description="Extended operation to test system stability",
            duration_steps=300,
            demand_pattern=DemandPattern.SEASONAL,
            demand_intensity=1.0,
            expected_outcomes={
                'min_revenue': 300.0,
                'min_fulfillment_rate': 75.0,
                'min_efficiency': 65.0
            }
        )
    ]
    
    return scenarios