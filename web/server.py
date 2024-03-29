import os
from abc import ABC
from tornado.web import Application, RequestHandler
from tornado.options import define, options, parse_command_line
from tornado.ioloop import IOLoop

define('port', default=5000, help='Port to listen on')

STATIC_DIRNAME = "assets"
settings = {
    "static_path": os.path.join(os.path.dirname(__file__), STATIC_DIRNAME),
    "static_url_prefix": "/assets/",
}


class InfoView(RequestHandler, ABC):
    SUPPORTED_METHODS = ["GET", "POST"]

    def get(self):
        self.render('index.html')

    def post(self):
        if self.get_argument("send", None) is not None:
            sender = self.get_body_argument("sender")
            recipient = self.get_body_argument("recipient")
            amount = self.get_body_argument("amount")
            transaction = {'sender': sender, 'recipient': recipient, 'amount': amount}

        if self.get_argument("check", None) is not None:
            key = self.get_body_argument("key")

        if self.get_argument("download", None) is not None:
            pass


def main():
    parse_command_line()
    app = Application([
        (r"/", InfoView),
    ], debug=True, **settings)
    app.listen(options.port)
    IOLoop.current().start()


if __name__ == "__main__":
    main()
