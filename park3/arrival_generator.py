import threading
import random

class ArrivalGenerator(threading.Thread):
    """
    Generates visitors arriving at the park over time.
    Uses a Poisson distribution to simulate random arrival patterns.
    Now supports group arrivals for families and friends.
    """
    def __init__(self, clock, park, metrics, total_visitors=100, 
                 park_hours=480, visitor_mix=None, initial_groups=None):
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
        
        # Group information (optional)
        self.initial_groups = initial_groups if initial_groups is not None else []
        
        # Track visitor IDs
        self.next_group_vid = 0
        self.next_solo_vid = 1000  # Solo visitors start at higher IDs
        
        # Pre-generate arrival schedule
        self.arrival_schedule = self._generate_arrival_schedule()
        
    def _generate_arrival_schedule(self):
        """
        Generate arrival schedule including both groups and solo visitors.
        Groups arrive together (or within a few minutes of each other).
        """
        schedule = {}
        
        # First, schedule group arrivals
        total_group_members = 0
        for group_info in self.initial_groups:
            # Groups arrive in the first half of park hours (earlier arrival)
            arrival_minute = random.randint(0, self.park_hours // 2)
            
            # Determine visitor type for group (families are mixed, friends are similar)
            if group_info['type'].value == 'family':
                # Families have mixed ages
                group_types = []
                for _ in range(group_info['size']):
                    group_types.append(random.choices(
                        list(self.visitor_mix.keys()),
                        weights=list(self.visitor_mix.values())
                    )[0])
            else:
                # Friends tend to be same type
                base_type = random.choices(
                    list(self.visitor_mix.keys()),
                    weights=list(self.visitor_mix.values())
                )[0]
                group_types = [base_type] * group_info['size']
            
            # Schedule each group member
            for i in range(group_info['size']):
                visitor_id = self.next_group_vid
                self.next_group_vid += 1
                group_info['member_ids'].append(visitor_id)
                
                # Stagger arrivals slightly (within 0-2 minutes)
                minute = arrival_minute + random.randint(0, 2)
                
                if minute not in schedule:
                    schedule[minute] = []
                
                schedule[minute].append((visitor_id, group_types[i], True))  # True = part of group
                total_group_members += 1
        
        # Then, schedule solo visitors using Poisson distribution
        remaining_visitors = self.total_visitors - total_group_members
        if remaining_visitors > 0:
            arrival_rate = remaining_visitors / self.park_hours
            
            visitor_id = self.next_solo_vid
            for minute in range(self.park_hours):
                # Number of arrivals in this minute follows Poisson(lambda)
                num_arrivals = random.choices(
                    range(0, 10),
                    weights=[self._poisson_pmf(k, arrival_rate) for k in range(10)]
                )[0]
                
                for _ in range(num_arrivals):
                    if visitor_id >= self.next_solo_vid + remaining_visitors:
                        break
                    
                    # Choose visitor type
                    visitor_type = random.choices(
                        list(self.visitor_mix.keys()),
                        weights=list(self.visitor_mix.values())
                    )[0]
                    
                    if minute not in schedule:
                        schedule[minute] = []
                    schedule[minute].append((visitor_id, visitor_type, False))  # False = solo
                    visitor_id += 1
                
                if visitor_id >= self.next_solo_vid + remaining_visitors:
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
                    for vid, visitor_type, is_group_member in self.arrival_schedule[current_minute]:
                        visitor = self.park.create_visitor(visitor_type, vid)
                        visitor.start()
                        
                current_minute += 1
                
            # Small sleep to avoid busy waiting
            self.clock.sleep_minutes(0.5)