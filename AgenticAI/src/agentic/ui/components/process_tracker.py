"""Process tracking component"""

import streamlit as st
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProcessStats:
    start_time: float
    tokens_used: int = 0
    estimated_cost: float = 0.0


class ProcessTracker:
    def __init__(self):
        self.current_process = ""

    def start_process(self, process_name: str):
        """Start tracking a new process"""
        self.current_process = process_name

    def show_summary(self, tokens: int = 0, cost: float = 0.0):
        """Show process summary"""
        self.current_process = (
            f"Käsitelty {tokens} tokenia (arvioitu kustannus: ${cost:.4f})"
        )
