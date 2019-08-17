#!/usr/bin/env python3
import configparser
import os
import logging
import threading
import time
from gpiozero import LED
from apscheduler.schedulers.background import BackgroundScheduler
from sensor import Sensor
from heater import Heater
from jsonencoding import Encoder
from simple_pid import PID
from vessel import Vessel
import connexion, flask
from flask import stream_with_context

logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING"))
log = logging.getLogger('werkzeug')
log.setLevel(os.environ.get("LOGLEVEL", "WARNING"))

apsched = BackgroundScheduler()
apsched.start()

config = configparser.ConfigParser()
with open(os.path.expanduser("~/.tempjs.conf"), "r") as f:
    config.read_file(f)

mlt_pid = PID(22, 0.1, 200, setpoint=1, output_limits = (0, 100))
hlt_pid = PID(22, 0.1, 200, setpoint=1, output_limits = (0, 100))
bk_pid = PID(22, 0.1, 200, setpoint=1, output_limits = (0, 100))

# Monkey-patch last seen output value into PID objects. This is for convenience
# since the PID objects are used by both Sensor and Heater.
mlt_pid.output = 0
hlt_pid.output = 0
bk_pid.output = 0
encoder = Encoder()

mlt_sensor = Sensor(start_temp = 80,
                    name = "Mäskkärl",
                    scheduler=apsched,
                    sensor_id=config.get("tempjs", "mlt_sensor", fallback=""),
                    pid = mlt_pid)

hlt_sensor = Sensor(start_temp = 80,
                    name = "Hetvattenskärl",
                    scheduler=apsched,
                    sensor_id=config.get("tempjs", "hlt_sensor", fallback=""),
                    pid = hlt_pid)

bk_sensor = Sensor(start_temp = 100,
                   name = "Kokkärl",
                   scheduler=apsched,
                   sensor_id=config.get("tempjs", "bk_sensor", fallback=""),
                   pid = bk_pid)

hlt_heater = Heater(10,
                    "Hetvattenskärl",
                    sensor=hlt_sensor,
                    pid=hlt_pid,
                    scheduler = apsched)

bk_heater = Heater(11,
                   "Kokkärl",
                   is_manual=True,
                   sensor=bk_sensor,
                   pid=bk_pid,
                   scheduler = apsched)

mlt_heater = Heater(17,
                    "Mäskkärl",
                    sensor=mlt_sensor,
                    pid=mlt_pid,
                    scheduler = apsched)

state = {
        "vessels": {
            "bk": Vessel("bk",
                         "Kokkärl",
                         heater=bk_heater,
                         sensor=bk_sensor,
                         pid=bk_pid),
            "mlt": Vessel("mlt",
                          "Mäskkärl",
                          heater=mlt_heater,
                          sensor=mlt_sensor,
                          pid=mlt_pid),
            "hlt": Vessel("hlt",
                          "Hetvattenskärl",
                          heater=hlt_heater,
                          sensor=hlt_sensor,
                          pid=hlt_pid)
        }
}

def get_landing_page():
    return flask.render_template('index.html')

def get_vessel():
    return list(state["vessels"].values())

def post_vessel_chart(vesselId, window):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel = state["vessels"][vesselId]

    return vessel.sensor.tempHistory

def get_vessel_chart_stream(vesselId):
    def stream():
        while True:
            c = post_vessel_chart(vesselId, {})
            yield encoder.sse(c[-1]) if len(c) > 0 else encoder.sse({})
            time.sleep(1)

    return flask.Response(stream_with_context(stream()), mimetype="text/event-stream")

def get_vessel_temperature(vesselId):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel = state["vessels"][vesselId]

    return vessel.sensor.temperature

def get_vessel_temperature_stream(vesselId):
    def stream():
        while True:
            yield encoder.sse(get_vessel_temperature(vesselId))
            time.sleep(1)

    return flask.Response(stream_with_context(stream()), mimetype="text/event-stream")

def get_vessel_mode(vesselId):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel = state["vessels"][vesselId]

    return vessel.heater.mode

def put_vessel_mode(vesselId, mode):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel = state["vessels"][vesselId]
    if mode == "on":
        vessel.heater.enable()
    elif mode == "off":
        vessel.heater.disable()
    elif mode == "pid":
        vessel.heater.enable_pid()
    else:
        return {"error": "Invalid mode"}, 400

def put_vessel_pid(vesselId, tunings):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel = state["vessels"][vesselId]

    vessel.pid.tunings = (
            tunings["Kp"],
            tunings["Ki"],
            tunings["Kd"])

def get_vessel_pid(vesselId):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel = state["vessels"][vesselId]

    return vessel.pid

def get_vessel_pid_stream(vesselId):
    e = Encoder()

    def stream():
        while 1:
            yield e.sse(get_vessel_pid(vesselId))
            time.sleep(1)

    return flask.Response(stream_with_context(stream()), mimetype="text/event-stream"), 200

def verify_api_key(apikey, required_scopes=None):
    return {"sub": "admin"}
