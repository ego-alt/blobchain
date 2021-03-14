import asyncio
import ast

peerlist = [('127.0.0.1', 8877), ('127.0.0.1', 8866), ('127.0.0.1', 8855)]


def extract_data(data):
    decoded = data.decode('utf-8')
    msgtype, message = ast.literal_eval(decoded)
    return msgtype, message


def process_message(msgtype, message):
    packet = str((msgtype, message))
    encoded = packet.encode('utf-8')
    return encoded


async def handle_echo(reader, writer):
    data = await reader.read(100)
    msgtype, message = extract_data(data)
    addr = writer.get_extra_info('peername')
    print(f"Received {msgtype!r}:{message!r} from {addr!r}")

    print(f'Sending reply {msgtype!r}: {message!r}...')
    packet = process_message(msgtype, message)
    writer.write(packet)
    await writer.drain()
    writer.close()


async def main():
    server = await asyncio.start_server(handle_echo, '127.0.0.1', 8888)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

asyncio.run(main())