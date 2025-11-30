"""
Amusement Park Simulation with Social Interactions
==================================================
A multi-threaded simulation featuring:
- 3 visitor types: Children, Tourists, Adrenaline Addicts
- Social groups (families, friends, couples)
- Location tracking and social behavior
"""

import time
import random
from park3.clock import Clock
from park3.metrics import Metrics
from park3.bathroom import Toilet
from park3.queue import Queue
from park3.merch import MerchStand
from park3.ride import Ride
from park3.food import FoodTruck
from park3.park import Park
from park3.arrival_generator import ArrivalGenerator
from park_ui import ParkUI

# Social systems
from park3.simple_social import LocationTracker, GroupManager, GroupCoordinator, GroupType

# Staff systems
from park3.staff import (
    StaffManager, CleanlinessManager,
    RideOperator, SecurityGuard, Janitor,
    StaffSkill, StaffType
)

def create_initial_groups(num_groups=30):
    """Create initial social groups"""
    groups_created = []
    
    for i in range(num_groups):
        group_size = random.choices(
            [2, 3, 4, 5, 6],
            weights=[0.35, 0.30, 0.20, 0.10, 0.05]
        )[0]
        
        if group_size == 2:
            group_type = random.choice([GroupType.COUPLE, GroupType.FRIENDS])
        elif group_size <= 4:
            group_type = random.choices(
                [GroupType.FAMILY, GroupType.FRIENDS],
                weights=[0.6, 0.4]
            )[0]
        else:
            group_type = GroupType.FAMILY
        
        groups_created.append({
            'size': group_size,
            'type': group_type,
            'member_ids': []
        })
    
    return groups_created

def create_rides(clock, metrics):
    rides_config = [
        ('RollerCoaster', 24, 5, 0.03, 15, 3, 140),
        ('DropTower', 16, 4, 0.04, 12, 2, 145),
        ('FerrisWheel', 32, 8, 0.01, 10, 4, 0),
        ('HauntedHouse', 20, 6, 0.02, 8, 3, 140),
        ('SpinningTeacups', 16, 4, 0.02, 6, 2, 100),
        ('BumperCars', 20, 5, 0.03, 7, 3, 110),
        ('SplashMountain', 28, 7, 0.03, 14, 4, 120),
        ('SpaceSimulator', 12, 6, 0.05, 20, 2, 120),
        ('CarouselHorses', 24, 5, 0.01, 5, 3, 0),
    ]
    
    rides = []
    for name, capacity, duration, break_prob, repair_time, board_window, min_height in rides_config:
        queue = Queue()
        ride = Ride(name, queue, clock, capacity, duration, 
                   break_prob, repair_time, board_window, metrics, min_height_cm=min_height)
        rides.append(ride)
    return rides

def create_food_trucks(clock, metrics, num_trucks):
    trucks = []
    for i in range(num_trucks):
        queue = Queue()
        truck = FoodTruck(f"FoodTruck-{i+1}", queue, clock, metrics)
        trucks.append(truck)
    return trucks

def create_merch_stands(clock, metrics, num_stands):
    stands = []
    for i in range(num_stands):
        q = Queue()
        stand = MerchStand(f"MerchStand-{i+1}", q, clock, metrics)
        stands.append(stand)
    return stands

def create_bathrooms(clock, metrics, num_bathrooms):
    bathrooms = []
    for i in range(num_bathrooms):
        q = Queue()
        bathroom = Toilet(f"Bathroom-{i+1}", q, clock, metrics)
        bathrooms.append(bathroom)
    return bathrooms

