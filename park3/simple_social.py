"""
Simplified Social System - Groups Only
======================================
Just tracks pre-formed groups (families, friends)
Speicifies the group behaviour coordinator, group manager, and location tracker.
"""

import threading
from typing import Set, Optional, List
from enum import Enum
from collections import defaultdict


# Location Tracking 

class Location(Enum):
    """Possible locations in the park"""
    ENTRANCE = "entrance"
    RIDE = "ride"
    FOOD = "food"
    MERCH = "merch"
    BATHROOM = "bathroom"
    WANDERING = "wandering"

class LocationTracker:
    """Tracks where each visitor is located"""
    def __init__(self):
        self._lock = threading.Lock()
        self._visitor_locations = {}  # visitor_id -> (location_type, location_name)
        
    def update_location(self, visitor_id: int, location_type: Location, location_name: str):
        """Update a visitor's location"""
        with self._lock:
            self._visitor_locations[visitor_id] = (location_type, location_name)
    
    def get_visitor_location(self, visitor_id: int) -> Optional[tuple]:
        """Get a visitor's current location"""
        with self._lock:
            return self._visitor_locations.get(visitor_id)
    
    def remove_visitor(self, visitor_id: int):
        """Remove a visitor from tracking"""
        with self._lock:
            self._visitor_locations.pop(visitor_id, None)
    
    def get_location_summary(self) -> dict:
        """Get count of visitors at each location"""
        with self._lock:
            summary = defaultdict(int)
            for loc_type, loc_name in self._visitor_locations.values():
                key = f"{loc_type.value}:{loc_name}"
                summary[key] += 1
            return dict(summary)


# Group Management 

class GroupType(Enum):
    """Types of social groups"""
    FAMILY = "family"
    FRIENDS = "friends"
    COUPLE = "couple"

class SocialGroup:
    """Represents a group of visitors traveling together"""
    def __init__(self, group_id: int, group_type: GroupType, member_ids: List[int]):
        self.group_id = group_id
        self.group_type = group_type
        self.members = set(member_ids)
        self.leader_id = member_ids[0]  # First member is leader
        
    def is_leader(self, visitor_id: int) -> bool:
        """Check if visitor is the group leader"""
        return visitor_id == self.leader_id
    
    def size(self) -> int:
        """Get group size"""
        return len(self.members)

class GroupManager:
    """Manages all social groups in the park"""
    def __init__(self):
        self._lock = threading.Lock()
        self._groups = {}  # group_id -> SocialGroup
        self._visitor_to_group = {}  # visitor_id -> group_id
        self._next_group_id = 1
        
        # Track statistics (never cleared, for end-of-sim reporting)
        self._created_groups = []  # List of all groups ever created
        self._total_visitors_in_groups = 0
        
    def create_group(self, group_type: GroupType, member_ids: List[int]) -> int:
        """Create a new social group"""
        with self._lock:
            group_id = self._next_group_id
            self._next_group_id += 1
            
            group = SocialGroup(group_id, group_type, member_ids)
            self._groups[group_id] = group
            
            # Track for statistics (permanent record)
            self._created_groups.append({
                'id': group_id,
                'type': group_type,
                'size': len(member_ids)
            })
            self._total_visitors_in_groups += len(member_ids)
            
            for vid in member_ids:
                self._visitor_to_group[vid] = group_id
                
            return group_id
    
    def get_visitor_group(self, visitor_id: int) -> Optional[SocialGroup]:
        """Get the group a visitor belongs to"""
        with self._lock:
            group_id = self._visitor_to_group.get(visitor_id)
            if group_id is None:
                return None
            return self._groups.get(group_id)
    
    def get_group_members(self, visitor_id: int) -> Set[int]:
        """Get all member IDs in this visitor's group"""
        group = self.get_visitor_group(visitor_id)
        if group is None:
            return {visitor_id}
        return group.members.copy()
    
    def is_group_leader(self, visitor_id: int) -> bool:
        """Check if visitor is their group's leader"""
        group = self.get_visitor_group(visitor_id)
        if group is None:
            return True  # Solo visitors lead themselves
        return group.is_leader(visitor_id)
    
    def is_in_group(self, visitor_id: int) -> bool:
        """Check if visitor is part of a group"""
        group = self.get_visitor_group(visitor_id)
        return group is not None and group.size() > 1
    
    def remove_visitor(self, visitor_id: int):
        """Remove visitor from tracking"""
        with self._lock:
            if visitor_id in self._visitor_to_group:
                group_id = self._visitor_to_group[visitor_id]
                if group_id in self._groups:
                    self._groups[group_id].members.discard(visitor_id)
                    if len(self._groups[group_id].members) == 0:
                        del self._groups[group_id]
                del self._visitor_to_group[visitor_id]
    
    def get_statistics(self) -> dict:
        """Get statistics about groups"""
        with self._lock:
            # Use permanent records, not current active groups
            group_sizes = defaultdict(int)
            for group_info in self._created_groups:
                group_sizes[group_info['size']] += 1
            
            group_types = defaultdict(int)
            for group_info in self._created_groups:
                group_types[group_info['type'].value] += 1
            
            return {
                'total_groups': len(self._created_groups),
                'total_visitors_in_groups': self._total_visitors_in_groups,
                'group_size_distribution': dict(group_sizes),
                'group_types': dict(group_types),
                'active_groups': len(self._groups)  # Currently active
            }


# Group Behavior Coordinator

class GroupCoordinator:
    """
    Coordinates group behavior - helps groups stay together and make decisions.
    Much simpler than the full social influencer.
    """
    def __init__(self, group_manager, location_tracker):
        self.group_manager = group_manager
        self.location_tracker = location_tracker
        
    def should_wait_for_group(self, visitor_id: int) -> bool:
        """
        Check if visitor should wait for group members.
        Only leaders wait, and only if members are scattered.
        """
        # Only check if in a group
        if not self.group_manager.is_in_group(visitor_id):
            return False
        
        # Only leaders coordinate waiting
        if not self.group_manager.is_group_leader(visitor_id):
            return False
        
        # Check how scattered the group is
        group = self.group_manager.get_visitor_group(visitor_id)
        if group is None:
            return False
        
        my_location = self.location_tracker.get_visitor_location(visitor_id)
        if my_location is None:
            return False
        
        # Count how many are at different locations
        members_elsewhere = 0
        for member_id in group.members:
            if member_id == visitor_id:
                continue
            member_loc = self.location_tracker.get_visitor_location(member_id)
            if member_loc != my_location:
                members_elsewhere += 1
        
        # If more than half are elsewhere, wait
        return members_elsewhere > group.size() / 2
    
    def get_group_activity_preference(self, visitor_id: int, activity_choices: list) -> str:
        """
        Get group's preferred activity.
        Non-leaders have high chance of following leader's location.
        """
        # Solo visitors or not in social system
        if not self.group_manager.is_in_group(visitor_id):
            return None
        
        # Leaders choose freely
        if self.group_manager.is_group_leader(visitor_id):
            return None
        
        # Non-leaders: 70% chance to follow leader
        import random
        if random.random() < 0.7:
            group = self.group_manager.get_visitor_group(visitor_id)
            if group:
                leader_loc = self.location_tracker.get_visitor_location(group.leader_id)
                if leader_loc:
                    loc_type, loc_name = leader_loc
                    # If leader is at a ride/food/merch, try to go there
                    if loc_name in activity_choices:
                        return loc_name
        
        return None  # Choose randomly