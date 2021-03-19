import os
from abc import ABC
from tornado.web import Application, RequestHandler
from tornado.httpserver import HTTPServer
from tornado.options import define, options
from tornado.ioloop import IOLoop
from blockchain import Blobchain

define('port', default=8888, help='Port to listen on')

STATIC_DIRNAME = "assets"
settings = {
    "static_path": os.path.join(os.path.dirname(__file__), STATIC_DIRNAME),
    "static_url_prefix": "/assets/",
}


class InfoView(RequestHandler, ABC):
    SUPPORTED_METHODS = ["GET", "POST"]

    def get(self):
        self.render('index.html')


if __name__ == "__main__":
    app = Application([
        (r"/", InfoView),
    ], debug=True, **settings)
    http_server = HTTPServer(app)
    http_server.listen(options.port)
    print(f"Listening on http://localhost:{options.port}")
    IOLoop.current().start()
