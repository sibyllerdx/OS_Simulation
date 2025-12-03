"""
Staff Management System
=======================
Adds employees to the park: ride operators, security, and janitors.
Staff affect park operations and visitor satisfaction.
"""

import threading
import random
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict

# Staff Types and Attributes

class StaffType(Enum):
    """Types of staff members"""
    RIDE_OPERATOR = "ride_operator"
    SECURITY = "security"
    JANITOR = "janitor"

class StaffSkill(Enum):
    """Skill levels for staff"""
    TRAINEE = "trainee"      # Slower, less efficient
    REGULAR = "regular"      # Normal performance
    EXPERIENCED = "experienced"  # Faster, more efficient
    EXPERT = "expert"        # Best performance


# Base Staff Class

class Staff(threading.Thread, ABC):
    """Base class for all staff members"""
    def __init__(self, staff_id, name, clock, park, skill_level=StaffSkill.REGULAR):
        super().__init__(daemon=True)
        self.staff_id = staff_id
        self.name = name
        self.clock = clock
        self.park = park
        self.skill_level = skill_level
        
        # Staff state
        self.energy = 100  # Decreases over shift
        self.on_duty = True
        self.current_task = None
        
        # Performance multipliers based on skill
        self.performance_multipliers = {
            StaffSkill.TRAINEE: 0.7,
            StaffSkill.REGULAR: 1.0,
            StaffSkill.EXPERIENCED: 1.3,
            StaffSkill.EXPERT: 1.6
        }
        
    def get_efficiency(self) -> float:
        """Calculate current efficiency (0.0 to 1.6)"""
        base = self.performance_multipliers[self.skill_level]
        # Energy affects efficiency
        energy_factor = self.energy / 100.0
        return base * energy_factor
    
    def rest(self):
        """Take a break to restore energy"""
        self.current_task = "resting"
        rest_time = random.randint(10, 20)
        self.clock.sleep_minutes(rest_time)
        self.energy = min(100, self.energy + 30)
        self.current_task = None
    
    @abstractmethod
    def work_cycle(self):
        """Main work cycle - implemented by subclasses"""
        pass
    
    def run(self):
        """Main thread loop"""
        while not self.clock.should_stop() and self.on_duty:
            # Check if needs rest
            if self.energy < 30 and random.random() < 0.7:
                self.rest()
            else:
                self.work_cycle()
            
            # Small pause between tasks
            self.clock.sleep_minutes(random.randint(1, 3))

# Ride Operator

class RideOperator(Staff):
    """
    Operates a specific ride.
    Skilled operators reduce boarding time and improve ride efficiency.
    """
    def __init__(self, staff_id, name, clock, park, assigned_ride, 
                 skill_level=StaffSkill.REGULAR):
        super().__init__(staff_id, name, clock, park, skill_level)
        self.assigned_ride = assigned_ride
        self.rides_operated = 0
        
    def work_cycle(self):
        """Monitor and optimize ride operations"""
        self.current_task = f"operating {self.assigned_ride.name}"
        
        # Check ride state
        if not self.assigned_ride.is_operational():
            # Ride is broken or in maintenance
            self.current_task = "waiting for ride repair"
            self.clock.sleep_minutes(5)
            return
        
        # Optimize boarding if there's a queue
        queue_size = self.assigned_ride.queue.size()
        if queue_size > 0:
            # Skilled operators reduce boarding window (faster loading)
            efficiency = self.get_efficiency()
            if efficiency > 1.0:
                # Could reduce board_window, but we'll just track performance
                self.rides_operated += 1
                # Track in metrics
                if hasattr(self.park, 'metrics') and self.park.metrics:
                    self.park.metrics.record_staff_action(
                        self.staff_id, self.name, "ride_operator", "operated_ride",
                        self.assigned_ride.name, self.clock.now(), efficiency
                    )
        
        # Decrease energy
        self.energy -= random.uniform(1, 3)
        
        # Monitor ride
        self.clock.sleep_minutes(random.randint(3, 7))

# Security Guard

