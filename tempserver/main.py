#!/usr/bin/env python3

from connexion import App
from pkg_resources import (resource_filename, resource_exists, resource_isdir)
from swagger_ui_bundle import swagger_ui_3_path
from threading import Thread

from tempserver.jsonencoding import Encoder


def main():
    def flask_thread():
        resource = 'data/openapi'
        if (not resource_exists(__name__, resource)
                or not resource_isdir(__name__, resource)):
            print("Unable to load OpenAPI specifications - installation broken?")
            return -1

        options = {'swagger_path': swagger_ui_3_path}
        spec_dir = resource_filename(__name__, resource)
        print("Options: " + str(options))

        app = App(__name__, specification_dir=spec_dir, options=options)
        app.app.json_encoder = Encoder
        app.add_api('landingpage.yaml')
        app.add_api('brewerycontrol.yaml')

        app.run(host="0.0.0.0", port=5000)

    Thread(target=flask_thread).start()


if __name__ == "__main__":
    main()
