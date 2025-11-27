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

            if self.conn is not None:
                self._insert(
                    "INSERT INTO merch_purchases (visitor_id, stand_name, product, minute, amount) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (visitor_id, stand_name, product, minute, amount)
                )


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
                        'total_revenue': self.total_revenue
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
