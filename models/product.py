"""Product data model for the supply chain simulator."""


class Product:
    """Represents a product in the supply chain."""
    
    def __init__(self, product_id: str, name: str, unit_cost: float, storage_cost: float):
        """
        Initialize a Product.
        
        Args:
            product_id: Unique identifier for the product
            name: Human-readable name of the product
            unit_cost: Cost per unit of the product
            storage_cost: Cost to store one unit per time step
        """
        if not product_id:
            raise ValueError("Product ID cannot be empty")
        if not name:
            raise ValueError("Product name cannot be empty")
        if unit_cost < 0:
            raise ValueError("Unit cost cannot be negative")
        if storage_cost < 0:
            raise ValueError("Storage cost cannot be negative")
        
        self.product_id = product_id
        self.name = name
        self.unit_cost = unit_cost
        self.storage_cost = storage_cost
    
    def __str__(self) -> str:
        return f"{self.name} (${self.unit_cost}/unit, ${self.storage_cost}/storage)"
    
    def __repr__(self) -> str:
        return f"Product('{self.product_id}', '{self.name}', {self.unit_cost}, {self.storage_cost})"