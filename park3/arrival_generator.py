import threading
import random

class ArrivalGenerator(threading.Thread):
    """
    Generates visitors arriving at the park over time.
    Uses a bell curve to simulate realistic arrival patterns.
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
        Generate a bell-curve arrival pattern.
        Most visitors arrive in the middle of the day.
        """
        schedule = {}
        
        # Generate arrival minute for each visitor
        for vid in range(self.total_visitors):
            # Bell curve centered at middle of day
            mean = self.park_hours / 2
            std_dev = self.park_hours / 6
            
            # Generate arrival time (bounded to park hours)
            arrival_minute = int(random.gauss(mean, std_dev))
            arrival_minute = max(0, min(self.park_hours - 60, arrival_minute))
            
            # Choose visitor type based on mix
            visitor_type = random.choices(
                list(self.visitor_mix.keys()),
                weights=list(self.visitor_mix.values())
            )[0]
            
            if arrival_minute not in schedule:
                schedule[arrival_minute] = []
            schedule[arrival_minute].append((vid, visitor_type))
            
        return schedule
        
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