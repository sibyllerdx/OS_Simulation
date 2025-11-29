import threading
import random
from abc import ABC, abstractmethod
from park3.strategies import RideChoiceStrategy, PreferenceStrategy, RandomStrategy

class Visitor(threading.Thread, ABC):
    """
    Base class for all visitor types.
    Each visitor is an autonomous agent running in its own thread.
    """
    def __init__(self, vid, park, clock, metrics=None):
        super().__init__(daemon=True)
        self.vid = vid
        self.park = park
        self.clock = clock
        self.metrics = metrics
        self.last_bathroom_time = 0
        self.bathroom_interval = 180 
        self.height_cm = 160  
        self.money = random.randint(20, 200) 
        self.ride_strategy: RideChoiceStrategy = PreferenceStrategy()
        
        # State variables
        self.hunger = random.randint(0, 3)
        self.energy = random.randint(7, 10)
        self.merch_probability = 0.1
        self.has_fastpass = random.choice([True, False])
        
        # Preferences (to be set by subclasses)
        self.ride_prefs = {}
        self.profile = {}
        
    def run(self):
        """Main visitor behavior loop"""
        # Record arrival
        if self.metrics:
            self.metrics.record_arrival(self.vid, self.clock.now(), 
                                       self.profile.get('kind', 'Unknown'))
        
        # Main decision loop
        while not self.clock.should_stop() and self.energy > 0:
            now = self.clock.now()
            
            # Increase hunger and decrease energy over time
            self.hunger += random.uniform(0.3, 0.8)
            self.energy -= random.uniform(0.2, 0.5)
            
            # Make decision (implemented by subclass)
            self.step(now)
            
            # Wait before next decision
            self.clock.sleep_minutes(random.randint(2, 5))
        
        # Record exit
        if self.metrics:
            self.metrics.record_exit(self.vid, self.clock.now())
            
    @abstractmethod
    def step(self, now):
        """Decision logic - implemented by each visitor type"""
        pass
        
    def _choose_ride(self):
        """Choose a ride using the configured strategy."""
        return self.ride_strategy.pick_ride(self, self.park)
        
    def go_to_ride(self):
        """Join a ride queue"""
        ride = self._choose_ride()
        if ride:
            self.park.join_ride_queue(self, ride)
            # Wait until ride is finished
            while ride.queue.check_person_in(self):
                self.clock.sleep_minutes(1)

    def go_to_bathroom(self):
        bathrooms = self.park.get_bathrooms()
        if not bathrooms:
            return

        bathroom = random.choice(bathrooms)
        self.park.join_bathroom_queue(self, bathroom)

        # Wait until done
        while bathroom.queue.check_person_in(self):
            self.clock.sleep_minutes(1)

        # When done, update timestamp
        self.last_bathroom_time = self.clock.now()
        if self.metrics is not None:
            self.metrics.record_bathroom_visit(
                visitor_id=self.vid,
                bathroom_name=bathroom.name,
                minute=self.clock.now()
            )
                    
    def go_to_food(self):
        """Join a food truck queue"""
        facility = random.choice(self.park.get_food_facilities())
        self.park.join_food_queue(self, facility)
        # Wait until served
        while facility.queue.check_person_in(self):
            self.clock.sleep_minutes(1)

    def go_to_merch(self):
        stands = self.park.get_merch_stands()
        if not stands:
            return

        stand = random.choice(stands)
        self.park.join_merch_queue(self, stand)

        # Wait until we are no longer in this stand's queue
        while stand.queue.check_person_in(self):
            self.clock.sleep_minutes(1)
            
    def on_ride_finished(self, ride_name, minute):
        """Called when a ride cycle completes"""
        self.hunger += random.uniform(0.5, 1.5)
        self.energy -= random.uniform(0.5, 1.0)

    def on_food_failed(self, stand_name, minute):
        """
        Called when a food purchase attempt fails because the visitor has no money.
        Simply lets the visitor continue with their day.
        """
        pass
        
    def on_food_served(self, facility_name, minute):
        """Called when food is served"""
        self.hunger = max(0, self.hunger - random.uniform(4, 6))
        self.energy = min(10, self.energy + random.uniform(1, 2))