def create_staff(clock, park, rides):
    """Create all staff members"""
    staff_manager = StaffManager()
    
    # Ride operators (1 per ride)
    for i, ride in enumerate(rides):
        skill = random.choices(
            [StaffSkill.TRAINEE, StaffSkill.REGULAR, StaffSkill.EXPERIENCED, StaffSkill.EXPERT],
            weights=[0.15, 0.55, 0.25, 0.05]
        )[0]
        
        operator = RideOperator(
            staff_id=i,
            name=f"Op-{ride.name[:4]}",
            clock=clock,
            park=park,
            assigned_ride=ride,
            skill_level=skill
        )
        staff_manager.add_staff(operator)
    
    # Security guards (5 zones)
    patrol_zones = ["north", "south", "east", "west", "central"]
    for i, zone in enumerate(patrol_zones):
        skill = random.choice([StaffSkill.REGULAR, StaffSkill.EXPERIENCED])
        guard = SecurityGuard(
            staff_id=100 + i,
            name=f"Sec-{zone[:3].upper()}",
            clock=clock,
            park=park,
            patrol_area=zone,
            skill_level=skill
        )
        staff_manager.add_staff(guard)
    
    # Janitors (5 zones)
    cleaning_zones = ["rides", "food_court", "bathrooms", "pathways", "entrance"]
    for i, zone in enumerate(cleaning_zones):
        skill = random.choice([StaffSkill.REGULAR, StaffSkill.EXPERIENCED])
        janitor = Janitor(
            staff_id=200 + i,
            name=f"Jan-{zone[:3].upper()}",
            clock=clock,
            park=park,
            assigned_zone=zone,
            skill_level=skill
        )
        staff_manager.add_staff(janitor)
    
    return staff_manager

