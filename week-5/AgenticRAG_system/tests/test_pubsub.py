import unittest
from AgenticRAG_system.messaging.pubsub import PubSubSystem


class TestPubSubSystem(unittest.TestCase):
    def setUp(self):
        self.pubsub = PubSubSystem()

    def test_subscribe_and_publish(self):
        # Testidata
        test_data = {"message": "test"}
        received_data = []

        # Callback-funktio
        def callback(data):
            received_data.append(data)

        # Testaa tilausta ja julkaisua
        self.pubsub.subscribe("test_event", callback)
        self.pubsub.publish("test_event", test_data)

        self.assertEqual(len(received_data), 1)
        self.assertEqual(received_data[0], test_data)

    def test_unsubscribe(self):
        received_data = []

        def callback(data):
            received_data.append(data)

        self.pubsub.subscribe("test_event", callback)
        self.pubsub.unsubscribe("test_event", callback)
        self.pubsub.publish("test_event", {"message": "test"})

        self.assertEqual(len(received_data), 0)
