# strategies.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
import random
from ride import Ride

class RideChoiceStrategy(ABC):
    @abstractmethod
    def pick_ride(self, visitor, park) -> Optional["Ride"]:
        """Return the chosen Ride (or None if no ride is available)."""
        ...

class RandomStrategy(RideChoiceStrategy):
    """Pure random choice among operational rides."""
    def pick_ride(self, visitor, park):
        rides = [r for r in park.get_rides() if r.is_operational()]
        return random.choice(rides) if rides else None

class PreferenceStrategy(RideChoiceStrategy):
    """
    Weighted by visitor.ride_prefs.
    Falls back to random among operational rides if no prefs match.
    """
    def pick_ride(self, visitor, park):
        rides = [r for r in park.get_rides() if r.is_operational()]
        if not rides:
            return None

        prefs = getattr(visitor, "ride_prefs", {})
        preferred = [r for r in rides if r.name in prefs]

        # If we have no preference info, just pick any operational ride
        if not preferred:
            return random.choice(rides)

        # Weighted random based on preferences
        weights = [prefs.get(r.name, 1.0) for r in preferred]
        return random.choices(preferred, weights=weights, k=1)[0]