class SecurityGuard(Staff):
    """
    Patrols the park, handles incidents, finds lost children.
    """
    def __init__(self, staff_id, name, clock, park, patrol_area,
                 skill_level=StaffSkill.REGULAR):
        super().__init__(staff_id, name, clock, park, skill_level)
        self.patrol_area = patrol_area  # e.g., "north", "south", "central"
        self.incidents_handled = 0
        self.children_found = 0
        
    def work_cycle(self):
        """Patrol and handle incidents"""
        self.current_task = f"patrolling {self.patrol_area}"
        
        # Check for lost children (random events)
        if random.random() < 0.05:  # 5% chance per cycle
            self._handle_lost_child()
        
        # Check for incidents (random events)
        if random.random() < 0.03:  # 3% chance per cycle
            self._handle_incident()
        
        # Regular patrol
        self.energy -= random.uniform(0.5, 1.5)
        self.clock.sleep_minutes(random.randint(5, 10))
    
    def _handle_lost_child(self):
        """Handle a lost child event"""
        efficiency = self.get_efficiency()
        search_time = int(15 / efficiency)  # Skilled guards find faster
        
        print(f"[SECURITY] {self.name} searching for lost child in {self.patrol_area}...")
        self.current_task = "searching for lost child"
        
        self.clock.sleep_minutes(search_time)
        
        if random.random() < 0.8 + (efficiency * 0.1):  # Higher skill = better success
            self.children_found += 1
            print(f"[SECURITY] {self.name} reunited lost child with family!")
            # Track in metrics
            if hasattr(self.park, 'metrics') and self.park.metrics:
                self.park.metrics.record_staff_action(
                    self.staff_id, self.name, "security", "found_child",
                    self.patrol_area, self.clock.now(), efficiency
                )
        else:
            print(f"[SECURITY] {self.name} escalating search...")
        
        self.energy -= 10
    
    def _handle_incident(self):
        """Handle a security incident"""
        incident_types = ["dispute", "medical", "disturbance", "safety_concern"]
        incident = random.choice(incident_types)
        
        print(f"[SECURITY] {self.name} responding to {incident} in {self.patrol_area}")
        self.current_task = f"handling {incident}"
        
        efficiency = self.get_efficiency()
        resolution_time = int(20 / efficiency)
        
        self.clock.sleep_minutes(resolution_time)
        self.incidents_handled += 1
        self.energy -= 8
        
        print(f"[SECURITY] {self.name} resolved {incident}")
        
        # Track in metrics
        if hasattr(self.park, 'metrics') and self.park.metrics:
            self.park.metrics.record_staff_action(
                self.staff_id, self.name, "security", f"incident_{incident}",
                self.patrol_area, self.clock.now(), efficiency
            )

# Janitor

class Janitor(Staff):
    """
    Cleans the park. Cleanliness affects visitor satisfaction.
    Areas get dirty over time based on visitor traffic.
    """
    def __init__(self, staff_id, name, clock, park, assigned_zone,
                 skill_level=StaffSkill.REGULAR):
        super().__init__(staff_id, name, clock, park, skill_level)
        self.assigned_zone = assigned_zone  # e.g., "rides", "food_court", "bathrooms"
        self.areas_cleaned = 0
        
    def work_cycle(self):
        """Clean assigned zone"""
        self.current_task = f"cleaning {self.assigned_zone}"
        
        # Check if zone needs cleaning
        if self.park.cleanliness_manager:
            cleanliness = self.park.cleanliness_manager.get_zone_cleanliness(
                self.assigned_zone
            )
            
            if cleanliness < 70:  # Needs cleaning
                self._clean_zone()
            else:
                # Routine maintenance
                self.current_task = f"maintaining {self.assigned_zone}"
                self.clock.sleep_minutes(random.randint(3, 6))
        else:
            # No cleanliness system, just simulate work
            self.clock.sleep_minutes(random.randint(5, 10))
        
        self.energy -= random.uniform(1, 2)
    
    def _clean_zone(self):
        """Clean the assigned zone"""
        efficiency = self.get_efficiency()
        clean_time = int(10 / efficiency)  # Skilled janitors clean faster
        
        if random.random() < 0.1:  # 10% chance of visible cleaning
            print(f"[CLEANING] {self.name} deep cleaning {self.assigned_zone}")
        
        self.clock.sleep_minutes(clean_time)
        
        # Improve cleanliness
        if self.park.cleanliness_manager:
            improvement = 20 * efficiency
            self.park.cleanliness_manager.clean_zone(self.assigned_zone, improvement)
        
        self.areas_cleaned += 1
        self.energy -= 5
        
        # Track in metrics
        if hasattr(self.park, 'metrics') and self.park.metrics:
            self.park.metrics.record_staff_action(
                self.staff_id, self.name, "janitor", "cleaned_zone",
                self.assigned_zone, self.clock.now(), efficiency
            )

