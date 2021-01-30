from abc import ABC
from tornado.web import Application, RequestHandler
from tornado.httpserver import HTTPServer
from tornado.options import define, options
from tornado.ioloop import IOLoop

from blockchain import Blockchain

define('port', default=8888, help='Port to listen on')
new_chain = Blockchain()


class InfoView(RequestHandler, ABC):
    SUPPORTED_METHODS = ["GET"]

    def get(self):
        self.write("Welcome to the hub. On this page is the blockchain ledger:")
        for block in new_chain.chain:
            self.write(vars(block))


class Transaction(RequestHandler, ABC):
    SUPPORTED_METHODS = ["GET", "POST"]

    def get(self):
        self.write('<html><body><form action="" method="POST">'
                   '<input type="text" name="recipient">'
                   '<input type="text" name="sender">'
                   '<input type="number" name="amount">'
                   '<input type="submit" value="Submit">'
                   '</form></body></html>')

    def post(self):
        self.set_header("Content-Type", "text/plain")
        new_chain.new_block(self.get_body_argument("recipient"), self.get_body_argument("sender"),
                            self.get_body_argument("amount"))
        self.write("The transaction was successful")


if __name__ == "__main__":
    app = Application([
        ("/", InfoView),
        ("/transaction/", Transaction),
    ], debug=True)
    http_server = HTTPServer(app)
    http_server.listen(options.port)
    print(f"Listening on http://localhost:{options.port}")
    IOLoop.current().start()
