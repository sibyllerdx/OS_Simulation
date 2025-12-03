"""
Simplified Social Visitor - Groups Only
========================================
Visitors that belong to pre-formed groups and coordinate with each other.
They interact with the park's rides, food facilities, merch stands, and bathrooms,
"""

import threading
import random
from abc import ABC, abstractmethod
from park3.strategies import RideChoiceStrategy, PreferenceStrategy, RandomStrategy
from park3.simple_social import Location

class SocialVisitor(threading.Thread, ABC):
    """
    Visitor that can be part of a group.
    Groups coordinate activities and try to stay together.
    """
    def __init__(self, vid, park, clock, metrics=None, 
                 location_tracker=None, group_manager=None,
                 group_coordinator=None):
        super().__init__(daemon=True)
        self.vid = vid
        self.park = park
        self.clock = clock
        self.metrics = metrics
        
        # Social systems
        self.location_tracker = location_tracker
        self.group_manager = group_manager
        self.group_coordinator = group_coordinator
        
        # Standard attributes
        self.last_bathroom_time = 0
        self.bathroom_interval = 180
        self.height_cm = 160
        self.money = random.randint(20, 200)
        self.ride_strategy: RideChoiceStrategy = PreferenceStrategy()
        
        # State
        self.hunger = random.randint(0, 3)
        self.energy = random.randint(7, 10)
        self.merch_probability = 0.1
        self.has_fastpass = random.choice([True, False])
        
        # Group state
        self.waiting_for_group = False
        
        # Preferences (set by subclasses)
        self.ride_prefs = {}
        self.profile = {}
        
    def run(self):
        """Main visitor behavior loop"""
        # Update location to entrance
        if self.location_tracker:
            self.location_tracker.update_location(self.vid, Location.ENTRANCE, "MainGate")
        
        # Record arrival
        if self.metrics:
            self.metrics.record_arrival(self.vid, self.clock.now(),
                                       self.profile.get('kind', 'Unknown'))
        
        # Main loop
        while not self.clock.should_stop() and self.energy > 0:
            now = self.clock.now()
            
            # Increase hunger, decrease energy
            self.hunger += random.uniform(0.3, 0.8)
            self.energy -= random.uniform(0.2, 0.5)
            
            # Check if should wait for group
            if self.group_coordinator and self.group_coordinator.should_wait_for_group(self.vid):
                self._wait_for_group()
                continue
            
            # Make decision (subclass implements)
            self.step(now)
            
            # Wait before next decision
            self.clock.sleep_minutes(random.randint(2, 5))
        
        # Record exit
        if self.metrics:
            self.metrics.record_exit(self.vid, self.clock.now())
        
        # Cleanup
        if self.location_tracker:
            self.location_tracker.remove_visitor(self.vid)
        if self.group_manager:
            self.group_manager.remove_visitor(self.vid)
    
    def _wait_for_group(self):
        """Wait for group members"""
        if self.group_manager and self.group_manager.is_in_group(self.vid):
            group = self.group_manager.get_visitor_group(self.vid)
            print(f"[GROUP] Visitor {self.vid} (Group {group.group_id} leader) waiting for members...")
        
        if self.location_tracker:
            self.location_tracker.update_location(self.vid, Location.WANDERING, "waiting")
        
        self.clock.sleep_minutes(random.randint(3, 8))
    
    @abstractmethod
    def step(self, now):
        """Decision logic"""
        pass
    
    def _choose_ride(self):
        """Choose a ride, possibly following group leader"""
        if self.group_coordinator:
            # Get all available rides
            available_rides = [r.name for r in self.park.get_rides() if r.is_operational()]
            
            # Check if should follow leader
            preferred = self.group_coordinator.get_group_activity_preference(
                self.vid, available_rides
            )
            
            if preferred:
                # Find this ride
                for ride in self.park.get_rides():
                    if ride.name == preferred and ride.is_operational():
                        group = self.group_manager.get_visitor_group(self.vid)
                        print(f"[GROUP] Visitor {self.vid} following group {group.group_id} leader to {preferred}")
                        return ride
        
        # Default: use strategy
        return self.ride_strategy.pick_ride(self, self.park)
    
    def go_to_ride(self):
        """Join a ride queue"""
        ride = self._choose_ride()
        if ride:
            if self.park.cleanliness_manager:
                self.park.cleanliness_manager.degrade_zone('rides', 0.5)
            if self.location_tracker:
                self.location_tracker.update_location(self.vid, Location.RIDE, ride.name)
            
            # Track group activity
            if self.group_manager and self.group_manager.is_in_group(self.vid):
                group = self.group_manager.get_visitor_group(self.vid)
                if group and self.park.metrics:
                    self.park.metrics.record_group_activity(
                        group.group_id, 'ride', ride.name, 
                        self.clock.now(), group.size()
                    )
            
            self.park.join_ride_queue(self, ride)
            
            while ride.queue.check_person_in(self):
                self.clock.sleep_minutes(1)
    
    def go_to_bathroom(self):
        """Join bathroom queue"""
        bathrooms = self.park.get_bathrooms()
        if not bathrooms:
            return
        
        bathroom = random.choice(bathrooms)
        if self.park.cleanliness_manager:
            self.park.cleanliness_manager.degrade_zone('bathrooms', 1.0)
        
        if self.location_tracker:
            self.location_tracker.update_location(self.vid, Location.BATHROOM, bathroom.name)
        
        self.park.join_bathroom_queue(self, bathroom)
        
        while bathroom.queue.check_person_in(self):
            self.clock.sleep_minutes(1)
        
        self.last_bathroom_time = self.clock.now()
    
    def go_to_food(self):
        """Join food queue"""
        facility = random.choice(self.park.get_food_facilities())
        if self.park.cleanliness_manager:
            self.park.cleanliness_manager.degrade_zone('food_court', 0.8)
        
        if self.location_tracker:
            self.location_tracker.update_location(self.vid, Location.FOOD, facility.name)
        
        # Track group activity
        if self.group_manager and self.group_manager.is_in_group(self.vid):
            group = self.group_manager.get_visitor_group(self.vid)
            if group and self.park.metrics:
                self.park.metrics.record_group_activity(
                    group.group_id, 'food', facility.name,
                    self.clock.now(), group.size()
                )
        
        self.park.join_food_queue(self, facility)
        
        while facility.queue.check_person_in(self):
            self.clock.sleep_minutes(1)
    
    def go_to_merch(self):
        """Join merch queue"""
        stands = self.park.get_merch_stands()
        if not stands:
            return
        
        stand = random.choice(stands)
        
        if self.location_tracker:
            self.location_tracker.update_location(self.vid, Location.MERCH, stand.name)
        
        # Track group activity
        if self.group_manager and self.group_manager.is_in_group(self.vid):
            group = self.group_manager.get_visitor_group(self.vid)
            if group and self.park.metrics:
                self.park.metrics.record_group_activity(
                    group.group_id, 'merch', stand.name,
                    self.clock.now(), group.size()
                )
        
        self.park.join_merch_queue(self, stand)
        
        while stand.queue.check_person_in(self):
            self.clock.sleep_minutes(1)
    
    def on_ride_finished(self, ride_name, minute):
        """Called when ride finishes"""
        self.hunger += random.uniform(0.5, 1.5)
        self.energy -= random.uniform(0.5, 1.0)
    
    def on_food_failed(self, stand_name, minute):
        """Called when food purchase fails"""
        pass
    
    def on_food_served(self, facility_name, minute):
        """Called when food is served"""
        self.hunger = max(0, self.hunger - random.uniform(4, 6))
        self.energy = min(10, self.energy + random.uniform(1, 2))


