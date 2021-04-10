import sys
from flask import Flask

app = Flask(__name__)

@app.route("/")
def log_transaction():