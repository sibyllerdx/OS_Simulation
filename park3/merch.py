import threading
import random

class MerchStand(threading.Thread):
    """
    A merchandise stand that sells items to visitors one at a time.
    Runs as its own thread, processing its queue continuously.
    """
    def __init__(self, name, queue, clock, metrics=None):
        super().__init__(daemon=True)
        self.name = name
        self.queue = queue          # your Queue instance
        self.clock = clock          # shared Clock
        self.metrics = metrics      # optional Metrics
        self._open = True

        self._lock = threading.Lock()
        self._profit = 0

        # Products and prices (same as your original code)
        self.products = {
            "T-shirt": 20,
            "Hat": 15,
            "Poster": 10,
            "Sticker": 5,
            "Hoodie": 30,
            "Keychain": 7
        }

    def run(self):
        """
        Main loop: similar to deliver_service(festival) from your old code.
        - If queue is empty: wait 1–4 sim minutes.
        - Otherwise: serve one customer via buy_merch().
        """
        while not self.clock.should_stop() and self._open:
            if self.queue.is_empty():
                # No customers right now, wait a bit
                self.clock.sleep_minutes(random.randint(1, 4))
                continue

            # Someone is waiting → sell merch
            self.buy_merch()

    def buy_merch(self):
        with self._lock:
            person = self.queue.dequeue_one()
            if person is None:
                return

            product = random.choice(list(self.products.keys()))
            price = self.products[product]

            # Check money
            if getattr(person, "money", 0) < price:
                # Not enough money → visitor leaves without purchase
                print(f"[{self.name}] Visitor {person.vid} cannot afford a {product} (${price})")
                return

            # Otherwise, complete purchase
            person.money -= price
            self._profit += price

            print(f"[{self.name}] Visitor {person.vid} buys {product} for ${price} "
                  f"(Remaining money: ${person.money})")

            # Metrics
            if self.metrics:
                self.metrics.record_merch_purchase(
                    visitor_id=person.vid,
                    stand_name=self.name,
                    product=product,
                    minute=self.clock.now(),
                    amount=price
                )

        # simulate processing time
        self.clock.sleep_minutes(random.randint(1, 2))


    def get_profit(self):
        """Return total profit from this stand."""
        with self._lock:
            return self._profit

    def close(self):
        """Close the merch stand."""
        self._open = False
