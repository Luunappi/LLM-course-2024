"""Debug tool for system monitoring"""

import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class DebugTool:
    def __init__(self):
        self.events = []
        self.max_events = 100

    def add_event(self, level: str, component: str, message: str, details: Dict = None):
        """Add debug event"""
        event = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "component": component,
            "message": message,
            "details": details,
        }
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events.pop(0)

    def get_events(self) -> List[Dict]:
        """Get all events"""
        return self.events

    def get_errors(self) -> List[Dict]:
        """Get error events"""
        return [e for e in self.events if e["level"] == "ERROR"]

    def get_warnings(self) -> List[Dict]:
        """Get warning events"""
        return [e for e in self.events if e["level"] == "WARNING"]

    def clear(self):
        """Clear all events"""
        self.events = []
