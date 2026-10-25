import queue
import threading
import time
from collections import deque
from typing import Callable, Dict, List, Set
from core.events import Event, EventType, EventPriority

class EventBus:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, max_queue_size: int = 500):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._init_bus(max_queue_size)
            return cls._instance

    def _init_bus(self, max_queue_size: int):
        self._subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._wildcard_subscribers: List[Callable[[Event], None]] = []
        self._sub_lock = threading.RLock()
        
        # Bounded event queue to handle backpressure
        self._queue = queue.Queue(maxsize=max_queue_size)
        self._history = deque(maxlen=150) # Rolling audit buffer
        
        self._running = True
        self._dispatcher_thread = threading.Thread(
            target=self._dispatch_loop,
            name="EventBusDispatcher",
            daemon=True
        )
        self._dispatcher_thread.start()

    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        """Subscribe a callable handler to a specific EventType."""
        with self._sub_lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if handler not in self._subscribers[event_type]:
                self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Callable[[Event], None]):
        """Subscribe a handler to all events (wildcard for telemetry/HUD)."""
        with self._sub_lock:
            if handler not in self._wildcard_subscribers:
                self._wildcard_subscribers.append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        """Unsubscribe a handler from a specific EventType."""
        with self._sub_lock:
            if event_type in self._subscribers and handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)

    def publish(self, event: Event) -> bool:
        """
        Publish an event to the bus.
        Non-blocking with intelligent backpressure for high-frequency events.
        """
        if not self._running:
            return False

        try:
            # If pointer movement queue is full, drop older pointer frames (lossy OK for cursor coords)
            if event.event_type == EventType.GESTURE_POINTER_MOVE and self._queue.full():
                try:
                    self._queue.get_nowait() # Discard oldest to preserve low-latency
                except queue.Empty:
                    pass
            self._queue.put_nowait(event)
            return True
        except queue.Full:
            print(f"[EventBus Warning] Queue full! Dropping event {event.event_type.value}")
            return False

    def _dispatch_loop(self):
        while self._running:
            try:
                event: Event = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            with self._sub_lock:
                self._history.append(event)
                handlers_to_call = list(self._subscribers.get(event.event_type, []))
                wildcard_handlers = list(self._wildcard_subscribers)

            for handler in handlers_to_call + wildcard_handlers:
                try:
                    handler(event)
                except Exception as e:
                    print(f"[EventBus Handler Error] in {handler.__name__ if hasattr(handler, '__name__') else handler}: {e}")
                    
            self._queue.task_done()

    def get_recent_history(self, count: int = 50) -> List[Dict]:
        """Returns the most recent events for HUD telemetry."""
        with self._sub_lock:
            return [e.to_dict() for e in list(self._history)[-count:]]

    def stop(self):
        """Clean shutdown of the event bus."""
        self._running = False
        if self._dispatcher_thread.is_alive():
            self._dispatcher_thread.join(timeout=1.0)