if __name__ == "__main__":
    print("\n" + "="*60)
    print("AMUSEMENT PARK SIMULATION")
    print("With Social Groups and Staff Management")
    print("="*60)
    
    # Parameters
    TOTAL_VISITORS = 300
    PARK_HOURS = 480
    SPEED_FACTOR = 0.05
    NUM_FOOD_TRUCKS = 5
    NUM_MERCH_STANDS = 3
    NUM_BATHROOMS = 5
    NUM_INITIAL_GROUPS = 30
    
    VISITOR_MIX = {
        'Child': 0.3,
        'Tourist': 0.5,
        'AdrenalineAddict': 0.2
    }
    
    print(f"\nConfiguration:")
    print(f"  Total Visitors: {TOTAL_VISITORS}")
    print(f"  Park Hours: {PARK_HOURS} minutes")
    print(f"  Initial Groups: {NUM_INITIAL_GROUPS}")
    
    # Initialize systems
    clock = Clock(speed_factor=SPEED_FACTOR)
    metrics = Metrics(db_path="park_metrics.sqlite")
    
    # Social systems
    print("\nInitializing social systems...")
    location_tracker = LocationTracker()
    group_manager = GroupManager()
    group_coordinator = GroupCoordinator(group_manager, location_tracker)
    
    # Staff systems
    print("Initializing staff systems...")
    cleanliness_manager = CleanlinessManager()
    
    # Create park
    park = Park(clock, metrics)
    park.location_tracker = location_tracker
    park.group_manager = group_manager
    park.group_coordinator = group_coordinator
    park.cleanliness_manager = cleanliness_manager
    
    # Create facilities
    print("\nSetting up facilities...")
    rides = create_rides(clock, metrics)
    for ride in rides:
        park.add_ride(ride)
    
    food_trucks = create_food_trucks(clock, metrics, NUM_FOOD_TRUCKS)
    for truck in food_trucks:
        park.add_food_facility(truck)
    
    merch_stands = create_merch_stands(clock, metrics, NUM_MERCH_STANDS)
    for stand in merch_stands:
        park.add_merch_stand(stand)
    
    bathrooms = create_bathrooms(clock, metrics, NUM_BATHROOMS)
    for bathroom in bathrooms:
        park.add_bathroom(bathroom)
    
    print(f"  ✓ {len(rides)} rides, {NUM_FOOD_TRUCKS} food trucks")
    
    # Create staff
    print("\nHiring staff...")
    staff_manager = create_staff(clock, park, rides)
    park.staff_manager = staff_manager
    print(f"  ✓ {staff_manager.get_staff_count()} staff members hired")
    print(f"    - {staff_manager.get_staff_count(StaffType.RIDE_OPERATOR)} ride operators")
    print(f"    - {staff_manager.get_staff_count(StaffType.SECURITY)} security guards")
    print(f"    - {staff_manager.get_staff_count(StaffType.JANITOR)} janitors")
    
    # Create groups
    print("\nCreating social groups...")
    initial_groups = create_initial_groups(NUM_INITIAL_GROUPS)
    total_group_members = sum(g['size'] for g in initial_groups)
    print(f"  ✓ {len(initial_groups)} groups ({total_group_members} visitors)")
    
    # Create arrival generator
    arrival_gen = ArrivalGenerator(
        clock, park, metrics, 
        total_visitors=TOTAL_VISITORS,
        park_hours=PARK_HOURS,
        visitor_mix=VISITOR_MIX,
        initial_groups=initial_groups
    )
    
    # Register groups
    for group_info in initial_groups:
        if group_info['member_ids']:
            group_manager.create_group(
                group_info['type'],
                group_info['member_ids']
            )
    
    # Create UI
    ui = ParkUI(park, clock, metrics, rides, food_trucks, merch_stands, bathrooms)
    
    # Start simulation
    print("\n" + "="*60)
    print("STARTING SIMULATION")
    print("="*60 + "\n")
    
    clock.start()
    
    # Start all systems
    park.start_all_rides()
    park.start_all_food_facilities()
    park.start_all_bathrooms()
    park.start_all_merch_stands()
    staff_manager.start_all_staff()
    park.start_cleanliness_degradation()
    arrival_gen.start()
    
    # Run
    try:
        sim_duration = PARK_HOURS * SPEED_FACTOR
        print(f"Simulation running for ~{sim_duration:.1f} seconds...")
        print("Close matplotlib window to stop.\n")
        
        ui.start()
            
    except KeyboardInterrupt:
        print("\n\nInterrupted!")
        
    finally:
        print("\n" + "="*60)
        print("ENDING SIMULATION")
        print("="*60)
        
        ui.stop()
        clock.stop()
        time.sleep(1)
        park.close_all()
        
        # Print all summaries
        metrics.print_summary()
        
        # Social stats
        print("\n" + "="*50)
        print("SOCIAL GROUP SUMMARY")
        print("="*50)
        social_stats = group_manager.get_statistics()
        print(f"Total Groups: {social_stats['total_groups']}")
        print(f"Visitors in Groups: {social_stats['total_visitors_in_groups']}")
        print(f"Solo Visitors: {TOTAL_VISITORS - social_stats['total_visitors_in_groups']}")
        
        if social_stats['group_size_distribution']:
            print("\nGroup Sizes:")
            for size, count in sorted(social_stats['group_size_distribution'].items()):
                print(f"  Size {size}: {count} groups")
        
        # Staff stats
        print("\n" + "="*50)
        print("STAFF PERFORMANCE SUMMARY")
        print("="*50)
        staff_stats = staff_manager.get_statistics()
        print(f"Total Staff: {staff_stats['total_staff']}")
        
        if 'performance' in staff_stats:
            perf = staff_stats['performance']
            if 'incidents_handled' in perf:
                print(f"\nSecurity Performance:")
                print(f"  Incidents Handled: {perf['incidents_handled']}")
                print(f"  Lost Children Found: {perf['children_found']}")
            
            if 'areas_cleaned' in perf:
                print(f"\nJanitor Performance:")
                print(f"  Areas Cleaned: {perf['areas_cleaned']}")
        
        # Cleanliness
        print("\n" + "="*50)
        print("PARK CLEANLINESS")
        print("="*50)
        clean_summary = cleanliness_manager.get_summary()
        print(f"Average Cleanliness: {clean_summary['average']:.1f}%\n")
        
        for zone, level in sorted(clean_summary['zones'].items()):
            if level >= 70:
                status = "✓ Clean"
            elif level >= 40:
                status = "⚠ Needs Attention"
            else:
                status = "✗ Dirty"
            print(f"  {zone:15} {level:5.1f}%  {status}")
        
        print("\n" + "="*50)
        print("RIDE STATISTICS")
        print("="*50)
        for ride in rides:
            print(f"  {ride.name:20} {ride.get_total_riders():4} riders")
        
        print("\n" + "="*60)
        print("SIMULATION COMPLETE")
        print("="*60 + "\n")
        
        metrics.close()