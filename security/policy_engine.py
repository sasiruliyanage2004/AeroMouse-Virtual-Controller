import time
from enum import Enum, auto
from typing import Dict, Any, Tuple, Optional

class ActionRiskLevel(Enum):
    READ_ONLY = auto()       # Time, screen reading, active window inspection
    SAFE_ACTION = auto()     # Volume, search, launching benign apps
    CONSEQUENTIAL = auto()   # Sending email, locking PC, window closing, modifications
    CRITICAL = auto()        # File deletion, terminal shell scripts

class SecurityPolicyEngine:
    def __init__(self, require_confirmation_for_consequential: bool = False):
        self.require_confirmation = require_confirmation_for_consequential
        self.audit_log = []

        # Tool name to risk mapping
        self.tool_risk_map = {
            "get_current_time_date": ActionRiskLevel.READ_ONLY,
            "inspect_active_screen": ActionRiskLevel.READ_ONLY,
            "get_active_window_info": ActionRiskLevel.READ_ONLY,
            "search_web": ActionRiskLevel.SAFE_ACTION,
            "play_youtube": ActionRiskLevel.SAFE_ACTION,
            "launch_application": ActionRiskLevel.SAFE_ACTION,
            "open_website": ActionRiskLevel.SAFE_ACTION,
            "control_volume": ActionRiskLevel.SAFE_ACTION,
            "send_or_compose_email": ActionRiskLevel.CONSEQUENTIAL,
            "lock_workstation": ActionRiskLevel.CONSEQUENTIAL,
            "close_window": ActionRiskLevel.CONSEQUENTIAL,
        }

    def evaluate_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Evaluates whether a tool call is authorized to execute.
        Returns: (is_authorized: bool, reason: str)
        """
        risk = self.tool_risk_map.get(tool_name, ActionRiskLevel.CONSEQUENTIAL)

        # Log policy evaluation attempt
        entry = {
            "timestamp": time.time(),
            "tool": tool_name,
            "risk": risk.name,
            "args": {k: str(v)[:100] for k, v in arguments.items()} # Redact overly long inputs
        }

        if risk == ActionRiskLevel.CRITICAL:
            entry["authorized"] = False
            self.audit_log.append(entry)
            return False, "Action rejected: Critical actions are disabled in autonomous mode."

        if risk == ActionRiskLevel.CONSEQUENTIAL and self.require_confirmation:
            entry["authorized"] = False
            self.audit_log.append(entry)
            return False, f"Action '{tool_name}' requires explicit confirmation."

        entry["authorized"] = True
        self.audit_log.append(entry)
        return True, "Authorized"

    def record_result(self, tool_name: str, success: bool, outcome: str):
        if self.audit_log and self.audit_log[-1]["tool"] == tool_name:
            self.audit_log[-1]["success"] = success
            self.audit_log[-1]["outcome"] = outcome[:200]
