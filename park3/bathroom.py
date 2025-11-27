import threading
import time
import random
from queue import Queue

class Toilet(threading.Thread):
    """
    A bathroom/toilet facility that serves visitors one at a time.
    Very similar in spirit to FoodTruck: sits in a loop, handles its queue.
    """
    def __init__(self, name, queue: Queue, clock, metrics=None):
        super().__init__(daemon=True)
        self.name = name
        self.queue = queue
        self.clock = clock
        self.metrics = metrics
        self._open = True
        self._lock = threading.Lock()

    def run(self):
        """Main loop: keep serving visitors while the park is running."""
        while self._open and not self.clock.should_stop():
            if self.queue.is_empty():
                # No one waiting – small idle pause
                self.clock.sleep_minutes(random.randint(1, 3))
                continue

            self._serve_next_visitor()

    def _serve_next_visitor(self):
        """Take the next visitor from the queue and let them use the bathroom."""
        with self._lock:
            visitor = self.queue.dequeue_one()
            if visitor is None:
                return

        vid = getattr(visitor, "vid", "unknown")
        print(f"[{self.name}] is occupied by Visitor {vid}")

        # Simulate time spent in bathroom (in sim minutes)
        self.clock.sleep_minutes(random.randint(2, 6))

        print(f"Visitor {vid} has finished using {self.name}")
        if self.metrics is not None and vid != "unknown":
            self.metrics.record_bathroom_visit(
                visitor_id=vid,
                bathroom_name=self.name,
                minute=self.clock.now()
            )

        # If you later want metrics, you could add something like:
        # if self.metrics:
        #     self.metrics.record_bathroom_use(self.name, self.clock.now(), vid)

    def close(self):
        """Close the bathroom."""
        self._open = False

