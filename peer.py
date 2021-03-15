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
        await self.build_peers()
        print(f'Serving on {self.address}')
        async with server:
            await server.serve_forever()

    async def send_echo(self, PEERHOST, PEERPORT, msgtype, message):
        reader, writer = await asyncio.open_connection(PEERHOST, PEERPORT)
        newpeer = (PEERHOST, PEERPORT)
        if newpeer not in peerlist and len(peerlist) < self.maxpeers:
            peerlist.append(newpeer)
            print(f'{PEERHOST}:{PEERPORT} added to peer list')

        print(f'Sending message {msgtype!r}: {message!r} to {newpeer!r}...')
        packet = process_message(msgtype, message)
        writer.write(packet)

        data = await reader.read(1024)
        replytype, reply = extract_data(data)
        print(f'Received reply {replytype}: {reply!r} from {newpeer!r}')

        await writer.drain()
        writer.close()

    async def handle_echo(self, reader, writer):
        data = await reader.read(1024)
        msgtype, message = extract_data(data)
        address = writer.get_extra_info('peername')
        print(f"Received message {msgtype}: {message!r} from {address!r}")

        writer.write(data)
        await writer.drain()
        writer.close()
        print("Close the connection")

    async def build_peers(self):
        try:
            await asyncio.gather(*(self.send_echo('127.0.0.1', port, 'PING', self.address) for port in sisters))
        except OSError:
            pass


class Handler:
    def __init__(self, HOST, PORT, maxpeers, PEERHOST=None, PEERPORT=None):
        self.host = HOST
        self.port = PORT
        self.maxpeers = maxpeers
        self.peerhost = PEERHOST
        self.peerport = PEERPORT
        self.handlers = {'PING': self.ping_check,
                        'LIST': self.list_peers,
                        'CASH': self.transaction,
                        'BLOB': self.request_blobchain,
                        'ERRO': self.flag_error}

    async def handle_data(self, data):
        msgtype, message = extract_data(data)
        if msgtype in self.handlers:
            await self.handlers[msgtype](message)

    async def ping_check(self, message):
        """PING is sent to a peer contact which was not initially in the peer list
        PING includes its message type 'PING' and the sender's contact details, i.e. host and port
        In response, the receiver checks whether the sender is in the peer list, and if not, adds them"""
        self.peerhost, self.peerport = ast.literal_eval(message)
        newpeer = (self.peerhost, self.peerport)

        if newpeer not in peerlist and len(peerlist) < self.maxpeers:
            peerlist.append(newpeer)
            print(f'{self.peerhost}:{self.peerport} added to peer list')
        elif newpeer in peerlist:
            print(f'ALERT: {self.peerhost}:{self.peerport} is already a peer')
        elif len(peerlist) < self.maxpeers:
            print(f'ALERT: peer list has reached its maximum capacity of {self.maxpeers}')

    async def list_peers(self, message):
        pass

    async def transaction(self, message):
        pass

    async def request_blobchain(self, message):
        pass

    async def flag_error(self, message):
        pass


BlobNode(8888)








