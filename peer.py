import asyncio
import socket
import ast

sisters = [8888, 8877, 8866, 8855]
peerlist = []


def extract_data(data):
    # Processes the raw data received into a tuple of the form (message type, message)
    decoded = data.decode('utf-8')
    msgtype, message = ast.literal_eval(decoded)
    return msgtype, message


def process_message(msgtype, message):
    # Converts the tuple (message type, message) into a string which can be encoded and sent
    packet = str((msgtype, message))
    encoded = packet.encode('utf-8')
    return encoded


class BlobNode:
    def __init__(self, PORT, HOST=None):
        self.maxpeers = 100
        self.port = PORT
        if not HOST:
            name = socket.gethostname()
            self.host = socket.gethostbyname(name)
        else:
            self.host = HOST
        self.address = None

        asyncio.run(self.main())

    async def main(self):
        server = await asyncio.start_server(self.handle_echo, self.host, self.port)
        self.address = server.sockets[0].getsockname()
        print(f'Serving on {self.address}')

        try:
            await asyncio.gather(*(self.build_peers('127.0.0.1', port) for port in sisters))
        except OSError:
            pass

        async with server:
            await server.serve_forever()

    async def send_echo(self, PEERHOST, PEERPORT, msgtype, message):
        reader, writer = await asyncio.open_connection(PEERHOST, PEERPORT)
        newpeer = (PEERHOST, PEERPORT)

        print(f'Sending message {msgtype!r}: {message!r} to {newpeer!r}...')
        packet = process_message(msgtype, message)
        writer.write(packet)

        data = await reader.read(1024)
        replytype, reply = extract_data(data)
        print(f'Received reply {replytype}: {reply!r} from {newpeer!r}')
        await writer.drain()
        writer.close()

        return replytype, reply

    async def handle_echo(self, reader, writer):
        data = await reader.read(1024)
        msgtype, message = extract_data(data)

        response = Handler(self.maxpeers)
        new_packet = await response.handle_data(data)
        print(f'Received message {msgtype}: {message!r}')
        packet = response.packet

        writer.write(packet)
        print(f'Sending reply...')
        await writer.drain()
        writer.close()

    async def build_peers(self, host, port):
        print(f'Building peers...')
        try:
            if await self.send_echo(host, port, 'PING', self.address):
                newpeer = (host, port)
                if newpeer not in peerlist and len(peerlist) < self.maxpeers:
                    peerlist.append(newpeer)
                    print(f'{host!r}:{port!r} added to peer list')

                _, reply = await self.send_echo(host, port, 'LIST', '')
                replylist = ast.literal_eval(str(reply))
                for peeraddr in replylist:
                    peerhost, peerport = peeraddr
                    if peerhost != self.host or peerport != self.port:
                        try:
                            await self.build_peers(peerhost, peerport)
                        except OSError:
                            pass
        except OSError:
            pass


class Handler:
    def __init__(self, maxpeers, PEERHOST=None, PEERPORT=None):
        self.maxpeers = maxpeers
        self.peerhost = PEERHOST
        self.peerport = PEERPORT
        self.handlers = {'PING': self.ping_check,
                        'LIST': self.list_peers,
                        'CASH': self.transaction,
                        'BLOB': self.request_blobchain,
                        'ERRO': self.flag_error}
        self.packet = None

    async def handle_data(self, data):
        msgtype, message = extract_data(data)
        message = str(message)
        if msgtype in self.handlers:
            await self.handlers[msgtype](message)
        else:
            pass

    async def ping_check(self, message):
        """PING is sent to a peer contact which was not initially in the peer list
        PING includes its message type 'PING' and the sender's contact details, i.e. host and port
        In response, the receiver checks whether the sender is in the peer list, and if not, adds them"""
        self.peerhost, self.peerport = ast.literal_eval(message)
        newpeer = (self.peerhost, self.peerport)

        if newpeer not in peerlist and len(peerlist) < self.maxpeers:
            peerlist.append(newpeer)
            print(f'{self.peerhost!r}:{self.peerport!r} added to peer list')
            replytype, reply = 'REPL', None
            self.packet = process_message(replytype, reply)

        elif newpeer in peerlist:
            print(f'ALERT: {self.peerhost!r}:{self.peerport!r} is already a peer')
            replytype, reply = 'ERRO', 'Request to add was declined, because you are already listed'
            self.packet = process_message(replytype, reply)

        elif len(peerlist) < self.maxpeers:
            print(f'ALERT: peer list has reached its maximum capacity of {self.maxpeers!r}')
            replytype, reply = 'ERRO', 'Request to add was declined, because maximum number of peers has been reached'
            self.packet = process_message(replytype, reply)

    async def list_peers(self, message):
        """Upon receiving LIST, shares the full peer list to the node which made the request"""
        replytype, reply = 'REPL', peerlist
        self.packet = process_message(replytype, reply)

    async def transaction(self, message):
        pass

    async def request_blobchain(self, message):
        pass

    async def flag_error(self, message):
        print(f'Error detected: {message}')
        return ''


BlobNode(8888)
