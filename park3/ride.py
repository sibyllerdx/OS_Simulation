import threading
import random
from ride_states import RideState, OpenState, BoardingState, BrokenState, MaintenanceState

class Ride(threading.Thread):
    """
    An amusement park ride that uses the State design pattern.
    Different states handle different operational modes.
    """
    def __init__(self, name, queue, clock, capacity=20, 
                 run_duration=5, break_probability=0.02,  # Reduced from 0.05
                 repair_time=10, board_window=3, metrics=None):
        super().__init__(daemon=True)
        self.name = name
        self.queue = queue
        self.clock = clock
        self.capacity = capacity
        self.run_duration = run_duration
        self.break_probability = break_probability
        self.repair_time = repair_time
        self.board_window = board_window  # How long to wait for riders
        self.metrics = metrics
        
        self._open = True
        self._lock = threading.Lock()
        self._total_riders = 0
        
        # Initialize all possible states
        self.open = OpenState()
        self.boarding = BoardingState()
        self.broken_state_template = BrokenState  # Factory for broken states
        self.maintenance_state_template = MaintenanceState  # Factory for maintenance
        
        # Set the ride reference for each state
        self.open.ride = self
        self.boarding.ride = self
        
        # Start in OPEN state
        self._current_state: RideState = None
        self.transition_to(self.open)
        
    def transition_to(self, new_state: RideState):
        """
        Transition to a new state.
        Calls on_exit() for old state and on_enter() for new state.
        """
        with self._lock:
            if self._current_state is not None:
                self._current_state.on_exit()
                
            self._current_state = new_state
            self._current_state.on_enter()
            
    def get_state_name(self) -> str:
        """Get the current state name"""
        with self._lock:
            return self._current_state.name()
        
    def run(self):
        """Main ride operation loop - delegates to current state"""
        while not self.clock.should_stop() and self._open:
            # Let the current state handle this tick
            with self._lock:
                current_state = self._current_state
                
            current_state.tick()
            
            # Sleep for one simulated minute
            self.clock.sleep_minutes(1)
            
    def _run_cycle(self, batch):
        """
        Execute one ride cycle with a batch of visitors.
        Called by the BoardingState.
        """
        # Ride is running
        self.clock.sleep_minutes(self.run_duration)
        
        # Update stats
        with self._lock:
            self._total_riders += len(batch)
            
        # Notify all visitors the ride is finished
        for visitor in batch:
            if self.metrics:
                self.metrics.record_ride(visitor.vid, self.name, self.clock.now())
            visitor.on_ride_finished(self.name, self.clock.now())
            
        # Small turnaround time
        self.clock.sleep_minutes(1)
        
        # Chance of breakdown after cycle
        if random.random() < self.break_probability:
            self._breakdown()
            
    def _breakdown(self):
        """Trigger a breakdown - transition to broken state"""
        broken = self.broken_state_template(self.repair_time)
        broken.ride = self
        self.transition_to(broken)
        
    def schedule_maintenance(self, minutes: int):
        """Schedule maintenance for this ride"""
        maintenance = self.maintenance_state_template(minutes)
        maintenance.ride = self
        self.transition_to(maintenance)
        
    def is_operational(self):
        """Check if ride is currently operational (can accept riders)"""
        with self._lock:
            return self._current_state.can_enqueue()
            
    def get_total_riders(self):
        """Get total number of riders served"""
        with self._lock:
            return self._total_riders
            
    def close(self):
        """Close the ride"""
        self._open = False