import sys
import unittest
from PyQt6 import QtWidgets
from core.events import Event, EventType
from core.event_bus import EventBus
from hud.hud_window import SASHUDWindow

class TestHUDWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QApplication instance if not present
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    def setUp(self):
        EventBus._instance = None
        self.bus = EventBus()
        self.hud = SASHUDWindow(bus=self.bus)

    def tearDown(self):
        self.hud.close()
        self.bus.stop()
        EventBus._instance = None

    def test_hud_initialization_and_events(self):
        self.assertIsNotNone(self.hud)
        # Test event emission to HUD
        self.bus.publish(Event(
            event_type=EventType.GESTURE_STATE_CHANGED,
            payload={"state": "ACTIVE", "hand": "Right"}
        ))
        QtWidgets.QApplication.processEvents()
        self.assertEqual(self.hud.status_pill.text(), "ONLINE")

if __name__ == '__main__':
    unittest.main()
