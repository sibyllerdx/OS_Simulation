import threading
import time

class Clock:
    """
    Central time keeper for the simulation.
    Converts real seconds to simulated minutes.
    """
    def __init__(self, speed_factor=0.1, max_minutes=None):
        """
        Args:
            speed_factor: seconds of real time per simulated minute
                         0.1 means 1 sim minute = 0.1 real seconds (fast)
            max_minutes: maximum simulation time in minutes (optional)
        """
        self._speed_factor = speed_factor
        self._max_minutes = max_minutes
        self._start_time = None
        self._stop_flag = False
        self._lock = threading.Lock()
        
    def start(self):
        """Start the simulation clock"""
        with self._lock:
            self._start_time = time.time()
            self._stop_flag = False
            
    def now(self):
        """Get current simulated minute"""
        with self._lock:
            if self._start_time is None:
                return 0
            elapsed_real = time.time() - self._start_time
            current = int(elapsed_real / self._speed_factor)
            
            # Cap at max_minutes if set
            if self._max_minutes is not None:
                current = min(current, self._max_minutes)
                # Auto-stop if we've reached the limit
                if current >= self._max_minutes:
                    self._stop_flag = True
                    
            return current
    
    def sleep_minutes(self, minutes):
        """Sleep for simulated minutes"""
        time.sleep(minutes * self._speed_factor)
        
    def should_stop(self):
        """Check if simulation should stop"""
        with self._lock:
            return self._stop_flag
            
    def stop(self):
        """Signal all threads to stop"""
        with self._lock:
            self._stop_flag = True