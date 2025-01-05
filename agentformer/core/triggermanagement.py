"""
Trigger Management for AgentFormer
Handles event triggers and their execution
"""


class TriggerManagement:
    def __init__(self):
        self.triggers = {}
        self.active_triggers = set()

    def add_trigger(self, name, condition, action):
        """Add new trigger"""
        self.triggers[name] = {"condition": condition, "action": action, "active": True}

    def check_triggers(self, state):
        """Check and execute active triggers"""
        for name, trigger in self.triggers.items():
            if trigger["active"] and trigger["condition"](state):
                trigger["action"](state)
                self.active_triggers.add(name)

    def deactivate_trigger(self, name):
        """Deactivate specific trigger"""
        if name in self.triggers:
            self.triggers[name]["active"] = False
            self.active_triggers.discard(name)
