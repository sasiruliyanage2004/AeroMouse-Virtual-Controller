import time
import unittest
from core.events import Event, EventType
from core.event_bus import EventBus
from automation.action_executor import ActionExecutor

class TestActionExecutor(unittest.TestCase):
    def setUp(self):
        EventBus._instance = None
        self.bus = EventBus()
        self.executor = ActionExecutor(bus=self.bus)

    def tearDown(self):
        self.executor.stop()
        self.bus.stop()
        EventBus._instance = None

    def test_executor_event_queueing(self):
        # Publish pointer and click events
        self.bus.publish(Event(
            event_type=EventType.GESTURE_POINTER_MOVE,
            payload={"coords": (0.5, 0.5)}
        ))
        self.bus.publish(Event(
            event_type=EventType.GESTURE_CLICK,
            payload={"button": "left"}
        ))
        
        # Give worker a brief moment to process
        time.sleep(0.15)
        # Executor runs without exceptions
        self.assertTrue(self.executor._running)

if __name__ == '__main__':
    unittest.main()
