import socket
import threading
import traceback
import json

ADDME = "JOIN"
PING = "PING"
GIVENAME = "NAME"
PEERLIST = "LIST"
TRANSACTION = "CASH"
REQUESTCHAIN = "BLOB"
REPLY = "REPL"
ERROR = "ERRO"


class Peer:
    def __init__(self, maxpeers, myid, serverport, peerhost: str, peerport: int, serverhost=None):
        """Initialises a peer node
        :param maxpeers: <int> Maximum number of peers that the node will maintain
        :param myid: <str> Canonical identifier of the node
        :param serverport: <int> Port on which the node listens for connections
        :param serverhost: <str>"""
        self.maxpeers = maxpeers
        self.serverport = serverport

        if serverhost:
            self.serverhost = serverhost
        else:
            self.serverhost = socket.gethostbyname(socket.gethostname())

        if myid:
            self.myid = myid
        else:
            self.myid = f"{self.serverhost}:{self.serverport}"

        self.shutdown = False
        self.peerlock = threading.Lock
        self.peers = {}
        self.handlers = {"JOIN": self.handle_addme,
                         "PING": self.handle_ping,
                         "NAME": self.handle_givename,
                         "LIST": self.handle_peerlist,
                         "CASH": self.handle_transaction,
                         "BLOB": self.handle_requestchain}

        self.mainloop(peerhost, peerport)

    def mainloop(self, peerhost, peerport):
        """Continuous loop accepting connections. When an incoming connection is accepted, the method handle_peer is
        called to handle communication with this connection on a new thread"""
        s = self.makesocket(self.serverport)
        s.settimeout(10)
        print(f"Server started: {self.myid}")

        while not self.shutdown:
            try:
                # Client socket is distinct from the listening socket
                print("Listening for connections...")
                client_sock, client_add = s.accept()
                client_sock.settimeout(None)
                t = threading.Thread(target=self.handlepeer, args=[client_sock])
                t.start()
            except:
                print("Exception in Peer.mainloop():")
                traceback.print_exc()

        print("Main loop exiting...")
        print("Side loop exiting...")
        s.close()

    def makesocket(self, port, backlog=5):
        """Server-side operations: sets up a socket which listens for incoming connections from other peers"""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', port))
        s.listen(backlog)
        return s

    def sideloop(self, peerhost, peerport):
        while len(self.peers) < self.maxpeers or self.maxpeers == 0:
            self.buildpeers(peerhost, peerport)
        print("Maximum number of peers reached")

    def handlepeer(self, client_sock):
        """Takes a newly formed connection, processes the request, and dispatches the request to an appropriate
        handler for processing"""
        print(f"New child {threading.currentThread().getName()}")
        print(f"Connected {client_sock.getpeername()}")
        host, port = client_sock.getpeername()
        peercon = Connection(None, host, port, client_sock, debug=False)
        try:
            msgtype, msgdata = peercon.received()
            if msgtype in self.handlers:
                print(f"Handling peer message: {msgtype}: {msgdata}")
                self.handlers[msgtype](peercon, msgdata)
            else:
                print(f"{msgtype}: {msgdata}")
        except:
            print("Exception in Peer.handlepeer():")
            traceback.print_exc()

    def findpeer(self, peerhost, peerport):
        try:
            _, peerid = self.sendpeer(peerhost, peerport, GIVENAME, '')
            print(f"Connection to {peerid} established")
            self.addpeer(peerhost, peerport, peerid)
            self.status = False
            return self.status
        except:
            print("Exception in Peer.findpeer():")
            traceback.print_exc()
            return True

    def buildpeers(self, peerhost, peerport, depth=4):
        if depth:
            try:
                _, peerjson =  self.sendpeer(peerhost, peerport, PEERLIST, '')
                peerdict = json.loads(peerjson)
                for nextpeer, data in peerdict:
                    if nextpeer not in self.peers and nextpeer != self.myid:
                        nexthost, nextport = data
                        self.addpeer(nextpeer, nexthost, nextport)
                        self.buildpeers(nexthost, nextport, depth-1)
            except:
                print("Exception in Peer.buildpeers():")
                traceback.print_exc()

    def sendpeer(self, host, port, msgtype, msgdata, peerid=None):
        replies = []
        try:
            peercon = Connection(peerid, host, port)
            sent = peercon.send(msgtype, msgdata)
            if sent:
                print(f"Request type {msgtype} sent. Waiting for reply...")
                reply = peercon.received()
                print(reply)
                while reply != (None, None):
                    replies.append(reply)
                    print(f"Received reply from {peerid}: {reply}")
            peercon.close()
        except:
            print("Exception in Peer.sendpeer():")
            traceback.print_exc()
        return replies

    def addpeer(self, peerid, host, port):
        """Adds peer name and host:port mapping to the known list of peers"""
        self.peers[peerid] = (host, port)
        print(f"{peerid} has been added")
        print(f"Requesting {peerid} to add me...")
        me = (self.myid, self.serverhost, self.serverport)
        self.sendpeer(host, port, ADDME, me)
        return True

    def handle_addme(self, peercon, data):
        if self.maxpeers == 0 or self.maxpeers > len(self.peers):
            peerid, host, port = data
            answer = self.addpeer(peerid, host, port)
            if answer:
                peercon.send(REPLY, f"{peerid} has been added")
        else:
            print("Maximum number of peers reached")
            peercon.send(ERROR, f"Maximum number of peers reached")

    def handle_ping(self, peercon, data):
        del data
        peercon.send(REPLY, "PONG")

    def handle_givename(self, peercon, data):
        del data
        peercon.send(REPLY, self.myid)

    def handle_peerlist(self, peercon, data):
        del data
        peercon.send(REPLY, self.peers)

    def handle_transaction(self, peercon, data):
        pass

    def handle_requestchain(self, peercon, data):
        pass


class Connection:
    def __init__(self, peerid, host, port, sock=None, debug=False):
        self.id = peerid
        self.debug = debug
        if not sock:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((host, port))
        else:
            self.s = sock

    def send(self, msgtype, msgdata):
        try:
            msgjson = json.dumps((msgtype, msgdata))
            self.s.send(bytes(msgjson, encoding='utf-8'))
            return True
        except:
            print("Exception in Connection.send():")
            traceback.print_exc()
            return False

    def received(self):
        try:
            fullmsg = ""
            while True:
                message = self.s.recv(1024)
                if len(message) <= 0:
                    break
                fullmsg += message.decode('utf-8')
            msgdata, msgtype = json.loads(fullmsg)
            return msgdata, msgtype
        except:
            print("Exception in Connection.received():")
            traceback.print_exc()
            return None, None

    def close(self):
        """Closes the peer connection"""
        self.s.close()
