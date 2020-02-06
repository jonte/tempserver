#!/usr/bin/env python3

from tempserver.service import TemperatureService


def main():
    service = TemperatureService()
    app = service.app
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