# Concrete Visitor Types

class SocialChild(SocialVisitor):
    def __init__(self, vid, park, clock, metrics=None,
                 location_tracker=None, group_manager=None, group_coordinator=None):
        super().__init__(vid, park, clock, metrics, location_tracker, group_manager, group_coordinator)
        self.profile = {'kind': 'Child'}
        self.merch_probability = 0.1
        self.height_cm = random.randint(100, 140)
        self.money = random.randint(10, 50)
        self.ride_prefs = {
            'SpinningTeacups': 5, 'BumperCars': 4,
            'FerrisWheel': 3, 'CarouselHorses': 4
        }
        self.ride_strategy = RandomStrategy()
        self.bathroom_interval = 90
    
    def step(self, now):
        if now - self.last_bathroom_time >= self.bathroom_interval:
            self.go_to_bathroom()
        elif self.hunger > 5 and random.random() < 0.5:
            self.go_to_food()
        elif self.money >= 5 and random.random() < self.merch_probability:
            self.go_to_merch()
        else:
            self.go_to_ride()


class SocialTourist(SocialVisitor):
    def __init__(self, vid, park, clock, metrics=None,
                 location_tracker=None, group_manager=None, group_coordinator=None):
        super().__init__(vid, park, clock, metrics, location_tracker, group_manager, group_coordinator)
        self.profile = {'kind': 'Tourist'}
        self.bathroom_interval = 180
        self.merch_probability = 0.3
        self.height_cm = random.randint(150, 190)
        self.money = random.randint(100, 200)
        self.ride_prefs = {
            'FerrisWheel': 5, 'HauntedHouse': 3,
            'RollerCoaster': 3, 'SplashMountain': 4
        }
    
    def step(self, now):
        if now - self.last_bathroom_time >= self.bathroom_interval:
            self.go_to_bathroom()
        elif self.hunger > 7 and random.random() < 0.4:
            self.go_to_food()
        elif self.money >= 5 and random.random() < self.merch_probability:
            self.go_to_merch()
        else:
            self.go_to_ride()


