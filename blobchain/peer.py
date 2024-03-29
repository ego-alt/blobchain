import blobchain.blockchain as blockchain
import asyncio
import socket
import ast

# Hard-coded nodes in the network provides a contact point for finding other peers
defaulthost = '127.0.0.1'
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
        """Initialises a fully functioning peer node which can handle and send requests"""
        self.blo = blockchain.Blobchain()

        self.maxpeers = 100
        self.port = PORT
        if not HOST:
            name = socket.gethostname()
            self.host = socket.gethostbyname(name)
        else:
            self.host = HOST
        self.address = None

    async def main(self):
        server = await asyncio.start_server(self.handle_echo, self.host, self.port)
        self.address = server.sockets[0].getsockname()
        print(f'Serving on {self.address}')

        try:
            await asyncio.gather(*(self.build_peers(defaulthost, peerport) for peerport in sisters))
        except OSError:
            pass

        async with server:
            await server.serve_forever()

    async def routine(self, PEERHOST, PEERPORT, msgtype, message):
        """Creates the routine of sending messages, receiving replies, and correctly using the information"""
        newpeer = (PEERHOST, PEERPORT)
        try:
            replytype, reply = await self.send_echo(PEERHOST, PEERPORT, msgtype, message)
            await self.handle_reply(newpeer, replytype, reply)
            return True
        except OSError:
            return False

    async def broadcast(self, msgtype, message):
        for peer in peerlist:
            peerhost, peerport = peer
            await self.routine(peerhost, peerport, msgtype, message)

    async def send_echo(self, PEERHOST, PEERPORT, msgtype, message):
        """Sends and receives messages"""
        reader, writer = await asyncio.open_connection(PEERHOST, PEERPORT)
        newpeer = (PEERHOST, PEERPORT)
        print(f'Sending message {msgtype}: {message!r} to {newpeer!r}...')
        packet = process_message(msgtype, message)
        writer.write(packet)

        data = await reader.read(1024)
        replytype, reply = extract_data(data)
        await writer.drain()
        writer.close()

        return replytype, reply

    async def handle_reply(self, newpeer, replytype, reply):
        """Interprets replytype in order to decide what to do with reply
        :param newpeer: Name of the client node
        :param replytype: In the format REPL-{original request} so that the purpose of the reply is known
        :param reply: Information satisfying the original request"""
        print(f'Received reply {replytype}: {reply!r} from {newpeer!r}')
        response = ReplyHandler()
        condition, element = await response.reply_data(replytype, reply, self.blo.chain)
        if condition == 'UPDATE':
            await self.update_blockchain(element)
            print(self.blo.chain)

    async def handle_echo(self, reader, writer):
        """Receives incoming messages and returns an appropriate reply"""
        data = await reader.read(1024)
        msgtype, message = extract_data(data)
        print(f'Received message {msgtype}: {message!r}')
        response = Handler(self.maxpeers)
        anunctype, announcement = await response.handle_data(data, self.blo)
        if anunctype:
            await self.broadcast(anunctype, announcement)
            writer.write(response.packet)
            print(f'Sending reply...')
            await writer.drain()
            writer.close()

    async def update_blockchain(self, other_chain):
        self.blo.chain = other_chain
        print('The blobchain has been updated with the longest chain')

    async def build_peers(self, host, port):
        try:
            newpeer = (host, port)
            if (host != self.host or port != self.port) and (newpeer not in peerlist):
                if len(peerlist) < self.maxpeers and await self.routine(host, port, 'PING', self.address):
                    peerlist.append(newpeer)
                    print(f'{host!r}:{port!r} added to peer list')

                    print(f'Building peers...')
                    _, reply = await self.send_echo(host, port, 'LIST', None)
                    reply = ast.literal_eval(str(reply))
                    for peeraddr in reply:
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
        """The object Handler takes incoming requests and decides how to reply
        PING: adds the sender to the peer list if the maximum has not been reached
        LIST: shares a copy of the full peer list to the sender
        CASH: puts in proof of work to verify the sent transaction
        BLOB: shares a copy of the full blockchain to the sender"""
        self.maxpeers = maxpeers
        self.peerhost = PEERHOST
        self.peerport = PEERPORT
        self.handlers = {'PING': self.ping_check,
                         'LIST': self.list_peers,
                         'BLOB': self.request_blobchain,
                         'BLOC': self.fresh_block}
        # value_handlers have to return values to the BlobNode for further handling
        self.value_handlers = {'CASH': self.transaction}
        self.packet = None

    async def handle_data(self, data, blo):
        msgtype, message = extract_data(data)
        message = str(message)
        if msgtype in self.handlers:
            await self.handlers[msgtype](message, blo)
            return None, None
        elif msgtype in self.value_handlers:
            anunctype, announcement = await self.value_handlers[msgtype](message, blo)
            return anunctype, announcement
        else:
            return None, None

    async def ping_check(self, message, *args):
        """PING is sent to a peer contact which was not initially in the peer list
        PING includes its message type 'PING' and the sender's contact details, i.e. host and port
        In response, the receiver checks whether the sender is in the peer list, and if not, adds them"""
        self.peerhost, self.peerport = ast.literal_eval(message)
        newpeer = (self.peerhost, self.peerport)

        if newpeer not in peerlist and len(peerlist) < self.maxpeers:
            peerlist.append(newpeer)
            print(f'{self.peerhost!r}:{self.peerport!r} added to peer list')
            replytype, reply = 'REPL-PING', None
            self.packet = process_message(replytype, reply)

        elif newpeer in peerlist:
            print(f'ALERT: {self.peerhost!r}:{self.peerport!r} is already a peer')
            replytype, reply = 'ERRO', 'Request to add was declined, because you are already listed'
            self.packet = process_message(replytype, reply)

        elif len(peerlist) < self.maxpeers:
            print(f'ALERT: peer list has reached its maximum capacity of {self.maxpeers!r}')
            replytype, reply = 'ERRO', 'Request to add was declined, because maximum number of peers has been reached'
            self.packet = process_message(replytype, reply)

    async def list_peers(self, _, *args):
        """Upon receiving LIST, shares the full peer list to the node which made the request"""
        replytype, reply = 'REPL-LIST', peerlist
        self.packet = process_message(replytype, reply)

    async def request_blobchain(self, _, blo):
        blobchain = []
        for blob in blo.chain:
            blobchain.append(vars(blob))
        replytype, reply = 'REPL-BLOB', blobchain
        self.packet = process_message(replytype, reply)

    async def fresh_block(self, message, blo):
        """On receiving BLOC, the node updates its own chain and broadcasts the new block to its own peers
        This should result in a network of broadcasts, in order to announce the existence of the new transaction"""
        transaction = ast.literal_eval(message)
        recipient = transaction["recipient"]
        sender = transaction["sender"]
        amount = transaction["amount"]
        blo.new_block(recipient, sender, amount)

    async def transaction(self, message, blo):
        """The receiver verifies the transaction and mines a new block"""
        transaction = ast.literal_eval(message)
        recipient = transaction["recipient"]
        sender = transaction["sender"]
        amount = transaction["amount"]

        blo.new_block(recipient, sender, amount)
        print(f'{sender} successfully transferred {amount} blobcoin to {recipient}')
        replytype, reply = 'REPL-CASH', None
        self.packet = process_message(replytype, reply)
        return 'BLOC', transaction


