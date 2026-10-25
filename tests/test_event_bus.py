import time
import unittest
from core.events import Event, EventType, EventPriority
from core.event_bus import EventBus

class TestEventBus(unittest.TestCase):
    def setUp(self):
        # Reset singleton if needed
        EventBus._instance = None
        self.bus = EventBus(max_queue_size=20)

    def tearDown(self):
        self.bus.stop()
        EventBus._instance = None

    def test_publish_and_subscribe(self):
        received_events = []
        def handler(event: Event):
            received_events.append(event)

        self.bus.subscribe(EventType.GESTURE_CLICK, handler)
        
        evt = Event(
            event_type=EventType.GESTURE_CLICK,
            payload={"button": "left"},
            source="test"
        )
        self.bus.publish(evt)
        
        # Give dispatcher thread a moment to process
        time.sleep(0.1)
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].payload["button"], "left")

    def test_wildcard_subscription(self):
        all_events = []
        def wildcard_handler(event: Event):
            all_events.append(event)

        self.bus.subscribe_all(wildcard_handler)
        
        self.bus.publish(Event(event_type=EventType.SYSTEM_STATUS, payload={"status": "OK"}))
        self.bus.publish(Event(event_type=EventType.WAKE_WORD_DETECTED, payload={"confidence": 0.95}))
        
        time.sleep(0.1)
        self.assertEqual(len(all_events), 2)

    def test_history_buffer(self):
        self.bus.publish(Event(event_type=EventType.SYSTEM_STARTUP, payload={"version": "2.0"}))
        time.sleep(0.1)
        history = self.bus.get_recent_history(count=5)
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[-1]["type"], EventType.SYSTEM_STARTUP.value)

if __name__ == '__main__':
    unittest.main()
