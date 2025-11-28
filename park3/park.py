import threading
from .visitor import ChildCreator, TouristCreator, AdrenalineAddictCreator

class Park:
    """
    Central coordinator for the amusement park.
    Manages all rides, food facilities, and visitors.
    """
    def __init__(self, clock, metrics=None):
        self.clock = clock
        self.metrics = metrics
        
        # Resources
        self._rides = []
        self._food_facilities = []
        self._visitors = []
        self._merch_stands = []
        self._bathrooms = []
        self._bathrooms_lock = threading.Lock()

        # Thread-safe locks
        self._rides_lock = threading.Lock()
        self._food_lock = threading.Lock()
        self._visitors_lock = threading.Lock()
        self._merch_lock = threading.Lock()
        
        # Visitor factories
        self._creators = {
            'Child': ChildCreator(),
            'Tourist': TouristCreator(),
            'AdrenalineAddict': AdrenalineAddictCreator()
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
        visitor = creator.register_visitor(vid, self, self.clock, self.metrics)
        
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
        with self._bathrooms_lock:
            for bathroom in self._bathrooms:
                bathroom.start()

    def add_bathroom(self, bathroom):
        """Register a new bathroom in the park."""
        with self._bathrooms_lock:
            self._bathrooms.append(bathroom)

    def get_bathrooms(self):
        """Return a copy of the bathroom list."""
        with self._bathrooms_lock:
            return list(self._bathrooms)

    def join_bathroom_queue(self, visitor, bathroom):
        """Put a visitor into the queue of a specific bathroom."""
        bathroom.queue.enqueue(visitor)  
    
    def add_merch_stand(self, stand):
        with self._merch_lock:
            self._merch_stands.append(stand)

    def get_merch_stands(self):
        with self._merch_lock:
            return self._merch_stands.copy()

    def join_merch_queue(self, visitor, stand):
        stand.queue.add_person(visitor)

    def start_all_merch_stands(self):
        with self._merch_lock:
            for stand in self._merch_stands:
                stand.start()

                
    def close_all(self):
        """Close all facilities"""
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