class Child(Visitor):
    """
    Child visitor - prefers gentle rides, gets hungry quickly
    """
    def __init__(self, vid, park, clock, metrics=None):
        super().__init__(vid, park, clock, metrics)
        self.profile = {'kind': 'Child'}
        self.merch_probability = 0.1
        self.height_cm = random.randint(100, 140)
        self.money = random.randint(10, 50) 
        self.ride_prefs = {
            'SpinningTeacups': 5,
            'BumperCars': 4,
            'FerrisWheel': 3,
            'CarouselHorses': 4
        }
        self.ride_strategy = RandomStrategy()
        self.bathroom_interval = 90 
        
    def step(self, now):
        """Children prioritize eating when hungry"""
        if now - self.last_bathroom_time >= self.bathroom_interval:
            self.go_to_bathroom()  # bathroom takes priority this cycle
            return
        if self.hunger > 5 and random.random() < 0.5:
            self.go_to_food()

        if self.money >= 5 and random.random() < self.merch_probability:
            self.go_to_merch()
            return
        
        else:
            self.go_to_ride()


class Tourist(Visitor):
    """
    Tourist visitor - balanced preferences, moderate behavior
    """
    def __init__(self, vid, park, clock, metrics=None):
        super().__init__(vid, park, clock, metrics)
        self.profile = {'kind': 'Tourist'}
        self.bathroom_interval = 180
        self.merch_probability = 0.3
        self.height_cm = random.randint(150, 190)
        self.money = random.randint(100, 200) 
        self.ride_prefs = {
            'FerrisWheel': 5,
            'HauntedHouse': 3,
            'RollerCoaster': 3,
            'SplashMountain': 4
        }
        
    def step(self, now):
        """Tourists are more balanced"""
        if now - self.last_bathroom_time >= self.bathroom_interval:
            self.go_to_bathroom()
            return
        if self.hunger > 7 and random.random() < 0.4:
            self.go_to_food()

        if self.money >= 5 and random.random() < self.merch_probability:
            self.go_to_merch()
            return
        else:
            self.go_to_ride()


class AdrenalineAddict(Visitor):
    """
    Adrenaline addict - loves thrill rides, avoids eating
    """
    def __init__(self, vid, park, clock, metrics=None):
        super().__init__(vid, park, clock, metrics)
        self.profile = {'kind': 'AdrenalineAddict'}
        self.bathroom_interval = 240 
        self.merch_probability = 0.025
        self.height_cm = random.randint(140, 200)
        self.money = random.randint(10, 100) 
        self.ride_prefs = {
            'RollerCoaster': 5,
            'DropTower': 5,
            'SpaceSimulator': 4,
            'SplashMountain': 3
        }
        
    def step(self, now):
        """Adrenaline addicts only eat when desperate"""
        if now - self.last_bathroom_time >= self.bathroom_interval:
            self.go_to_bathroom()

            return  # bathroom takes priority this cycle
        if self.hunger > 8 and random.random() < 0.1:
            self.go_to_food()

        if self.money >= 5 and random.random() < self.merch_probability:
            self.go_to_merch()
            return
        else:
            self.go_to_ride()


# Factory pattern for visitor creation
class VisitorCreator(ABC):
    """Abstract factory for creating visitors"""
    
    @abstractmethod
    def factory_method(self, vid, park, clock, metrics):
        """Create a visitor instance"""
        pass
        
    def register_visitor(self, vid, park, clock, metrics, **kwargs):
        """
        Create and register a visitor.
        **kwargs allows for optional social system parameters (ignored by base visitors)
        """
        # Base visitors ignore social parameters
        visitor = self.factory_method(vid, park, clock, metrics)
        print(f"Visitor {vid} ({visitor.profile['kind']}) entering park...")
        return visitor


class ChildCreator(VisitorCreator):
    def factory_method(self, vid, park, clock, metrics):
        return Child(vid, park, clock, metrics)


class TouristCreator(VisitorCreator):
    def factory_method(self, vid, park, clock, metrics):
        return Tourist(vid, park, clock, metrics)


class AdrenalineAddictCreator(VisitorCreator):
    def factory_method(self, vid, park, clock, metrics):
        return AdrenalineAddict(vid, park, clock, metrics)