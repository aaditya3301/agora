"""Performance tracking system for the supply chain simulator."""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import time


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    total_revenue: float = 0.0
    total_storage_costs: float = 0.0
    total_lost_sales: float = 0.0
    total_orders_fulfilled: int = 0
    total_orders_lost: int = 0
    simulation_start_time: float = field(default_factory=time.time)
    simulation_end_time: Optional[float] = None
    
    @property
    def net_profit(self) -> float:
        """Calculate net profit (revenue - costs)."""
        return self.total_revenue - self.total_storage_costs
    
    @property
    def fulfillment_rate(self) -> float:
        """Calculate order fulfillment rate as percentage."""
        total_orders = self.total_orders_fulfilled + self.total_orders_lost
        if total_orders == 0:
            return 100.0
        return (self.total_orders_fulfilled / total_orders) * 100.0
    
    @property
    def efficiency_score(self) -> float:
        """Calculate overall efficiency score (0-100)."""
        if self.total_revenue == 0:
            return 0.0
        
        # Efficiency based on profit margin and fulfillment rate
        profit_margin = (self.net_profit / self.total_revenue) * 100
        fulfillment_weight = 0.6
        profit_weight = 0.4
        
        # Normalize profit margin to 0-100 scale (assuming reasonable margins are 0-50%)
        normalized_profit = min(max(profit_margin, 0), 50) * 2
        
        return (fulfillment_weight * self.fulfillment_rate + 
                profit_weight * normalized_profit)