class SocialAdrenalineAddict(SocialVisitor):
    def __init__(self, vid, park, clock, metrics=None,
                 location_tracker=None, group_manager=None, group_coordinator=None):
        super().__init__(vid, park, clock, metrics, location_tracker, group_manager, group_coordinator)
        self.profile = {'kind': 'AdrenalineAddict'}
        self.bathroom_interval = 240
        self.merch_probability = 0.025
        self.height_cm = random.randint(140, 200)
        self.money = random.randint(10, 100)
        self.ride_prefs = {
            'RollerCoaster': 5, 'DropTower': 5,
            'SpaceSimulator': 4, 'SplashMountain': 3
        }
    
    def step(self, now):
        if now - self.last_bathroom_time >= self.bathroom_interval:
            self.go_to_bathroom()
        elif self.hunger > 8 and random.random() < 0.1:
            self.go_to_food()
        elif self.money >= 5 and random.random() < self.merch_probability:
            self.go_to_merch()
        else:
            self.go_to_ride()


# Factories

class SocialVisitorCreator(ABC):
    @abstractmethod
    def factory_method(self, vid, park, clock, metrics,
                      location_tracker, group_manager, group_coordinator):
        pass
        
    def register_visitor(self, vid, park, clock, metrics, **kwargs):
        location_tracker = kwargs.get('location_tracker')
        group_manager = kwargs.get('group_manager')
        group_coordinator = kwargs.get('group_coordinator')
        
        visitor = self.factory_method(vid, park, clock, metrics,
                                     location_tracker, group_manager, group_coordinator)
        
        # Print group info
        group_info = ""
        if group_manager:
            group = group_manager.get_visitor_group(vid)
            if group and group.size() > 1:
                role = "leader" if group.is_leader(vid) else "member"
                group_info = f" [Group {group.group_id}-{group.group_type.value}, {role}]"
        
        print(f"Visitor {vid} ({visitor.profile['kind']}){group_info} entering park...")
        return visitor


class SocialChildCreator(SocialVisitorCreator):
    def factory_method(self, vid, park, clock, metrics,
                      location_tracker, group_manager, group_coordinator):
        return SocialChild(vid, park, clock, metrics,
                          location_tracker, group_manager, group_coordinator)


class SocialTouristCreator(SocialVisitorCreator):
    def factory_method(self, vid, park, clock, metrics,
                      location_tracker, group_manager, group_coordinator):
        return SocialTourist(vid, park, clock, metrics,
                            location_tracker, group_manager, group_coordinator)


class SocialAdrenalineAddictCreator(SocialVisitorCreator):
    def factory_method(self, vid, park, clock, metrics,
                      location_tracker, group_manager, group_coordinator):
        return SocialAdrenalineAddict(vid, park, clock, metrics,
                                     location_tracker, group_manager, group_coordinator)