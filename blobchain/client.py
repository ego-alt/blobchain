from flask import Flask, request
import blobchain.peer as peer
import asyncio

app = Flask(__name__)
defaulthost = '127.0.0.1'
sisters = [8888, 8877, 8866, 8855]
port = 5000


@app.route('/transaction', methods=['POST'])
def make_transaction():
    if request.method == 'POST':
        transaction = request.get_json(force=True)
        print(f'Data received: {transaction}')
        client = peer.BlobNode(port)
        try:
            for peerport in sisters:
                asyncio.run(client.send_echo(defaulthost, peerport, 'CASH', transaction))
            print(f'Your transaction has been broadcast')
        except OSError:
            pass


app.run()
