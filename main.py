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

# Import simplified social system
from park3.simple_social import LocationTracker, GroupManager, GroupCoordinator, GroupType

def create_initial_groups(num_groups=30):
    """Create initial social groups"""
    groups_created = []
    
    for i in range(num_groups):
        # Group size distribution
        group_size = random.choices(
            [2, 3, 4, 5, 6],
            weights=[0.35, 0.30, 0.20, 0.10, 0.05]
        )[0]
        
        # Group type
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
    """Create ride instances"""
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

if __name__ == "__main__":
    print("\n" + "="*60)
    print("AMUSEMENT PARK SIMULATION WITH SOCIAL GROUPS")
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
    print(f"  Speed Factor: {SPEED_FACTOR}s per sim minute")
    print(f"  Initial Groups: {NUM_INITIAL_GROUPS}")
    
    # Initialize systems
    clock = Clock(speed_factor=SPEED_FACTOR)
    metrics = Metrics(db_path="park_metrics.sqlite")
    
    # Social systems
    print("\nInitializing social systems...")
    location_tracker = LocationTracker()
    group_manager = GroupManager()
    group_coordinator = GroupCoordinator(group_manager, location_tracker)
    print("  Social systems ready!")
    
    # Create park
    park = Park(clock, metrics)
    park.location_tracker = location_tracker
    park.group_manager = group_manager
    park.group_coordinator = group_coordinator
    
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
    
    print(f"  Created {len(rides)} rides, {NUM_FOOD_TRUCKS} food trucks, "
          f"{NUM_MERCH_STANDS} merch stands, {NUM_BATHROOMS} bathrooms")
    
    # Create groups
    print("\nCreating social groups...")
    initial_groups = create_initial_groups(NUM_INITIAL_GROUPS)
    total_group_members = sum(g['size'] for g in initial_groups)
    print(f"  Created {len(initial_groups)} groups with {total_group_members} members")
    print(f"  Solo visitors: {TOTAL_VISITORS - total_group_members}")
    
    # Create arrival generator
    arrival_gen = ArrivalGenerator(
        clock, park, metrics, 
        total_visitors=TOTAL_VISITORS,
        park_hours=PARK_HOURS,
        visitor_mix=VISITOR_MIX,
        initial_groups=initial_groups
    )
    
    # Register groups AFTER arrival generator fills member_ids
    print("\nRegistering groups...")
    groups_registered = 0
    for group_info in initial_groups:
        if group_info['member_ids']:
            group_manager.create_group(
                group_info['type'],
                group_info['member_ids']
            )
            groups_registered += 1
    print(f"  Registered {groups_registered} groups")
    
    # Verify registration
    stats = group_manager.get_statistics()
    print(f"  Verification: {stats['total_groups']} groups, "
          f"{stats['total_visitors_in_groups']} visitors in groups")
    
    # Create UI
    print("\nSetting up UI...")
    ui = ParkUI(park, clock, metrics, rides, food_trucks, merch_stands, bathrooms)
    
    # Start simulation
    print("\n" + "="*60)
    print("STARTING SIMULATION")
    print("="*60 + "\n")
    
    clock.start()
    
    # Start facilities
    park.start_all_rides()
    park.start_all_food_facilities()
    park.start_all_bathrooms()
    park.start_all_merch_stands()
    
    # Start arrivals
    arrival_gen.start()
    
    # Run
    try:
        sim_duration = PARK_HOURS * SPEED_FACTOR
        print(f"Simulation will run for ~{sim_duration:.1f} seconds...")
        print("Close the matplotlib window to stop.\n")
        
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
        
        # Print results
        metrics.print_summary()
        
        # Social statistics
        print("\n" + "="*50)
        print("SOCIAL GROUP SUMMARY")
        print("="*50)
        
        social_stats = group_manager.get_statistics()
        print(f"Total Groups Created: {social_stats['total_groups']}")
        print(f"Visitors in Groups: {social_stats['total_visitors_in_groups']}")
        print(f"Solo Visitors: {TOTAL_VISITORS - social_stats['total_visitors_in_groups']}")
        print(f"Active Groups (still in park): {social_stats['active_groups']}")
        
        if social_stats['group_size_distribution']:
            print("\nGroup Size Distribution:")
            for size, count in sorted(social_stats['group_size_distribution'].items()):
                print(f"  Size {size}: {count} groups")
        
        if social_stats['group_types']:
            print("\nGroup Types:")
            for gtype, count in social_stats['group_types'].items():
                print(f"  {gtype}: {count} groups")
        else:
            print("\nNo group data available")
        
        print("\nLocation Distribution (visitors still in park):")
        loc_summary = location_tracker.get_location_summary()
        if loc_summary:
            for location, count in sorted(loc_summary.items()):
                print(f"  {location}: {count} visitors")
        else:
            print("  All visitors have left the park")
        
        print("\n" + "="*50)
        print("RIDE STATISTICS")
        print("="*50)
        for ride in rides:
            print(f"  {ride.name}: {ride.get_total_riders()} riders")
        
        print("\n" + "="*60)
        print("SIMULATION COMPLETE")
        print("="*60 + "\n")
        
        metrics.close()