#!/usr/bin/env python3
import configparser
import flask
import logging
import os
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from flask import stream_with_context
from queue import (Queue, Full)
from simple_pid import PID
from pkg_resources import resource_string

from tempserver.heater import (Heater, HeaterMode)
from tempserver.jsonencoding import Encoder
from tempserver.sensor import Sensor
from tempserver.temperature import Temperature
from tempserver.vessel import Vessel

# Maximum length of a subscribers' queue before considering it inactive and eventually removing it
MAX_SUBSCRIBER_QUEUE_LEN = 200

logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING"))
log = logging.getLogger('werkzeug')
log.setLevel(os.environ.get("LOGLEVEL", "WARNING"))

apsched = BackgroundScheduler()
apsched.start()

config = configparser.ConfigParser()
conf_candidates = ["~/.tempserver.conf", "/etc/tempserver.conf"]

config_read = False
for candidate in conf_candidates:
    path = os.path.expanduser(candidate)
    if os.path.exists(path):
        with open(path, "r") as f:
            config.read_file(f)
            config_read = True
        break

if not config_read:
    print("Failed to read config. Tried the following locations: " + ', '.join(conf_candidates))
    sys.exit(-1)

encoder = Encoder()

stream_subscribers = []


def notify_change(elem):
    for subscriber in stream_subscribers:
        try:
            subscriber.put_nowait(elem)
        except Full:
            # Its likely full because nobody listens anymore. Clean up.
            stream_subscribers.remove(subscriber)


state = {
    "vessels": {}
}

for vessel_id in set([x.split("/")[1] for x in config.sections() if x.startswith("vessels/")]):
    name = config.get("vessels/" + vessel_id, "name", fallback="Unknown name")
    pid = PID(float(config.get("vessels/" + vessel_id + "/pid", "p")),
              float(config.get("vessels/" + vessel_id + "/pid", "i")),
              float(config.get("vessels/" + vessel_id + "/pid", "d")),
              setpoint=1, output_limits=(0, 100))

    # Monkey-patch last seen output value into PID objects. This is for convenience
    # since the PID objects are used by both Sensor and Heater.
    pid.output = 0

    sensor = Sensor(name=name,
                    id_=vessel_id,
                    scheduler=apsched,
                    sensor_id=config.get("vessels/" + vessel_id, "sensor_id", fallback=""),
                    pid=pid,
                    notify_change=notify_change)

    heater = Heater(config.get("vessels/" + vessel_id + "/heater", "gpio_pin"),
                    name,
                    id_=vessel_id,
                    sensor=sensor,
                    pid=pid,
                    scheduler=apsched,
                    notify_change=notify_change)

    vessel = Vessel(vessel_id, name, heater=heater, sensor=sensor, pid=pid)

    state["vessels"][vessel_id] = vessel


def get_static(file):
    template = resource_string(__name__, 'data/web-ui/static/' + file)
    template = template.decode('utf-8')
    return template


def get_landing_page():
    template = resource_string(__name__, 'data/web-ui/templates/index.html')
    template = template.decode('utf-8')
    return flask.render_template_string(template)


def get_vessel():
    return list(state["vessels"].values())


def get_stream():
    queue = Queue(MAX_SUBSCRIBER_QUEUE_LEN)  # If many events are queued, most likely the listener has disconnected.

    def stream():
        stream_subscribers.append(queue)

        while True:
            tag, message = queue.get()
            data = encoder.sse(tag, message)
            yield data

    return flask.Response(stream_with_context(stream()), mimetype="text/event-stream")


def post_vessel_chart(vesselId, window):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel_ = state["vessels"][vesselId]

    return vessel_.sensor.tempHistory


def get_vessel_temperature(vesselId):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel_ = state["vessels"][vesselId]

    return vessel_.sensor.temperature


def get_vessel_mode(vesselId):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel_ = state["vessels"][vesselId]

    return vessel_.heater.mode


def put_vessel_mode(vesselId, mode):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel_ = state["vessels"][vesselId]
    mode = HeaterMode(mode["mode"])
    if mode == HeaterMode.ON:
        vessel_.heater.enable()
    elif mode == HeaterMode.OFF:
        vessel_.heater.disable()
    elif mode == HeaterMode.PID:
        vessel_.heater.enable_pid()
    else:
        return {"error": "Invalid mode"}, 400


def put_vessel_pid(vesselId, tunings):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel_ = state["vessels"][vesselId]

    vessel_.pid.tunings = (
        tunings["Kp"],
        tunings["Ki"],
        tunings["Kd"])

    vessel_.heater.publish_state()


def put_vessel_setpoint(vesselId, setpoint):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel_ = state["vessels"][vesselId]

    vessel_.pid.setpoint = setpoint["temperature"]
    vessel_.heater.publish_state()


def get_vessel_setpoint(vesselId):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel_ = state["vessels"][vesselId]

    return Temperature(vessel_.pid.setpoint)


def get_vessel_pid(vesselId):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel_ = state["vessels"][vesselId]

    return vessel_.pid


def verify_api_key(apikey, required_scopes=None):
    return {"sub": "admin"}
