"""
Ride State Design Pattern
=========================
Implements different operational states for rides:
- Open: Waiting for visitors
- Boarding: Collecting passengers for next cycle
- Broken: Under repair
- Maintenance: Scheduled downtime
"""

from __future__ import annotations
from abc import ABC, abstractmethod

class RideState(ABC):
    """Base interface for all ride states."""

    # The Ride context will set this when we transition
    ride: "Ride" = None  # type: ignore

    # Optional hooks for state transitions
    def on_enter(self):
        """Called when entering this state"""
        pass
    
    def on_exit(self):
        """Called when exiting this state"""
        pass

    @abstractmethod
    def name(self) -> str:
        """Return the name of this state"""
        ...

    @abstractmethod
    def can_enqueue(self) -> bool:
        """Can visitors join the queue while in this state?"""
        ...

    @abstractmethod
    def tick(self):
        """
        Called by the Ride thread once per simulated minute.
        This is where the state performs its work and may transition.
        """
        ...


class OpenState(RideState):
    """Ride is open and waiting for visitors"""
    
    def name(self) -> str:
        return "OPEN"
    
    def can_enqueue(self) -> bool:
        return True

    def tick(self):
        # If there are people waiting, start boarding
        if self.ride.queue.size() > 0:
            self.ride.transition_to(self.ride.boarding)


class BoardingState(RideState):
    """Ride is boarding passengers"""
    
    def name(self) -> str:
        return "BOARDING"
    
    def can_enqueue(self) -> bool:
        return True  # Visitors can still join queue during boarding

    def on_enter(self):
        """Initialize boarding window timer"""
        self._minutes_in_window = 0

    def tick(self):
        """
        Give the queue a short window to fill seats.
        After boarding window or when batch is ready, run the ride.
        """
        self._minutes_in_window += 1
        
        # Try to get a batch of riders
        batch = self.ride.queue.dequeue_batch(self.ride.capacity)

        if batch:
            # We have riders - run the ride cycle
            print(f"[{self.ride.name}] Boarding {len(batch)} riders...")
            self.ride._run_cycle(batch)
            
            # After cycle completes, go back to OPEN
            self.ride.transition_to(self.ride.open)
        else:
            # No riders yet - check if boarding window has expired
            if self._minutes_in_window >= self.ride.board_window:
                # Window closed with no riders - return to OPEN
                self.ride.transition_to(self.ride.open)
            # Otherwise stay in boarding and wait


class BrokenState(RideState):
    """Ride is broken and under repair"""
    
    def __init__(self, repair_minutes: int = 0):
        self._remaining = max(0, repair_minutes)

    def name(self) -> str:
        return "BROKEN"
    
    def can_enqueue(self) -> bool:
        return False  # Can't join queue while broken

    def on_enter(self):
        """Set repair time and notify"""
        if self._remaining == 0:
            self._remaining = 15  # Default repair time
        
        print(f"[ALERT] {self.ride.name} has BROKEN DOWN! Repair time: {self._remaining} minutes")

    def tick(self):
        """Count down repair time"""
        if self._remaining > 0:
            self._remaining -= 1
            
        if self._remaining <= 0:
            print(f"[FIXED] {self.ride.name} is operational again!")
            self.ride.transition_to(self.ride.open)


class MaintenanceState(RideState):
    """Ride is under scheduled maintenance"""
    
    def __init__(self, minutes: int):
        self._remaining = max(1, minutes)

    def name(self) -> str:
        return "MAINTENANCE"
    
    def can_enqueue(self) -> bool:
        return False  # Can't join queue during maintenance

    def on_enter(self):
        """Notify of maintenance start"""
        print(f"[MAINTENANCE] {self.ride.name} closed for {self._remaining} minutes of maintenance")

    def tick(self):
        """Count down maintenance time"""
        self._remaining -= 1
        
        if self._remaining <= 0:
            print(f"[REOPENED] {self.ride.name} maintenance complete!")
            self.ride.transition_to(self.ride.open)