import threading
import random

class FoodTruck(threading.Thread):
    """
    A food service facility that serves visitors one at a time.
    Runs as its own thread, processing its queue continuously.
    """
    def __init__(self, name, queue, clock, metrics=None):
        super().__init__(daemon=True)
        self.name = name
        self.queue = queue
        self.clock = clock
        self.metrics = metrics
        self._open = True
        self._revenue = 0
        self._lock = threading.Lock()
        
        # Menu with prices
        self.menu = {
            'hot_dog': 5,
            'burger': 8,
            'fries': 4,
            'pizza_slice': 6,
            'nachos': 7,
            'ice_cream': 4,
            'soda': 3,
            'water': 2
        }
        
    def run(self):
        """Main service loop - serves visitors from queue"""
        while not self.clock.should_stop() and self._open:
            visitor = self.queue.dequeue_one()
            
            if visitor is None:
                # No customers, wait a bit
                self.clock.sleep_minutes(1)
                continue
                
            # Serve the visitor
            self._serve_visitor(visitor)
            
    def _serve_visitor(self, visitor):
        """Process one visitor's order with affordability logic"""

        # Build list of items they can afford
        affordable_items = [
            (item, price) for item, price in self.menu.items()
            if visitor.money >= price
        ]

        vid = visitor.vid

        # If nothing is affordable → fail purchase
        if not affordable_items:
            print(f"[{self.name}] Visitor {vid} cannot afford ANY food items.")
            visitor.on_food_failed(self.name, self.clock.now())
            return

        # Pick randomly from affordable items
        item, price = random.choice(affordable_items)

        # Simulate service time (1–3 minutes)
        service_time = random.randint(1, 3)
        self.clock.sleep_minutes(service_time)

        # Deduct money
        visitor.money -= price

        # Update revenue
        with self._lock:
            self._revenue += price

        # Record metrics
        if self.metrics:
            self.metrics.record_food_purchase(
                visitor.vid,
                self.name,
                self.clock.now(),
                price
            )

        print(
            f"[{self.name}] Visitor {visitor.vid} buys {item} for ${price} "
            f"(Remaining money: ${visitor.money})"
        )

        # Notify visitor they were served
        visitor.on_food_served(self.name, self.clock.now())
        
    def get_revenue(self):
        """Get total revenue for this food truck"""
        with self._lock:
            return self._revenue
            
    def close(self):
        """Close the food truck"""
        self._open = False