# Cleanliness Manager

class CleanlinessManager:
    """
    Tracks cleanliness of different park zones.
    Visitors decrease cleanliness, janitors increase it.
    """
    def __init__(self, metrics=None):
        self._lock = threading.Lock()
        self.metrics = metrics
        
        # Zone cleanliness (0-100)
        self._zones = {
            'rides': 100,
            'food_court': 100,
            'bathrooms': 100,
            'pathways': 100,
            'entrance': 100
        }
        
        # Track visitor traffic
        self._traffic_count = defaultdict(int)
    
    def get_zone_cleanliness(self, zone: str) -> float:
        """Get cleanliness of a zone (0-100)"""
        with self._lock:
            return self._zones.get(zone, 100)
    
    def clean_zone(self, zone: str, improvement: float):
        """Increase cleanliness of a zone"""
        with self._lock:
            if zone in self._zones:
                self._zones[zone] = min(100, self._zones[zone] + improvement)
    
    def degrade_zone(self, zone: str, amount: float):
        """Decrease cleanliness (from visitor traffic)"""
        with self._lock:
            if zone in self._zones:
                self._zones[zone] = max(0, self._zones[zone] - amount)
                self._traffic_count[zone] += 1
    
    def periodic_degradation(self, clock):
        """Background thread that degrades cleanliness over time"""
        while not clock.should_stop():
            with self._lock:
                for zone in self._zones:
                    # Degrade based on traffic
                    traffic = self._traffic_count.get(zone, 0)
                    degradation = min(5, traffic * 0.1)
                    self._zones[zone] = max(0, self._zones[zone] - degradation)
                    
                    # Log cleanliness to metrics
                    if self.metrics:
                        self.metrics.record_cleanliness(
                            zone, self._zones[zone], clock.now()
                        )
                    
                # Reset traffic count
                self._traffic_count.clear()
            
            clock.sleep_minutes(10)  # Check every 10 minutes
    
    def get_average_cleanliness(self) -> float:
        """Get park-wide average cleanliness"""
        with self._lock:
            return sum(self._zones.values()) / len(self._zones)
    
    def get_summary(self) -> dict:
        """Get cleanliness summary"""
        with self._lock:
            return {
                'zones': dict(self._zones),
                'average': self.get_average_cleanliness()
            }

# Staff Manager

class StaffManager:
    """
    Manages all park staff members.
    Tracks performance and coordinates staff activities.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._staff = []
        self._staff_by_type = defaultdict(list)
        
    def add_staff(self, staff: Staff):
        """Add a staff member"""
        with self._lock:
            self._staff.append(staff)
            # Determine type
            if isinstance(staff, RideOperator):
                self._staff_by_type[StaffType.RIDE_OPERATOR].append(staff)
            elif isinstance(staff, SecurityGuard):
                self._staff_by_type[StaffType.SECURITY].append(staff)
            elif isinstance(staff, Janitor):
                self._staff_by_type[StaffType.JANITOR].append(staff)
    
    def start_all_staff(self):
        """Start all staff threads"""
        with self._lock:
            for staff in self._staff:
                staff.start()
    
    def get_staff_count(self, staff_type: StaffType = None) -> int:
        """Get count of staff by type"""
        with self._lock:
            if staff_type is None:
                return len(self._staff)
            return len(self._staff_by_type[staff_type])
    
    def get_statistics(self) -> dict:
        """Get staff performance statistics"""
        with self._lock:
            stats = {
                'total_staff': len(self._staff),
                'by_type': {},
                'performance': {}
            }
            
            for staff_type, staff_list in self._staff_by_type.items():
                stats['by_type'][staff_type.value] = len(staff_list)
            
            # Ride operators
            operators = self._staff_by_type[StaffType.RIDE_OPERATOR]
            if operators:
                total_rides = sum(op.rides_operated for op in operators)
                stats['performance']['total_rides_operated'] = total_rides
                stats['performance']['avg_rides_per_operator'] = total_rides / len(operators)
            
            # Security
            guards = self._staff_by_type[StaffType.SECURITY]
            if guards:
                stats['performance']['incidents_handled'] = sum(g.incidents_handled for g in guards)
                stats['performance']['children_found'] = sum(g.children_found for g in guards)
            
            # Janitors
            janitors = self._staff_by_type[StaffType.JANITOR]
            if janitors:
                stats['performance']['areas_cleaned'] = sum(j.areas_cleaned for j in janitors)
            
            return stats