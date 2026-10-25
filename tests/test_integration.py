import unittest
import time
from core.events import Event, EventType
from core.event_bus import EventBus
from security.policy_engine import SecurityPolicyEngine, ActionRiskLevel
from perception.screen_context import ScreenContextManager
from automation.action_executor import ActionExecutor

class TestSASIntegration(unittest.TestCase):
    def setUp(self):
        EventBus._instance = None
        self.bus = EventBus()
        self.policy = SecurityPolicyEngine(require_confirmation_for_consequential=True)
        self.screen_mgr = ScreenContextManager(bus=self.bus)
        self.executor = ActionExecutor(bus=self.bus)

    def tearDown(self):
        self.executor.stop()
        self.bus.stop()
        EventBus._instance = None

    def test_security_policy_evaluation(self):
        # Read-only actions must be auto-authorized
        auth, reason = self.policy.evaluate_tool_call("get_current_time_date", {})
        self.assertTrue(auth)
        self.assertEqual(reason, "Authorized")

        # Consequential actions require confirmation if policy set to True
        auth_seq, reason_seq = self.policy.evaluate_tool_call("send_or_compose_email", {"to": "test@test.com"})
        self.assertFalse(auth_seq)
        self.assertIn("confirmation", reason_seq)

    def test_screen_context_active_window(self):
        window_info = self.screen_mgr.get_active_window_info()
        self.assertIn("title", window_info)
        self.assertIn("hwnd", window_info)
        self.assertIsInstance(window_info["title"], str)

    def test_event_bus_multimodal_flow(self):
        received = []
        self.bus.subscribe(EventType.SCREEN_CAPTURED, lambda e: received.append(e))
        
        self.bus.publish(Event(
            event_type=EventType.SCREEN_CAPTURED,
            payload={"window": "TestWindow"}
        ))
        time.sleep(0.1)
        self.assertEqual(len(received), 1)

if __name__ == '__main__':
    unittest.main()
