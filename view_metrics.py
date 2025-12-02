"""
View Metrics Database
=====================
Query and display metrics from the SQLite database
"""

import sqlite3
import sys

def view_all_tables(db_path="park_metrics.sqlite"):
    """View all tables and their row counts"""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Get all table names
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cur.fetchall()
        
        print("\n" + "="*60)
        print("PARK METRICS DATABASE SUMMARY")
        print("="*60)
        print(f"Database: {db_path}\n")
        
        for (table_name,) in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cur.fetchone()[0]
            print(f"  {table_name:30} {count:6} rows")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

def view_table_sample(db_path="park_metrics.sqlite", table_name=None, limit=10):
    """View sample data from a specific table"""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        if table_name is None:
            print("Available tables:")
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            for (name,) in cur.fetchall():
                print(f"  - {name}")
            conn.close()
            return
        
        # Get column names
        cur.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cur.fetchall()]
        
        # Get sample data
        cur.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cur.fetchall()
        
        print(f"\n{'='*60}")
        print(f"Table: {table_name} (showing {len(rows)} of {limit} max)")
        print('='*60)
        
        if rows:
            # Print header
            print(" | ".join(f"{col:15}" for col in columns))
            print("-" * (len(columns) * 18))
            
            # Print rows
            for row in rows:
                print(" | ".join(f"{str(val):15}" for val in row))
        else:
            print("No data in table")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

def view_summary_stats(db_path="park_metrics.sqlite"):
    """View summary statistics"""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        print("\n" + "="*60)
        print("DETAILED STATISTICS")
        print("="*60)
        
        # Visitor stats
        cur.execute("SELECT COUNT(*) FROM visitor_arrivals")
        total_arrivals = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM visitor_exits")
        total_exits = cur.fetchone()[0]
        
        print(f"\nVisitor Stats:")
        print(f"  Total Arrivals: {total_arrivals}")
        print(f"  Total Exits: {total_exits}")
        print(f"  Still in Park: {total_arrivals - total_exits}")
        
        # Revenue
        cur.execute("SELECT SUM(amount) FROM food_purchases")
        food_revenue = cur.fetchone()[0] or 0
        cur.execute("SELECT SUM(amount) FROM merch_purchases")
        merch_revenue = cur.fetchone()[0] or 0
        
        print(f"\nRevenue:")
        print(f"  Food Revenue: ${food_revenue:.2f}")
        print(f"  Merch Revenue: ${merch_revenue:.2f}")
        print(f"  Total Revenue: ${food_revenue + merch_revenue:.2f}")
        
        # Top rides
        cur.execute("""
            SELECT ride_name, COUNT(*) as rides 
            FROM rides 
            GROUP BY ride_name 
            ORDER BY rides DESC 
            LIMIT 5
        """)
        print(f"\nTop 5 Rides:")
        for ride, count in cur.fetchall():
            print(f"  {ride:20} {count:4} rides")
        
        # Social groups
        cur.execute("SELECT COUNT(*) FROM social_groups")
        total_groups = cur.fetchone()[0]
        if total_groups > 0:
            cur.execute("""
                SELECT group_type, COUNT(*) as count, AVG(group_size) as avg_size
                FROM social_groups
                GROUP BY group_type
            """)
            print(f"\nSocial Groups: ({total_groups} total)")
            for group_type, count, avg_size in cur.fetchall():
                print(f"  {group_type:15} {count:3} groups (avg size: {avg_size:.1f})")
        
        # Staff actions
        cur.execute("SELECT COUNT(*) FROM staff_actions")
        total_staff_actions = cur.fetchone()[0]
        if total_staff_actions > 0:
            cur.execute("""
                SELECT action_type, COUNT(*) as count
                FROM staff_actions
                GROUP BY action_type
                ORDER BY count DESC
                LIMIT 10
            """)
            print(f"\nStaff Actions: ({total_staff_actions} total)")
            for action, count in cur.fetchall():
                print(f"  {action:25} {count:4} times")
        
        # Ride incidents
        cur.execute("SELECT COUNT(*) FROM ride_breakdowns")
        total_breakdowns = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM ride_maintenance")
        total_maintenance = cur.fetchone()[0]
        
        if total_breakdowns > 0 or total_maintenance > 0:
            print(f"\nRide Incidents:")
            print(f"  Breakdowns: {total_breakdowns}")
            print(f"  Maintenance Events: {total_maintenance}")
        
        # Cleanliness
        cur.execute("SELECT COUNT(*) FROM cleanliness_logs")
        cleanliness_samples = cur.fetchone()[0]
        if cleanliness_samples > 0:
            cur.execute("""
                SELECT zone, AVG(cleanliness_level) as avg_clean
                FROM cleanliness_logs
                GROUP BY zone
                ORDER BY avg_clean DESC
            """)
            print(f"\nCleanliness (avg over {cleanliness_samples} samples):")
            for zone, avg_clean in cur.fetchall():
                print(f"  {zone:15} {avg_clean:5.1f}%")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    db_path = "park_metrics.sqlite"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "summary":
            view_summary_stats(db_path)
        elif sys.argv[1] == "tables":
            view_all_tables(db_path)
        elif sys.argv[1] == "table":
            if len(sys.argv) > 2:
                table_name = sys.argv[2]
                limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
                view_table_sample(db_path, table_name, limit)
            else:
                view_table_sample(db_path)
        else:
            print("Usage:")
            print("  python view_metrics.py summary    - Show summary statistics")
            print("  python view_metrics.py tables     - List all tables")
            print("  python view_metrics.py table <name> [limit] - Show table data")
    else:
        # Default: show everything
        view_all_tables(db_path)
        view_summary_stats(db_path)
