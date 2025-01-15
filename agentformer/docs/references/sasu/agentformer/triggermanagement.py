

class TriggerManager:
    def __init__(self):
        # Initialize the dictionary with empty lists for each query
        self.subscriptionsWithTrigger = {}

    def add_trigger(self, query, instruction):
        # Check if the query already exists in the dictionary
        if query in self.subscriptionsWithTrigger:
            # Append the new instruction to the existing list
            if instruction not in self.subscriptionsWithTrigger[query]:
                self.subscriptionsWithTrigger[query].append(instruction)
        else:
            # Create a new list with the instruction
            self.subscriptionsWithTrigger[query] = [instruction]

    def remove_trigger(self, query, instruction):
        # Check if the query exists in the dictionary
        if query in self.subscriptionsWithTrigger:
            try:
                # Remove the instruction from the list
                self.subscriptionsWithTrigger[query].remove(instruction)
                # If the list becomes empty, remove the query from the dictionary
                if not self.subscriptionsWithTrigger[query]:
                    del self.subscriptionsWithTrigger[query]
            except ValueError:
                print(f"Instruction '{instruction}' not found for query '{query}'")
       
    def get_triggers(self, query):
        # Retrieve the list of instructions for the query
        return self.subscriptionsWithTrigger.get(query, [])

    def has_query(self, query):
        # Check if the query exists in the dictionary
        return query in self.subscriptionsWithTrigger
        