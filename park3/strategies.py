# strategies.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
import random
from .ride import Ride

class RideChoiceStrategy(ABC):
    @abstractmethod
    def pick_ride(self, visitor, park) -> Optional["Ride"]:
        """Return the chosen Ride (or None if no ride is available)."""
        ...

def _eligible_rides(visitor, park):
    """Helper: operational rides where visitor meets height requirements."""
    height = getattr(visitor, "height_cm", 0)
    rides = []
    for r in park.get_rides():
        if not r.is_operational():
            continue
        min_h = getattr(r, "min_height_cm", 0)
        if height >= min_h:
            rides.append(r)
    return rides

class RandomStrategy(RideChoiceStrategy):
    """Pure random choice among operational rides the visitor is tall enough for."""
    def pick_ride(self, visitor, park):
        rides = _eligible_rides(visitor, park)
        return random.choice(rides) if rides else None

class PreferenceStrategy(RideChoiceStrategy):
    """
    Weighted by visitor.ride_prefs, only among rides the visitor can legally ride.
    Falls back to random among eligible rides if no prefs match.
    """
    def pick_ride(self, visitor, park):
        rides = _eligible_rides(visitor, park)
        if not rides:
            return None

        prefs = getattr(visitor, "ride_prefs", {})
        preferred = [r for r in rides if r.name in prefs]

        # If we have no preference info, just pick any eligible ride
        if not preferred:
            return random.choice(rides)

        # Weighted random based on preferences
        weights = [prefs.get(r.name, 1.0) for r in preferred]
        return random.choices(preferred, weights=weights, k=1)[0]