#!/usr/bin/env python3

from threading import Thread
from connexion import FlaskApp
from jsonencoding import Encoder

if __name__ == "__main__":
    def flask_thread():
        app = FlaskApp(__name__, specification_dir='openapi/')
        app.app.json_encoder = Encoder
        app.add_api('landingpage.yaml')
        app.add_api('brewerycontrol.yaml')

        app.run(host="0.0.0.0", port=5000)

    Thread(target=flask_thread).start()