class PerformanceTracker:
    """Tracks and calculates performance metrics for the supply chain simulation."""
    
    def __init__(self):
        """Initialize the performance tracker."""
        self.metrics = PerformanceMetrics()
        self.agent_revenues: Dict[str, float] = {}
        self.agent_storage_costs: Dict[str, float] = {}
        self.stockout_events: List[Dict] = []
        self.sales_events: List[Dict] = []
    
    def record_sale(self, agent_id: str, product_id: str, quantity: int, 
                   unit_price: float, timestamp: float = None) -> None:
        """
        Record a successful sale.
        
        Args:
            agent_id: ID of the agent making the sale
            product_id: ID of the product sold
            quantity: Number of units sold
            unit_price: Price per unit
            timestamp: When the sale occurred (defaults to current time)
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if unit_price < 0:
            raise ValueError("Unit price cannot be negative")
        
        revenue = quantity * unit_price
        self.metrics.total_revenue += revenue
        self.metrics.total_orders_fulfilled += 1
        
        # Track per-agent revenue
        if agent_id not in self.agent_revenues:
            self.agent_revenues[agent_id] = 0.0
        self.agent_revenues[agent_id] += revenue
        
        # Record sale event
        sale_event = {
            'timestamp': timestamp if timestamp is not None else time.time(),
            'agent_id': agent_id,
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'revenue': revenue
        }
        self.sales_events.append(sale_event)
    
    def record_storage_cost(self, agent_id: str, product_id: str, quantity: int,
                           storage_cost_per_unit: float, timestamp: float = None) -> None:
        """
        Record storage costs incurred.
        
        Args:
            agent_id: ID of the agent incurring storage costs
            product_id: ID of the product being stored
            quantity: Number of units in storage
            storage_cost_per_unit: Storage cost per unit per time step
            timestamp: When the cost was incurred (defaults to current time)
        """
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if storage_cost_per_unit < 0:
            raise ValueError("Storage cost cannot be negative")
        
        cost = quantity * storage_cost_per_unit
        self.metrics.total_storage_costs += cost
        
        # Track per-agent storage costs
        if agent_id not in self.agent_storage_costs:
            self.agent_storage_costs[agent_id] = 0.0
        self.agent_storage_costs[agent_id] += cost
    
    def record_stockout(self, agent_id: str, product_id: str, requested_quantity: int,
                       lost_revenue: float, timestamp: float = None) -> None:
        """
        Record a stockout event (lost sale).
        
        Args:
            agent_id: ID of the agent experiencing stockout
            product_id: ID of the product that was out of stock
            requested_quantity: Number of units that couldn't be fulfilled
            lost_revenue: Revenue lost due to stockout
            timestamp: When the stockout occurred (defaults to current time)
        """
        if requested_quantity <= 0:
            raise ValueError("Requested quantity must be positive")
        if lost_revenue < 0:
            raise ValueError("Lost revenue cannot be negative")
        
        self.metrics.total_lost_sales += lost_revenue
        self.metrics.total_orders_lost += 1
        
        # Record stockout event
        stockout_event = {
            'timestamp': timestamp if timestamp is not None else time.time(),
            'agent_id': agent_id,
            'product_id': product_id,
            'requested_quantity': requested_quantity,
            'lost_revenue': lost_revenue
        }
        self.stockout_events.append(stockout_event)
    
    def get_agent_performance(self, agent_id: str) -> Dict:
        """
        Get performance metrics for a specific agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dictionary containing agent-specific metrics
        """
        return {
            'agent_id': agent_id,
            'total_revenue': self.agent_revenues.get(agent_id, 0.0),
            'total_storage_costs': self.agent_storage_costs.get(agent_id, 0.0),
            'net_profit': (self.agent_revenues.get(agent_id, 0.0) - 
                          self.agent_storage_costs.get(agent_id, 0.0)),
            'sales_count': len([e for e in self.sales_events if e['agent_id'] == agent_id]),
            'stockout_count': len([e for e in self.stockout_events if e['agent_id'] == agent_id])
        }
    
    def get_overall_metrics(self) -> PerformanceMetrics:
        """Get overall performance metrics."""
        return self.metrics
    
    def end_simulation(self) -> PerformanceMetrics:
        """
        Mark the simulation as ended and return final metrics.
        
        Returns:
            Final performance metrics
        """
        self.metrics.simulation_end_time = time.time()
        return self.metrics
    
    def reset(self) -> None:
        """Reset all metrics and start fresh."""
        self.metrics = PerformanceMetrics()
        self.agent_revenues.clear()
        self.agent_storage_costs.clear()
        self.stockout_events.clear()
        self.sales_events.clear()
    
    def get_current_metrics(self) -> Dict:
        """
        Get current performance metrics as a dictionary for real-time display.
        
        Returns:
            Dictionary containing current metrics
        """
        metrics = self.metrics
        current_time = time.time()
        duration = current_time - metrics.simulation_start_time
        
        return {
            'total_revenue': metrics.total_revenue,
            'storage_costs': metrics.total_storage_costs,
            'lost_sales': metrics.total_lost_sales,
            'net_profit': metrics.net_profit,
            'orders_fulfilled': metrics.total_orders_fulfilled,
            'orders_lost': metrics.total_orders_lost,
            'fulfillment_rate': metrics.fulfillment_rate,
            'efficiency_score': metrics.efficiency_score,
            'simulation_duration': duration,
            'agent_count': len(self.agent_revenues),
            'stockout_events': len(self.stockout_events),
            'sales_events': len(self.sales_events),
            'agent_revenues': dict(self.agent_revenues),
            'agent_storage_costs': dict(self.agent_storage_costs)
        }
    
    def get_summary_report(self) -> str:
        """
        Generate a human-readable summary report.
        
        Returns:
            Formatted string with performance summary
        """
        metrics = self.metrics
        duration = (metrics.simulation_end_time or time.time()) - metrics.simulation_start_time
        
        report = f"""
=== Supply Chain Performance Report ===
Simulation Duration: {duration:.1f} seconds

Financial Metrics:
  Total Revenue: ${metrics.total_revenue:.2f}
  Storage Costs: ${metrics.total_storage_costs:.2f}
  Lost Sales: ${metrics.total_lost_sales:.2f}
  Net Profit: ${metrics.net_profit:.2f}

Operational Metrics:
  Orders Fulfilled: {metrics.total_orders_fulfilled}
  Orders Lost: {metrics.total_orders_lost}
  Fulfillment Rate: {metrics.fulfillment_rate:.1f}%
  Efficiency Score: {metrics.efficiency_score:.1f}/100

Agent Count: {len(self.agent_revenues)} agents with revenue
Stockout Events: {len(self.stockout_events)}
Sales Events: {len(self.sales_events)}
"""
        return report.strip()