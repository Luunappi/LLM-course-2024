from events import EventBroker
from dynamicDistLLMMemory import DynamicDistLLMMemory
import threading
import json
import requests
import pickle
import asyncio
import zmq
import time


class AsyncMessageReceiver:
    def __init__(self, node_id, socket, context):
        self.context = context
        self.node_id = node_id
        self.socket = socket

        # Poller to handle incoming messages
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.running = True
        self.thread = threading.Thread(target=self.receive_messages)
        self.thread.start()

    def receive_messages(self):
        print("Receiving messages")
        while self.running:
            socks = dict(self.poller.poll(timeout=1000))  # Timeout in milliseconds
            if self.socket in socks and socks[self.socket] == zmq.POLLIN:
                message = self.socket.recv()
                self.handle_message(message)
            time.sleep(0.1)

    def handle_message(self, message):
        # Process the received message
        print(f"Received message: {message}")

    def stop(self):
        self.running = False
        self.thread.join()



instruction_text = [
  {"command": "SUBSCRIBE", "query": "EVENT_A", "anchor": "KPI_PacketLoss"},
  {"command": "SUBSCRIBE", "query": "PacketLoss1", "anchor": "KPI_PacketLoss"},
  {"command": "SUBSCRIBE", "query": "PacketLoss2", "anchor": "KPI_PacketLoss"},
  {"command": "SUBSCRIBE", "query": "PacketLoss3", "anchor": "KPI_PacketLoss"},
  {"command": "WINDOW", "limit": 100, "scope":"KPI_PacketLoss"},
  {"command": "LLM-TRIGGER", "query": "PacketLoss1", "prompt" : "Evaluate the packet loss for the network slices. Stop evaluation if there is no data. Be compact. Only output analysis.", "anchor": "KPI_Analysis", "scope":"KPI_PacketLoss"},
  {"command": "LLM-TRIGGER", "query": "PacketLoss2", "prompt" : "Evaluate the packet loss for the network slices. Stop evaluation if there is no data. Be compact. Only output analysis.", "anchor": "KPI_Analysis", "scope":"KPI_PacketLoss"},
  {"command": "LLM-TRIGGER", "query": "PacketLoss3", "prompt" : "Evaluate the packet loss for the network slices. Stop evaluation if there is no data. Be compact. Only output analysis.", "anchor": "KPI_Analysis", "scope":"KPI_PacketLoss"},
]

contents_text = {
  "KPI_PacketLoss": "",
  "KPI_Analysis": ""
}

node_id = "node3"
context = zmq.Context()
address = "tcp://localhost:5555"
socket = context.socket(zmq.DEALER)
socket.setsockopt_string(zmq.IDENTITY, str(node_id))
socket.connect(address)


def send_command_to_server(cmd_type, event_type, data=None):
    try:
        if data is not None:
            data_bytes = pickle.dumps(data)
            command = f"{cmd_type}|{event_type}|".encode() + data_bytes
        else:
            command = f"{cmd_type}|{event_type}".encode()
        print(f"Client {node_id} sending command: {cmd_type} {event_type}")
        socket.send_multipart([b'', command])
      
        print("SENT MESSAGE")
        
        # Poll for the reply with a timeout
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        socks = dict(poller.poll(100))  
      
        if socket in socks:
            reply = socket.recv()
            if len(reply) >= 3:
                print(f"Client {node_id} received reply: {reply}")
            else:
                print(f"Client {node_id} received an incomplete reply:{reply}")
        else:
            print(f"Client {node_id} did not receive a reply in time")
    except zmq.ZMQError as e:
        print(f"Client {node_id} ZMQ Error in send_command: {e}")
    except Exception as e:
        print(f"Unexpected error in send_command: {e}")


def on_send(self, id, command, message):
    print(f"Sent message from {id}: {message}")
    send_command_to_server(command, message, None)
    
def on_receive(self, id, message):
    print(f"Received message from {id}: {message}")

def main():

    receiver = AsyncMessageReceiver(node_id, socket, context)

    # Wait for the server to initialize
    time.sleep(1)

    node1 = DynamicDistLLMMemory(instruction_text, contents_text,"node1",on_send, on_receive)
    print("Starting memory")
    # Initialize memory and subscribe
    node1.execute_instruction_init('')

    node2 = DynamicDistLLMMemory(instruction_text, contents_text,"node2",on_send, on_receive)
    print("Starting memory")
    # Initialize memory and subscribe
    node2.execute_instruction_init('')

    # Initialize memory and subscribe
    #node2.execute_instruction_init('')
    
    print("Publishing event")
    send_command_to_server('EVENT','EVENT_A', 'Sample data')
      
    print(node1.contents)
    time.sleep(5000)


# Clean up context
    node1.terminate()
    context.term()

if __name__ == "__main__":
    asyncio.run(main())