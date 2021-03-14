import asyncio
import socket
import ast

sisters = [8888, 8877, 8866, 8855]
peerlist = []


def extract_data(data):
    decoded = data.decode('utf-8')
    msgtype, message = ast.literal_eval(decoded)
    return msgtype, message


def process_message(msgtype, message):
    packet = str((msgtype, message))
    encoded = packet.encode('utf-8')
    return encoded


async def handle_echo(reader, writer):
    data = await reader.read(1024)
    msgtype, message = extract_data(data)
    address = writer.get_extra_info('peername')
    print(f"Received {msgtype}: {message!r} from {address!r}")

    writer.write(data)
    await writer.drain()
    writer.close()
    print("Close the connection")


async def send_echo(PEERHOST, PEERPORT, msgtype, message):
    reader, writer = await asyncio.open_connection(PEERHOST, PEERPORT)
    newpeer = (PEERHOST, PEERPORT)
    if newpeer not in peerlist:
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


async def main(PORT, HOST=None):
    if not HOST:
        name = socket.gethostname()
        HOST = socket.gethostbyname(name)

    for port in sisters:
        try:
            await send_echo('127.0.0.1', port, 'PING', 'PING')
        except:
            pass

    server = await asyncio.start_server(handle_echo, HOST, PORT)
    address = server.sockets[0].getsockname()
    print(f'Serving on {address}')

    async with server:
        await server.serve_forever()

asyncio.run(main(8888))