class ReplyHandler:
    """The object ReplyHandler receives replies from its previous requests and decides how to use the information
    REPL-LIST: adds new peers to the peer list
    REPL-CASH: reports the first instance of a verification of the transaction
    REPLY-BLOB: compares the highest index in the chain received with its own blobchain"""
    def __init__(self):
        self.handlers = {'REPL-LIST': self.reply_list,
                         'REPL-CASH': self.reply_cash,
                         'REPL-BLOB': self.reply_blob}

    async def reply_data(self, command, reply, blockchain):
        reply = ast.literal_eval(str(reply))
        if command == 'REPL-BLOB':
            return await self.reply_blob(reply, blockchain)
        elif command in self.handlers and not 'REPL-BLOB':
            return await self.handlers[command](reply)
        else:
            return False, None

    async def reply_list(self, reply):
        newpeers = []
        for peeraddr in reply:
            newpeers.append(peeraddr) if peeraddr not in peerlist else newpeers
        peerlist.extend(newpeers)
        counter = len(newpeers)
        print(f'{counter} new peers added to peer list')
        return True, None

    async def reply_cash(self, reply):
        return True, None

    async def reply_blob(self, reply, blockchain):
        other_chain = reply
        block_num = len(other_chain)
        return ('UPDATE', other_chain) if len(blockchain) < block_num else (False, None)
