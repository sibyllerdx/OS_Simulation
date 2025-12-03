import threading
from collections import defaultdict
import sqlite3
from typing import Optional

class Metrics:
    """
    Collects statistics about the simulation.
    Thread-safe aggregator for visitor activities, revenue, etc.
    Also persists metrics to a SQLite database if db_path is provided.
    """
    def __init__(self, db_path: Optional[str] = None):
        self.lock = threading.Lock()
        self.visitor_arrivals = []
        self.visitor_exits = []
        self.ride_counts = defaultdict(int)
        self.food_purchases = defaultdict(int)
        self.merch_purchases = defaultdict(int) 

        self.total_revenue = 0
        self.total_food_revenue = 0.0
        self.total_merch_revenue = 0.0

        self.bathroom_visits = defaultdict(int)
        
        # Social group tracking
        self.group_activities = []  # Track group activities together
        
        # Staff performance tracking
        self.staff_actions = []  # Track staff actions (cleaning, incidents, etc.)
        
        # Ride incidents tracking
        self.ride_breakdowns = []  # Track when rides break down
        self.ride_maintenance = []  # Track scheduled maintenance
        
        # Cleanliness tracking
        self.cleanliness_logs = []  # Track cleanliness over time
        
        # NEW: Enhanced tracking for plotting
        self.ride_queue_entries = []  # {visitor_id, ride_name, minute, queue_length}
        self.ride_boardings = []  # {visitor_id, ride_name, minute}
        self.visitor_data = {}  # visitor_id -> {arrival, exit, rides_taken, money_spent}
        self.facility_revenue = defaultdict(float)  # facility_name -> total_revenue
        self.max_time = 0  # Maximum simulation time seen


        # SQLite setup
        self.db_path = db_path
        self.conn = None
        if db_path is not None:
            # allow use from multiple threads, but protect with self.lock
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self._init_db()

    # ---------- SQLite helpers ----------

    def _init_db(self):
        """Create tables if they don't already exist."""
        with self.lock:
            cur = self.conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS visitor_arrivals (
                    id INTEGER,
                    minute INTEGER,
                    type TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS visitor_exits (
                    id INTEGER,
                    minute INTEGER
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS rides (
                    visitor_id INTEGER,
                    ride_name TEXT,
                    minute INTEGER
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS food_purchases (
                    visitor_id INTEGER,
                    facility_name TEXT,
                    minute INTEGER,
                    amount REAL
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS bathroom_visits (
                    visitor_id INTEGER,
                    bathroom_name TEXT,
                    minute INTEGER
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS merch_purchases (
                    visitor_id INTEGER,
                    stand_name TEXT,
                    product TEXT,
                    minute INTEGER,
                    amount REAL
                )
            """)
            
            # Social groups table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS social_groups (
                    group_id INTEGER,
                    group_type TEXT,
                    group_size INTEGER
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS group_activities (
                    group_id INTEGER,
                    activity_type TEXT,
                    location TEXT,
                    minute INTEGER,
                    member_count INTEGER
                )
            """)
            
            # Staff performance tables
            cur.execute("""
                CREATE TABLE IF NOT EXISTS staff_actions (
                    staff_id INTEGER,
                    staff_name TEXT,
                    staff_type TEXT,
                    action_type TEXT,
                    location TEXT,
                    minute INTEGER,
                    efficiency REAL
                )
            """)
            
            # Ride incidents tables
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ride_breakdowns (
                    ride_name TEXT,
                    minute INTEGER,
                    repair_duration INTEGER
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ride_maintenance (
                    ride_name TEXT,
                    minute INTEGER,
                    maintenance_duration INTEGER
                )
            """)
            
            # Cleanliness tracking
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cleanliness_logs (
                    zone TEXT,
                    cleanliness_level REAL,
                    minute INTEGER
                )
            """)

            self.conn.commit()

    def _insert(self, query, params):
        """Small helper to execute an INSERT with locking."""
        if self.conn is None:
            return
        cur = self.conn.cursor()
        cur.execute(query, params)
        self.conn.commit()

    def close(self):
        """Close the database connection if open."""
        if self.conn is not None:
            with self.lock:
                self.conn.close()
                self.conn = None

    # ---------- Metrics recording ----------

    def record_arrival(self, visitor_id, minute, visitor_type):
        """Record a visitor entering the park"""
        with self.lock:
            self.visitor_arrivals.append({
                'id': visitor_id,
                'minute': minute,
                'type': visitor_type
            })
            # Track per-visitor data
            if visitor_id not in self.visitor_data:
                self.visitor_data[visitor_id] = {
                    'arrival': minute,
                    'exit': None,
                    'rides_taken': 0,
                    'money_spent': 0.0
                }
            self.max_time = max(self.max_time, minute)
            if self.conn is not None:
                self._insert(
                    "INSERT INTO visitor_arrivals (id, minute, type) VALUES (?, ?, ?)",
                    (visitor_id, minute, visitor_type)
                )

    def record_exit(self, visitor_id, minute):
        """Record a visitor leaving the park"""
        with self.lock:
            self.visitor_exits.append({
                'id': visitor_id,
                'minute': minute
            })
            # Update per-visitor data
            if visitor_id in self.visitor_data:
                self.visitor_data[visitor_id]['exit'] = minute
            self.max_time = max(self.max_time, minute)
            if self.conn is not None:
                self._insert(
                    "INSERT INTO visitor_exits (id, minute) VALUES (?, ?)",
                    (visitor_id, minute)
                )

    def record_bathroom_visit(self, visitor_id, bathroom_name, minute):
        with self.lock:
            self.bathroom_visits[bathroom_name] += 1
            if self.conn is not None:
                self._insert(
                    "INSERT INTO bathroom_visits (visitor_id, bathroom_name, minute) "
                    "VALUES (?, ?, ?)",
                    (visitor_id, bathroom_name, minute)
                )

    def record_ride(self, visitor_id, ride_name, minute):
        """Record a visitor riding an attraction"""
        with self.lock:
            self.ride_counts[ride_name] += 1
            # Update per-visitor ride count
            if visitor_id in self.visitor_data:
                self.visitor_data[visitor_id]['rides_taken'] += 1
            self.max_time = max(self.max_time, minute)
            if self.conn is not None:
                self._insert(
                    "INSERT INTO rides (visitor_id, ride_name, minute) VALUES (?, ?, ?)",
                    (visitor_id, ride_name, minute)
                )

    def record_food_purchase(self, visitor_id, facility_name, minute, amount):
        """Record a food purchase"""
        with self.lock:
            self.food_purchases[facility_name] += 1
            self.total_food_revenue += amount
            self.total_revenue += amount  # total = food + merch
            # Update per-visitor spend and per-facility revenue
            if visitor_id in self.visitor_data:
                self.visitor_data[visitor_id]['money_spent'] += amount
            self.facility_revenue[facility_name] += amount
            self.max_time = max(self.max_time, minute)

            if self.conn is not None:
                self._insert(
                    "INSERT INTO food_purchases (visitor_id, facility_name, minute, amount) "
                    "VALUES (?, ?, ?, ?)",
                    (visitor_id, facility_name, minute, amount)
                )

    def record_merch_purchase(self, visitor_id, stand_name, product, minute, amount):
        """Record a merchandise purchase"""
        with self.lock:
            self.merch_purchases[stand_name] += 1
            self.total_merch_revenue += amount
            self.total_revenue += amount  # keep combined total
            # Update per-visitor spend and per-facility revenue
            if visitor_id in self.visitor_data:
                self.visitor_data[visitor_id]['money_spent'] += amount
            self.facility_revenue[stand_name] += amount
            self.max_time = max(self.max_time, minute)

            if self.conn is not None:
                self._insert(
                    "INSERT INTO merch_purchases (visitor_id, stand_name, product, minute, amount) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (visitor_id, stand_name, product, minute, amount)
                )
    
    def record_social_group(self, group_id, group_type, group_size, minute):
        """Record creation of a social group"""
        with self.lock:
            if self.conn is not None:
                self._insert(
                    "INSERT INTO social_groups (group_id, group_type, group_size) "
                    "VALUES (?, ?, ?)",
                    (group_id, group_type, group_size)
                )
    
    def record_group_activity(self, group_id, activity_type, location, minute, member_count):
        """Record a group doing an activity together"""
        with self.lock:
            self.group_activities.append({
                'group_id': group_id,
                'activity_type': activity_type,
                'location': location,
                'minute': minute,
                'member_count': member_count
            })
            if self.conn is not None:
                self._insert(
                    "INSERT INTO group_activities (group_id, activity_type, location, minute, member_count) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (group_id, activity_type, location, minute, member_count)
                )
    
    def record_staff_action(self, staff_id, staff_name, staff_type, action_type, location, minute, efficiency=1.0):
        """Record a staff member performing an action"""
        with self.lock:
            self.staff_actions.append({
                'staff_id': staff_id,
                'staff_name': staff_name,
                'staff_type': staff_type,
                'action_type': action_type,
                'location': location,
                'minute': minute,
                'efficiency': efficiency
            })
            if self.conn is not None:
                self._insert(
                    "INSERT INTO staff_actions (staff_id, staff_name, staff_type, action_type, location, minute, efficiency) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (staff_id, staff_name, staff_type, action_type, location, minute, efficiency)
                )
    
    def record_ride_breakdown(self, ride_name, minute, repair_duration):
        """Record a ride breaking down"""
        with self.lock:
            self.ride_breakdowns.append({
                'ride_name': ride_name,
                'minute': minute,
                'repair_duration': repair_duration
            })
            if self.conn is not None:
                self._insert(
                    "INSERT INTO ride_breakdowns (ride_name, minute, repair_duration) "
                    "VALUES (?, ?, ?)",
                    (ride_name, minute, repair_duration)
                )
    
    def record_ride_maintenance(self, ride_name, minute, maintenance_duration):
        """Record scheduled ride maintenance"""
        with self.lock:
            self.ride_maintenance.append({
                'ride_name': ride_name,
                'minute': minute,
                'maintenance_duration': maintenance_duration
            })
            if self.conn is not None:
                self._insert(
                    "INSERT INTO ride_maintenance (ride_name, minute, maintenance_duration) "
                    "VALUES (?, ?, ?)",
                    (ride_name, minute, maintenance_duration)
                )
    
    def record_cleanliness(self, zone, cleanliness_level, minute):
        """Record cleanliness level of a zone"""
        with self.lock:
            self.cleanliness_logs.append({
                'zone': zone,
                'cleanliness_level': cleanliness_level,
                'minute': minute
            })
            if self.conn is not None:
                self._insert(
                    "INSERT INTO cleanliness_logs (zone, cleanliness_level, minute) "
                    "VALUES (?, ?, ?)",
                    (zone, cleanliness_level, minute)
                )
    
    def record_ride_queue_entry(self, visitor_id, ride_name, minute, queue_length):
        """Record when a visitor joins a ride queue"""
        with self.lock:
            self.ride_queue_entries.append({
                'visitor_id': visitor_id,
                'ride_name': ride_name,
                'minute': minute,
                'queue_length': queue_length
            })
            self.max_time = max(self.max_time, minute)
    
    def record_ride_boarding(self, visitor_id, ride_name, minute):
        """Record when a visitor boards a ride"""
        with self.lock:
            self.ride_boardings.append({
                'visitor_id': visitor_id,
                'ride_name': ride_name,
                'minute': minute
            })
            self.max_time = max(self.max_time, minute)


    # ---------- Aggregated summary ----------

    def get_summary(self):
        """Get summary statistics from in-memory aggregations."""
        with self.lock:
            return {
                        'total_visitors': len(self.visitor_arrivals),
                        'total_exits': len(self.visitor_exits),
                        'ride_counts': dict(self.ride_counts),
                        'food_purchases': dict(self.food_purchases),
                        'merch_purchases': dict(self.merch_purchases),
                        'total_food_revenue': self.total_food_revenue,
                        'total_merch_revenue': self.total_merch_revenue,
                        'total_revenue': self.total_revenue,
                        'total_group_activities': len(self.group_activities),
                        'total_staff_actions': len(self.staff_actions),
                        'total_breakdowns': len(self.ride_breakdowns),
                        'total_maintenance_events': len(self.ride_maintenance),
                        'cleanliness_samples': len(self.cleanliness_logs)
                        }
        
    def print_summary(self):
        """Print a formatted summary"""
        summary = self.get_summary()
        print("\n" + "="*50)
        print("PARK SIMULATION SUMMARY")
        print("="*50)
        print(f"Total Visitors: {summary['total_visitors']}")
        print(f"Visitors Who Left: {summary['total_exits']}")

        print(f"\nMost Popular Rides:")
        for ride, count in sorted(summary['ride_counts'].items(),
                                  key=lambda x: x[1], reverse=True):
            print(f"  {ride}: {count} rides")

        print(f"\nFood Revenue:  ${summary['total_food_revenue']:.2f}")
        if summary['merch_purchases']:
            print("\nMerch Purchases by Stand:")
            for stand, count in summary['merch_purchases'].items():
                print(f"  {stand}: {count} purchases")

        print(f"Merch Revenue: ${summary['total_merch_revenue']:.2f}")
        print(f"TOTAL Revenue: ${summary['total_revenue']:.2f}")
        
        # New metrics
        print(f"\nSocial & Operations:")
        print(f"  Group Activities Logged: {summary['total_group_activities']}")
        print(f"  Staff Actions Logged: {summary['total_staff_actions']}")
        print(f"  Ride Breakdowns: {summary['total_breakdowns']}")
        print(f"  Maintenance Events: {summary['total_maintenance_events']}")
        print(f"  Cleanliness Samples: {summary['cleanliness_samples']}")
    
    def get_analysis_data(self):
        """
        Prepare comprehensive analysis data for plotting.
        Returns a dictionary with all metrics needed for visualization.
        """
        with self.lock:
            # Calculate per-ride wait times
            wait_times_by_ride = defaultdict(list)
            
            # Create a mapping of (visitor_id, ride_name) -> queue_entry_time
            queue_entries = {}
            for entry in self.ride_queue_entries:
                key = (entry['visitor_id'], entry['ride_name'])
                if key not in queue_entries:  # Keep first entry
                    queue_entries[key] = entry['minute']
            
            # Match boardings to queue entries to calculate wait times
            for boarding in self.ride_boardings:
                key = (boarding['visitor_id'], boarding['ride_name'])
                if key in queue_entries:
                    wait_time = boarding['minute'] - queue_entries[key]
                    wait_times_by_ride[boarding['ride_name']].append(wait_time)
            
            # Calculate average wait times per ride
            avg_wait_times = {}
            for ride_name, wait_list in wait_times_by_ride.items():
                if wait_list:
                    avg_wait_times[ride_name] = sum(wait_list) / len(wait_list)
            
            # Calculate per-visitor metrics
            visitor_time_in_park = []
            visitor_spend = []
            visitor_rides_taken = []
            visitor_ids = []
            spend_vs_time = []  # [(time, spend), ...]
            visitor_time_data = []  # [(visitor_id, time_in_park), ...] for sorting
            
            for vid, data in self.visitor_data.items():
                if data['exit'] is not None and data['arrival'] is not None:
                    time_in_park = data['exit'] - data['arrival']
                    visitor_time_in_park.append(time_in_park)
                    visitor_spend.append(data['money_spent'])
                    visitor_rides_taken.append(data['rides_taken'])
                    visitor_ids.append(vid)
                    spend_vs_time.append((time_in_park, data['money_spent']))
                    visitor_time_data.append((vid, time_in_park))
            
            # Sort visitor_time_data by time (least to most)
            visitor_time_sorted = sorted(visitor_time_data, key=lambda x: x[1])
            
            # Calculate population over time
            # Create events list: (minute, +1 for arrival, -1 for exit)
            events = []
            for arrival in self.visitor_arrivals:
                events.append((arrival['minute'], 1))
            for exit in self.visitor_exits:
                events.append((exit['minute'], -1))
            
            # Sort by time
            events.sort()
            
            # Build time series
            population_over_time = []
            current_pop = 0
            current_minute = 0
            
            if events:
                for minute, delta in events:
                    # Fill gaps with current population
                    while current_minute < minute:
                        population_over_time.append((current_minute, current_pop))
                        current_minute += 1
                    current_pop += delta
                    population_over_time.append((minute, current_pop))
                    current_minute = minute + 1
                
                # Extend to max_time
                while current_minute <= self.max_time:
                    population_over_time.append((current_minute, current_pop))
                    current_minute += 1
            
            return {
                'ride_counts': dict(self.ride_counts),
                'avg_wait_times': avg_wait_times,
                'facility_revenue': dict(self.facility_revenue),
                'visitor_time_in_park': visitor_time_in_park,
                'visitor_spend': visitor_spend,
                'visitor_rides_taken': visitor_rides_taken,
                'visitor_ids': visitor_ids,
                'spend_vs_time': spend_vs_time,
                'visitor_time_sorted': visitor_time_sorted,
                'population_over_time': population_over_time,
                'max_time': self.max_time
            }
