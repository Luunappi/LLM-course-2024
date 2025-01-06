"""Debug tool for AgentFormer

This tool collects and manages debug information from various components.
It provides both terminal output and GUI visualization of debug data.

Features:
- Log collection and filtering
- System state monitoring
- Performance metrics
- Component status tracking
- Error tracking and analysis
"""

import logging
import sys
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)


@dataclass
class DebugEvent:
    timestamp: float
    level: str
    component: str
    message: str
    details: Dict[str, Any] = None


class DebugTool:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DebugTool, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = True
            self._debug_events = []
            self._setup_logging()
            logger.debug("DebugTool initialized")

    def _setup_logging(self):
        """Setup custom logging handler"""

        class DebugToolHandler(logging.Handler):
            def __init__(self, debug_tool):
                super().__init__()
                self.debug_tool = debug_tool

            def emit(self, record):
                self.debug_tool.add_event(
                    level=record.levelname,
                    component=record.name,
                    message=record.getMessage(),
                    details={"exc_info": record.exc_info if record.exc_info else None},
                )

        # Add handler to root logger
        logging.getLogger().addHandler(DebugToolHandler(self))

    def add_event(self, level: str, component: str, message: str, details: Dict = None):
        """Add new debug event"""
        event = DebugEvent(
            timestamp=datetime.now().timestamp(),
            level=level,
            component=component,
            message=message,
            details=details,
        )
        self._debug_events.append(event)
        # Print to terminal if it's an error or warning
        if level in ["ERROR", "WARNING"]:
            print(f"[{level}] {component}: {message}", file=sys.stderr)

    def get_debug_info(self) -> Dict[str, Any]:
        """Get all debug information for GUI display"""
        return {
            "events": [
                {
                    "timestamp": datetime.fromtimestamp(e.timestamp).strftime(
                        "%H:%M:%S"
                    ),
                    "level": e.level,
                    "component": e.component,
                    "message": e.message,
                    "details": e.details,
                }
                for e in self._debug_events[-50:]  # Last 50 events
            ],
            "stats": {
                "total_events": len(self._debug_events),
                "error_count": sum(1 for e in self._debug_events if e.level == "ERROR"),
                "warning_count": sum(
                    1 for e in self._debug_events if e.level == "WARNING"
                ),
                "components": list(set(e.component for e in self._debug_events)),
            },
        }

    def clear_events(self):
        """Clear all debug events"""
        self._debug_events = []
