import threading

class Queue:
    """
    Thread-safe queue supporting priority (fast pass) and regular lines.
    Used for rides, food trucks, and any service with waiting lines.
    """
    def __init__(self):
        self.priority = []  # Fast pass holders
        self.regular = []   # Regular visitors
        self.lock = threading.Lock()
        
    def enqueue(self, visitor, priority=False):
        """Add a visitor to the queue"""
        with self.lock:
            if priority:
                self.priority.append(visitor)
            else:
                self.regular.append(visitor)
                
    def add_person(self, person):
        """Alias for enqueue (regular line)"""
        self.enqueue(person, priority=False)
        
    def dequeue_one(self):
        """Remove and return one visitor (priority first)"""
        with self.lock:
            if len(self.priority) > 0:
                return self.priority.pop(0)
            elif len(self.regular) > 0:
                return self.regular.pop(0)
            return None
            
    def pop_first_customer(self):
        """Alias for dequeue_one"""
        return self.dequeue_one()
        
    def dequeue_batch(self, capacity):
        """
        Remove and return a batch of visitors up to capacity.
        Priority visitors go first.
        """
        with self.lock:
            batch = []
            
            # Take all priority visitors first
            while len(self.priority) > 0 and len(batch) < capacity:
                batch.append(self.priority.pop(0))
                
            # Fill remaining capacity with regular visitors
            while len(self.regular) > 0 and len(batch) < capacity:
                batch.append(self.regular.pop(0))
                
            return batch
    
    def size(self):
        """Return total number of visitors in queue"""
        with self.lock:
            return len(self.priority) + len(self.regular)
            
    def length_of_queue(self):
        """Alias for size"""
        return self.size()
        
    def is_empty(self):
        """Check if queue is empty"""
        return self.size() == 0
        
    def check_person_in(self, person):
        """Check if person is still in queue"""
        with self.lock:
            return person in self.priority or person in self.regular