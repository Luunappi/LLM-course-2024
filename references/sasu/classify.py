# LLM Memory (DDMMem) part of the MemoryFormer architecture
# Note this is experimental POC code


from dynamicDistLLMMemory import DynamicDistLLMMemory


instruction_text = [
    {"command": "SUBSCRIBE", "event": "event", "anchor": "event", "replace": True},
    {
        "command": "LLM-CLASSIFY",
        "prompt": "Classify the input event to destinations: packet loss, latency and throughput are the destinations.",
        "anchor": "KPI_Packetloss KPI_Latency KPI_Throughput",
        "scope": "event",
        "model": "ollama/llama3.1:70b",
    },
    {
        "command": "LLM-TRIGGER",
        "event": "event",
        "prompt": "Re-evaluate the latency values and write update latency part for the analysis. If there is no input data output nothing. ",
        "anchor": "KPI_Latency_Analysis",
        "scope": "KPI_Latency",
    },
    {
        "command": "LLM-TRIGGER",
        "event": "event",
        "prompt": "Re-evaluate the packet loss values and write update to this part of the analysis. If there is no input data output nothing.",
        "anchor": "KPI_Packetloss_Analysis",
        "scope": "KPI_Packetloss",
    },
    {
        "command": "LLM-TRIGGER",
        "event": "event",
        "prompt": "Re-evaluate the throughput values and write update to this part of the analysis. If there is no input data output nothing.",
        "anchor": "KPI_Throughput_Analysis",
        "scope": "KPI_Throughput",
    },
    {
        "command": "LLM-CONTENT-TRIGGER",
        "prompt": "Re-evaluate the overall network slice status and write detailed analysis. If there is no input data output nothing.",
        "anchor": "KPI_Analysis",
        "scope": "KPI_Latency_Analysis KPI_Throughput_Analysis KPI_Packetloss_Analysis",
    },
]

contents_text = {
    "KPI_Packetloss": "",
    "KPI_Latency": "",
    "KPI_Throughput": "",
    "KPI_PacketLoss_Analysis": "",
    "KPI_Latency_Analysis": "",
    "KPI_Throughput_Analysis": "",
    "KPI_Overall_Analysis": "",
}


# add publish memory result feature, can be a parameter

# Define the memory instance
memory = DynamicDistLLMMemory(instruction_text, contents_text)

# Initialize memory and subscribe
memory.execute_instruction_init("")

# React to an event
event_name = "event"
event_data = {"Packetloss": "0.4", "Summary": "Packet loss event. Slice A."}
memory.react_to_event(event_name, event_data)

event_name = "event"
event_data = {"Latency": "0.1", "Summary": "Latency event. Slice B."}
memory.react_to_event(event_name, event_data)

event_name = "event"
event_data = {"Packetloss": "0.2", "Summary": "Packet loss event. Slice C."}
memory.react_to_event(event_name, event_data)

print("-----------------------------")
print(memory.get_contents())
print("-----------------------------")

print("Context:KPI_PacketLoss")
context = memory.getContext("KPI_PacketLoss")
print(context)
print("Context:KPI_Analysis")
context = memory.getContext("KPI_Analysis")
print(context)

print("-----------------------------")
print("Partitioning memory for offloading:")
bundle = memory.detect_bundles()
print(bundle)
