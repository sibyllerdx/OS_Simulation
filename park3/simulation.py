"""
Amusement Park Simulation
=========================
A multi-threaded simulation of an amusement park with:
- 3 visitor types: Children, Tourists, Adrenaline Addicts
- Multiple rides that can break down
- Food trucks that generate revenue
- Realistic arrival patterns and visitor behaviors
"""

import time
from clock import Clock
from metrics import Metrics
from bathroom import Toilet
from queue import Queue
from merch import MerchStand
from ride import Ride
from food import FoodTruck
from park import Park
from arrival_generator import ArrivalGenerator

def create_rides():
    """Create ride instances with their specifications"""
    rides_config = [
        # (name, capacity, duration, break_prob, repair_time, board_window, min_height_cm)
        ('RollerCoaster', 24, 5, 0.03, 15, 3, 140),  # Reduced break probability
        ('DropTower', 16, 4, 0.04, 12, 2, 145),
        ('FerrisWheel', 32, 8, 0.01, 10, 4,0),  # Very reliable
        ('HauntedHouse', 20, 6, 0.02, 8, 3, 140),
        ('SpinningTeacups', 16, 4, 0.02, 6, 2, 100),
        ('BumperCars', 20, 5, 0.03, 7, 3, 110),
        ('SplashMountain', 28, 7, 0.03, 14, 4, 120),
        ('SpaceSimulator', 12, 6, 0.05, 20, 2, 120),  # More complex, breaks more
        ('CarouselHorses', 24, 5, 0.01, 5, 3,0),  # Very reliable
    ]
    
    rides = []
    for name, capacity, duration, break_prob, repair_time, board_window, min_height in rides_config:
        queue = Queue()
        ride = Ride(name, queue, clock, capacity, duration, 
                   break_prob, repair_time, board_window, metrics, min_height_cm=min_height)
        rides.append(ride)
        
    return rides

def create_food_trucks(num_trucks):
    """Create food truck instances"""
    trucks = []
    for i in range(num_trucks):
        queue = Queue()
        truck = FoodTruck(f"FoodTruck-{i+1}", queue, clock, metrics)
        trucks.append(truck)
    return trucks

def create_merch_stands(num_stands):
    stands = []
    for i in range(num_stands):
        q = Queue()
        stand = MerchStand(f"MerchStand-{i+1}", q, clock, metrics)
        stands.append(stand)
    return stands

if __name__ == "__main__":
    print("\n" + "="*60)
    print("AMUSEMENT PARK SIMULATION")
    print("="*60)
    
    # Simulation parameters
    TOTAL_VISITORS = 300
    PARK_HOURS = 480  # 8 hours in simulated minutes
    SPEED_FACTOR = 0.05  # 0.05 real seconds = 1 sim minute (fast simulation)
    NUM_FOOD_TRUCKS = 5
    NUM_MERCH_STANDS = 3 
    
    # Visitor mix
    VISITOR_MIX = {
        'Child': 0.3,
        'Tourist': 0.5,
        'AdrenalineAddict': 0.2
    }
    
    print(f"\nConfiguration:")
    print(f"  Total Visitors: {TOTAL_VISITORS}")
    print(f"  Park Hours: {PARK_HOURS} minutes")
    print(f"  Speed Factor: {SPEED_FACTOR}s per sim minute")
    print(f"  Visitor Mix: {VISITOR_MIX}")
    print(f"  Food Trucks: {NUM_FOOD_TRUCKS}")
    
    # Initialize core systems
    clock = Clock(speed_factor=SPEED_FACTOR)
    metrics = Metrics(db_path="park_metrics.sqlite")
    park = Park(clock, metrics)
    
    # Create and add rides
    print("\nSetting up rides...")
    rides = create_rides()
    for ride in rides:
        park.add_ride(ride)
    print(f"  Created {len(rides)} rides")
    
    # Create and add food trucks
    print("Setting up food trucks...")
    food_trucks = create_food_trucks(NUM_FOOD_TRUCKS)
    for truck in food_trucks:
        park.add_food_facility(truck)
    print(f"  Created {NUM_FOOD_TRUCKS} food trucks")

    #Create merch shops
    print("Setting up merch stands...")
    merch_stands = create_merch_stands(NUM_MERCH_STANDS)
    for stand in merch_stands:
        park.add_merch_stand(stand)
    print(f"  Created {NUM_MERCH_STANDS} merch stands")


    #Create the bathrooms 
    num_bathrooms = 5
    bathrooms = []

    for i in range(num_bathrooms):
        q = Queue()
        bathroom = Toilet(
            name=f"Bathroom-{i+1}",
            queue=q,
            clock=clock,
            metrics=metrics
        )
        park.add_bathroom(bathroom)
        bathrooms.append(bathroom)

    
    # Create arrival generator
    arrival_gen = ArrivalGenerator(
        clock, park, metrics, 
        total_visitors=TOTAL_VISITORS,
        park_hours=PARK_HOURS,
        visitor_mix=VISITOR_MIX
    )
    
    # Start simulation
    print("\n" + "="*60)
    print("STARTING SIMULATION")
    print("="*60 + "\n")
    
    clock.start()
    
    # Start all facility threads
    park.start_all_rides()
    park.start_all_food_facilities()
    bathroom.start()
    park.start_all_merch_stands()
    
    # Start arrival generator
    arrival_gen.start()
    
    # Run simulation for specified duration
    try:
        sim_duration = PARK_HOURS * SPEED_FACTOR
        print(f"Simulation will run for ~{sim_duration:.1f} seconds of real time...\n")
        
        # Monitor progress and ride states
        start_time = time.time()
        last_status_minute = -10
        while clock.now() < PARK_HOURS:
            time.sleep(2)
            current_minute = clock.now()
            progress = (current_minute / PARK_HOURS) * 100
            print(f"Simulation progress: {progress:.1f}% (Minute {current_minute}/{PARK_HOURS})")
            
            # Periodically show ride states
            if current_minute - last_status_minute >= 30:
                print("\n  Current Ride States:")
                for ride in rides:
                    state = ride.get_state_name()
                    queue_size = ride.queue.size()
                    print(f"    {ride.name}: {state} (Queue: {queue_size})")
                print()
                last_status_minute = current_minute
            
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user!")
        
    finally:
        # Stop simulation
        print("\n" + "="*60)
        print("ENDING SIMULATION")
        print("="*60)
        
        clock.stop()
        time.sleep(1)  # Give threads time to finish
        park.close_all()
        
        # Print results
        metrics.print_summary()
                        # Additional stats
        print("\nRide Statistics:")
        for ride in rides:
            print(f"  {ride.name}: {ride.get_total_riders()} total riders")
            
        print("\nFood Revenue by Truck:")
        total_food_revenue = 0
        for truck in food_trucks:
            revenue = truck.get_revenue()
            total_food_revenue += revenue
            print(f"  {truck.name}: ${revenue:.2f}")
            
        
        print("\n" + "="*60)
        print("SIMULATION COMPLETE")
        print("="*60 + "\n")
        metrics.close()