import threading
import random

class ArrivalGenerator(threading.Thread):
    """
    Generates visitors arriving at the park over time.
    Uses a Poisson distribution to simulate random arrival patterns.
    """
    def __init__(self, clock, park, metrics, total_visitors=100, 
                 park_hours=480, visitor_mix=None):
        super().__init__(daemon=True)
        self.clock = clock
        self.park = park
        self.metrics = metrics
        self.total_visitors = total_visitors
        self.park_hours = park_hours
        
        # Default visitor mix
        if visitor_mix is None:
            visitor_mix = {
                'Child': 0.3,
                'Tourist': 0.5,
                'AdrenalineAddict': 0.2
            }
        self.visitor_mix = visitor_mix
        
        # Pre-generate arrival schedule
        self.arrival_schedule = self._generate_arrival_schedule()
        
    def _generate_arrival_schedule(self):
        """
        Generate a Poisson arrival pattern.
        Arrivals are randomly distributed with a constant average rate.
        """
        schedule = {}
        
        # Calculate average arrival rate (lambda) per minute
        arrival_rate = self.total_visitors / self.park_hours
        
        # Generate arrivals for each minute using Poisson distribution
        visitor_id = 0
        for minute in range(self.park_hours):
            # Number of arrivals in this minute follows Poisson(lambda)
            num_arrivals = random.choices(
                range(0, 10),  # Reasonable upper bound for arrivals per minute
                weights=[self._poisson_pmf(k, arrival_rate) for k in range(10)]
            )[0]
            
            # Create visitors for this minute
            for _ in range(num_arrivals):
                if visitor_id >= self.total_visitors:
                    break
                    
                # Choose visitor type based on mix
                visitor_type = random.choices(
                    list(self.visitor_mix.keys()),
                    weights=list(self.visitor_mix.values())
                )[0]
                
                if minute not in schedule:
                    schedule[minute] = []
                schedule[minute].append((visitor_id, visitor_type))
                visitor_id += 1
            
            if visitor_id >= self.total_visitors:
                break
        
        return schedule
    
    def _poisson_pmf(self, k, lambda_rate):
        """
        Calculate Poisson probability mass function.
        P(X=k) = (lambda^k * e^(-lambda)) / k!
        """
        import math
        return (lambda_rate ** k * math.exp(-lambda_rate)) / math.factorial(k)
        
    def run(self):
        """Release visitors according to the schedule"""
        current_minute = 0
        
        while not self.clock.should_stop() and current_minute < self.park_hours:
            now = self.clock.now()
            
            # Check if we've reached the next minute
            if now >= current_minute:
                # Release any visitors scheduled for this minute
                if current_minute in self.arrival_schedule:
                    for vid, visitor_type in self.arrival_schedule[current_minute]:
                        visitor = self.park.create_visitor(visitor_type, vid)
                        visitor.start()
                        
                current_minute += 1
                
            # Small sleep to avoid busy waiting
            self.clock.sleep_minutes(0.5)