import threading
import random
from park3.simple_social_visitor import SocialChildCreator, SocialTouristCreator, SocialAdrenalineAddictCreator

class Park:
    """
    Central coordinator for the amusement park.
    Manages all rides, food facilities, visitors, staff, and social systems.
    """
    def __init__(self, clock, metrics=None):
        self.clock = clock
        self.metrics = metrics
        
        # Social systems (optional - can be None)
        self.location_tracker = None
        self.group_manager = None
        self.group_coordinator = None
        
        # Staff systems (optional - can be None)
        self.cleanliness_manager = None
        self.staff_manager = None
        
        # Resources
        self._rides = []
        self._food_facilities = []
        self._visitors = []
        self._merch_stands = []
        self._bathrooms = []

        # Thread-safe locks
        self._rides_lock = threading.Lock()
        self._food_lock = threading.Lock()
        self._visitors_lock = threading.Lock()
        self._merch_lock = threading.Lock()
        self._bathrooms_lock = threading.Lock()
        
        # Always use social visitors (they work for solo visitors too)
        self._creators = {
            'Child': SocialChildCreator(),
            'Tourist': SocialTouristCreator(),
            'AdrenalineAddict': SocialAdrenalineAddictCreator()
        }
        
    def add_ride(self, ride):
        """Add a ride to the park"""
        with self._rides_lock:
            self._rides.append(ride)
            
    def add_food_facility(self, facility):
        """Add a food facility to the park"""
        with self._food_lock:
            self._food_facilities.append(facility)
            
    def get_rides(self):
        """Get list of all rides"""
        with self._rides_lock:
            return self._rides.copy()
            
    def get_food_facilities(self):
        """Get list of all food facilities"""
        with self._food_lock:
            return self._food_facilities.copy()
            
    def create_visitor(self, visitor_type, vid):
        """Create a visitor using the factory pattern"""
        if visitor_type not in self._creators:
            raise ValueError(f"Unknown visitor type: {visitor_type}")
            
        creator = self._creators[visitor_type]
        
        # Pass all systems (they can be None, visitors will handle it)
        visitor = creator.register_visitor(
            vid, self, self.clock, self.metrics,
            location_tracker=self.location_tracker,
            group_manager=self.group_manager,
            group_coordinator=self.group_coordinator
        )
        
        with self._visitors_lock:
            self._visitors.append(visitor)
            
        return visitor
        
    def join_ride_queue(self, visitor, ride):
        """Add a visitor to a ride's queue"""
        ride.queue.enqueue(visitor, priority=visitor.has_fastpass)
        
    def join_food_queue(self, visitor, facility):
        """Add a visitor to a food facility's queue"""
        facility.queue.add_person(visitor)
        
    def start_all_rides(self):
        """Start all ride threads"""
        with self._rides_lock:
            for ride in self._rides:
                ride.start()
                
    def start_all_food_facilities(self):
        """Start all food facility threads"""
        with self._food_lock:
            for facility in self._food_facilities:
                facility.start()

    def start_all_bathrooms(self):
        """Start all bathroom threads"""
        with self._bathrooms_lock:
            for bathroom in self._bathrooms:
                bathroom.start()

    def add_bathroom(self, bathroom):
        """Register a new bathroom in the park"""
        with self._bathrooms_lock:
            self._bathrooms.append(bathroom)

    def get_bathrooms(self):
        """Return a copy of the bathroom list"""
        with self._bathrooms_lock:
            return list(self._bathrooms)

    def join_bathroom_queue(self, visitor, bathroom):
        """Put a visitor into the queue of a specific bathroom"""
        bathroom.queue.enqueue(visitor)  
    
    def add_merch_stand(self, stand):
        """Add a merchandise stand to the park"""
        with self._merch_lock:
            self._merch_stands.append(stand)

    def get_merch_stands(self):
        """Get list of all merch stands"""
        with self._merch_lock:
            return self._merch_stands.copy()

    def join_merch_queue(self, visitor, stand):
        """Add a visitor to a merch stand queue"""
        stand.queue.add_person(visitor)

    def start_all_merch_stands(self):
        """Start all merch stand threads"""
        with self._merch_lock:
            for stand in self._merch_stands:
                stand.start()

    def start_cleanliness_degradation(self):
        """Start background cleanliness degradation thread"""
        if self.cleanliness_manager:
            degradation_thread = threading.Thread(
                target=self.cleanliness_manager.periodic_degradation,
                args=(self.clock,),
                daemon=True
            )
            degradation_thread.start()
    
    def start_maintenance_scheduler(self):
        """Start periodic maintenance scheduler for rides"""
        def maintenance_worker():
            """Schedule periodic maintenance for rides"""
            while not self.clock.should_stop():
                # Wait for some time before scheduling maintenance
                self.clock.sleep_minutes(random.randint(60, 120))
                
                with self._rides_lock:
                    # Pick a random ride for maintenance
                    if self._rides:
                        ride = random.choice(self._rides)
                        # Only schedule if ride is operational
                        if ride.is_operational():
                            maintenance_duration = random.randint(15, 30)
                            print(f"[SCHEDULER] Scheduling {maintenance_duration}min maintenance for {ride.name}")
                            ride.schedule_maintenance(maintenance_duration)
        
        maintenance_thread = threading.Thread(
            target=maintenance_worker,
            daemon=True
        )
        maintenance_thread.start()
                
    def close_all(self):
        """Close all facilities and stop all threads"""
        with self._rides_lock:
            for ride in self._rides:
                ride.close()
                
        with self._food_lock:
            for facility in self._food_facilities:
                facility.close()
        
        with self._bathrooms_lock:
            for bathroom in self._bathrooms:
                bathroom.close()

        with self._merch_lock:
            for stand in self._merch_stands:
                stand.close()
                
    def get_total_visitors(self):
        """Get total number of visitors created"""
        with self._visitors_lock:
            return len(self._visitors)