"""Lightweight local audit logging and export utility for JARVIS Nexus."""

import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from jarvis_nexus.security import redact_secrets


class AuditManager:
    """Manages structured local audit trails for agent actions, protocol runs, and tasks."""

    def __init__(self, log_path: Optional[str] = None) -> None:
        self.log_path = log_path or os.environ.get("JARVIS_AUDIT_LOG", "data/jarvis_audit.json")
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        try:
            d = os.path.dirname(self.log_path)
            if d:
                os.makedirs(d, exist_ok=True)
        except Exception:
            pass

    def record_event(self, event_type: str, action: str, details: Dict[str, Any], status: str = "success") -> Dict[str, Any]:
        """Record an explicit audit event with timestamp and redacted content."""
        env_key = os.getenv("NEBIUS_API_KEY", "")
        def sanitize(val: Any) -> Any:
            if isinstance(val, str):
                s = redact_secrets(val)
                if env_key and len(env_key) > 5 and env_key in s:
                    s = s.replace(env_key, "[REDACTED]")
                return s
            return val

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "event_type": str(event_type),
            "action": sanitize(str(action)),
            "status": str(status),
            "details": {k: sanitize(v) for k, v in details.items()}
        }
        try:
            events = self.get_audit_events()
            events.append(event)
            # Bound audit log to last 500 events
            if len(events) > 500:
                events = events[-500:]
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(events, f, indent=2)
        except Exception as e:
            print(f"Error recording audit event: {e}")
        return event

    def get_audit_events(self) -> List[Dict[str, Any]]:
        """Retrieve all recorded audit events safely."""
        try:
            if os.path.exists(self.log_path):
                with open(self.log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
        except Exception:
            pass
        return []

    def export_json(self) -> str:
        """Export audit trail as a formatted JSON string."""
        events = self.get_audit_events()
        return json.dumps({
            "export_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "total_events": len(events),
            "events": events
        }, indent=2)

    def export_markdown(self) -> str:
        """Export audit trail as a formatted Markdown document."""
        events = self.get_audit_events()
        lines = [
            "# JARVIS Nexus Local Audit Trail",
            f"**Exported At:** {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
            f"**Total Events Recorded:** {len(events)}",
            "",
            "---",
            ""
        ]
        if not events:
            lines.append("*No audit events recorded yet.*")
        else:
            for i, ev in enumerate(events, 1):
                lines.append(f"### {i}. [{ev.get('event_type', 'INFO').upper()}] {ev.get('action', 'Action')}")
                lines.append(f"- **Timestamp:** `{ev.get('timestamp', 'N/A')}`")
                lines.append(f"- **Status:** `{ev.get('status', 'success')}`")
                details = ev.get('details', {})
                if details:
                    lines.append("- **Details:**")
                    for dk, dv in details.items():
                        lines.append(f"  - *{dk}:* `{dv}`")
                lines.append("")
        return "\n".join(lines)
