import socket
import threading
import struct
import time


class Peer:
    def __init__(self, max_peers, my_id, server_port, server_host=None):
        """Initialises a peer node
        :param max_peers: <int> Maximum size of the list of known peers that the node will maintain
        :param peer_id: <str> Canonical identifier of the node
        :param server_port: <int> Port on which the node listens for connections
        :param server_host: <str>"""
        self.max_peers = max_peers
        self.server_port = server_port
        self.debug = 0

        if server_host:
            self.server_host = server_host
        else:
            self.server_host = socket.gethostbyname(socket.gethostname())

        if my_id:
            self.my_id = my_id
        else:
            self.my_id = f"{self.server_host}:{self.server_port}"

        self.peers = {}
        self.handlers = {}
        self.router = None
        self.shutdown = False

    # Server-related operations
    def make_socket(self, port, backlog=5):
        """Sets up a socket which listens for incoming connections from other peers"""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', port))
        s.listen(backlog)
        return s

    def main_loop(self):
        """Continuous loop accepting connections. When an incoming connection is accepted, the server will have a new
        socket object used to send and receive data on the connection. The method handle_peer is called to handle
        communication with this connection on a new thread"""
        s = self.make_socket(self.server_port)
        while not self.shutdown:
            client_sock, client_add = s.accept()
            t = threading.Thread(target=self.handle_peer(client_sock))
            t.start()

            self.update_peers()

        s.close()

    def handle_peer(self, client_sock):
        """Takes a newly formed connection, processes the request, and dispatches the request to an appropriate
        handler for processing"""
        print(f"Connected {client_sock.getpeername()}")
        host, port = client_sock.getpeername()
        peercon = Connection(None, host, port, client_sock, debug=False)
        try:
            msg_type, msg_data = peercon.received()
            if msg_type not in self.handlers:
                print(f"Not handled: {msg_type}: {msg_data}")
            else:
                print(f"Handling peer message: {msg_type}: {msg_data}")
                self.handlers[msg_type](peercon, msg_data)
        except:
            pass

    def add_peer(self, peer_id, host, port):
        """Adds a peer name and host:port mapping to the known list of peers"""
        if peer_id not in self.peers and self.max_peers == 0 or self.max_peers > len(self.peers):
            self.peers[peer_id] = (host, port)
            return True
        else:
            return False

    def update_peers(self):
        """Attempts to ping all currently known peers in order to ensure that they are still active. Automatically
        updates the peer list every 60 seconds"""
        for peer_id in self.peers:
            try:
                host, port = self.peers[peer_id]
                peercon = Connection(peer_id, host, port)
                peercon.send('PING', '')
            except:
                if peer_id in self.peers:
                    del self.peers[peer_id]
        time.sleep(60)

    def send_to_peers(self, msg_type, msg_data):
        """Sends blockchain data out to every active peer in the peer list"""
        for peer_id in self.peers:
            try:
                host, port = self.peers[peer_id]
                peercon = Connection(peer_id, host, port)
                peercon.send(msg_type, msg_data)
            except:
                pass


class Connection:
    def __init__(self, peer_id, host, port, sock=None, debug=False):
        self.id = peer_id
        self.debug = debug
        if not sock:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((host, port))
        else:
            self.s = sock
        self.sd = self.s.makefile('rw')

    def received(self):
        """Receives data from a peer connection"""
        try:
            msg_type = self.sd.read(4)
            if not msg_type:
                return None, None
            msg_len = struct.unpack( "!L", self.sd.read(4))[0]
            msg = ""
            while len(msg) != msg_len:
                data = self.sd.read(min(2048, msg_len - len(msg)))
                msg += data
        except:
            return None, None
        return msg_type, msg

    def send(self, msg_type, msg_data):
        """Sends data through a peer connection
        :return: <bool> True on success and False on error"""
        try:
            msg_len = len(msg_data)
            msg = struct.pack(f"!4sL{msg_len}s", msg_type, msg_len, msg_data)
            self.sd.write(msg)
            self.sd.flush()
        except:
            return False
        return True

    def close(self):
        """Closes the peer connection"""
        self.s.close()
        self.s, self.sd = None, None


me = Peer(0, None, 80, None)
print(me.my_id)
me.main_loop()
