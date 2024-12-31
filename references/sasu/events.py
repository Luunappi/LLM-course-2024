import zmq
import threading
import pickle
import time


class EventBroker:
    """
    EventBroker toimii tapahtumavälittäjänä hajautetussa järjestelmässä.
    Toteuttaa publish-subscribe -mallin ZMQ:n avulla.
    """

    def __init__(self):
        # Alustetaan ZMQ konteksti ja ROUTER-socket viestien välitykseen
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.bind("tcp://*:5555")  # Sidotaan socket porttiin 5555

        # Sanakirja tilaajien hallintaan: {event_type: set(client_ids)}
        self.subscribers = {}
        self.running = True

    def get_context(self):
        """Palauttaa ZMQ kontekstin muiden komponenttien käyttöön"""
        return self.context

    def run(self):
        """
        Pääsilmukka viestien vastaanottamiseen ja käsittelyyn.
        Käsittelee SUBSCRIBE, UNSUBSCRIBE ja EVENT -tyyppisiä viestejä.
        """
        print("Server started, waiting for messages...")
        try:
            while self.running:
                try:
                    # Alustetaan poller viestien vastaanottoa varten
                    poller = zmq.Poller()
                    poller.register(self.socket, zmq.POLLIN)
                    socks = dict(poller.poll(1000))  # 1000ms timeout

                    if self.socket in socks and socks[self.socket] == zmq.POLLIN:
                        # Vastaanotetaan viesti osissa: client_id, tyhjä kehys, data
                        message = self.socket.recv_multipart()
                        client_id, empty, command = message
                        client_id_str = client_id.decode()
                        parts = command.split(b"|")
                        cmd_type = parts[0].decode()

                        print(f"Received {cmd_type} from client {client_id_str}")

                        # Käsitellään eri viestityypit
                        if cmd_type == "SUBSCRIBE":
                            # Lisätään uusi tilaaja tapahtumalle
                            event_type = parts[1].decode()
                            self.subscribers.setdefault(event_type, set()).add(
                                client_id
                            )
                            reply = f"Client{client_id_str} subscribed to {event_type}"
                            print(f"SENDING response {reply}")
                            self.socket.send(client_id, zmq.SNDMORE)
                            self.socket.send_string(reply)
                            print(f"Client {client_id_str} subscribed to {event_type}")

                        elif cmd_type == "UNSUBSCRIBE":
                            # Poistetaan tilaaja tapahtumalta
                            event_type = parts[1].decode()
                            if (
                                event_type in self.subscribers
                                and client_id in self.subscribers[event_type]
                            ):
                                self.subscribers[event_type].remove(client_id)
                                reply = f"Client{client_id_str} unsubscribed to {event_type}"
                                self.socket.send(client_id, zmq.SNDMORE)
                                self.socket.send_string(reply)
                                print(
                                    f"Client {client_id_str} unsubscribed from {event_type}"
                                )

                        elif cmd_type == "EVENT":
                            # Käsitellään ja välitetään tapahtuma tilaajille
                            event_type = parts[1].decode()
                            data = pickle.loads(parts[2])
                            self.broadcast_event(event_type, data)
                            reply = f"Event {event_type} broadcasted"
                            self.socket.send(client_id, zmq.SNDMORE)
                            self.socket.send_string(reply)
                            print(f"Event {event_type} broadcasted with data {data}")
                    else:
                        print("No messages received in the last second")
                except zmq.ZMQError as e:
                    print(f"ZMQ Error: {e}")
        except Exception as e:
            print(f"Unexpected error in server run loop: {e}")
        finally:
            # Suljetaan socket ja konteksti hallitusti
            self.socket.close()
            self.context.term()
            print("Server context terminated")

    def broadcast_event(self, event_type, data):
        """
        Lähettää tapahtuman kaikille sen tilanneille asiakkaille.

        Args:
            event_type: Tapahtuman tyyppi
            data: Tapahtuman data
        """
        if event_type in self.subscribers:
            message = pickle.dumps((event_type, data))
            for client_id in self.subscribers[event_type]:
                self.socket.send_multipart([client_id, b"", message])
                print(f"Broadcasted event {event_type} to client {client_id.decode()}")

    def stop(self):
        """Pysäyttää event brokerin toiminnan"""
        self.running = False


if __name__ == "__main__":
    # Testataan event brokeria
    event_broker = EventBroker()
    event_broker_thread = threading.Thread(target=event_broker.run)
    event_broker_thread.start()

    # Odotetaan että palvelin käynnistyy
    time.sleep(1)
