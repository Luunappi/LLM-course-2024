"""System monitoring tool for AgentFormer"""

import logging
from typing import Dict, List, Any
from dataclasses import dataclass
from time import time

logger = logging.getLogger(__name__)


@dataclass
class TimingStep:
    step: str
    time: float
    details: Dict[str, Any] = None


class SystemTool:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemTool, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = True
            self._current_session = {
                "start_time": time(),
                "steps": [],
                "model_used": None,
                "total_time": 0,
            }
            logger.debug("SystemTool initialized")

    def start_timing(self) -> None:
        """Start new timing session"""
        self._current_session = {
            "start_time": time(),
            "steps": [],
            "model_used": None,
            "total_time": 0,
        }

    def add_step(
        self, step: str, duration: float, details: Dict[str, Any] = None
    ) -> None:
        """Add timing step"""
        self._current_session["steps"].append(
            TimingStep(step=step, time=duration, details=details)
        )
        logger.debug(f"Added timing step: {step} - {duration:.2f}s")

    def set_model(self, model: str) -> None:
        """Set model used for current session"""
        self._current_session["model_used"] = model

    def end_timing(self) -> None:
        """End timing session and calculate total"""
        self._current_session["total_time"] = (
            time() - self._current_session["start_time"]
        )

    def get_timing_stats(self) -> Dict[str, Any]:
        """Get current timing statistics"""
        return {
            "steps": [
                {"step": step.step, "time": step.time, "details": step.details}
                for step in self._current_session["steps"]
            ],
            "total_time": self._current_session["total_time"],
            "model_used": self._current_session["model_used"],
        }
