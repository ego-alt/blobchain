from flask import Flask, request

app = Flask(__name__)
localhost = '127.0.0.1'
port = 5000


@app.route('/transaction', methods=['POST'])
def make_transaction():
    if request.method == 'POST':
        try:
            transaction = request.get_json(force=True)
            print(f'Data received: {transaction}')
            print(f'Your transaction has been broadcast')
        except OSError:
            pass


app.run()
