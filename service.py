#!/usr/bin/env python3
import configparser
import os
import logging
import threading
import time
from gpiozero import LED
from apscheduler.schedulers.background import BackgroundScheduler
from sensor import Sensor
from heater import (Heater, HeaterMode)
from jsonencoding import Encoder
from simple_pid import PID
from vessel import Vessel
import connexion, flask
from flask import stream_with_context
from queue import Queue

logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING"))
log = logging.getLogger('werkzeug')
log.setLevel(os.environ.get("LOGLEVEL", "WARNING"))

apsched = BackgroundScheduler()
apsched.start()

config = configparser.ConfigParser()
with open(os.path.expanduser("~/.tempjs.conf"), "r") as f:
    config.read_file(f)

mlt_pid = PID(5, 0.03, 200, setpoint=1, output_limits = (0, 100))
hlt_pid = PID(5, 0.03, 200, setpoint=1, output_limits = (0, 100))
bk_pid = PID(5, 0.03, 200, setpoint=1, output_limits = (0, 100))

# Monkey-patch last seen output value into PID objects. This is for convenience
# since the PID objects are used by both Sensor and Heater.
mlt_pid.output = 0
hlt_pid.output = 0
bk_pid.output = 0
encoder = Encoder()

stream_subscribers = []

def notify_change(elem):
    for subscriber in stream_subscribers:
        subscriber(elem)

mlt_sensor = Sensor(start_temp = 80,
                    name = "Mäskkärl",
                    id = "mlt",
                    scheduler=apsched,
                    sensor_id=config.get("tempjs", "mlt_sensor", fallback=""),
                    pid = mlt_pid,
                    notify_change = notify_change)

hlt_sensor = Sensor(start_temp = 80,
                    name = "Hetvattenskärl",
                    id = "hlt",
                    scheduler=apsched,
                    sensor_id=config.get("tempjs", "hlt_sensor", fallback=""),
                    pid = hlt_pid,
                    notify_change = notify_change)

bk_sensor = Sensor(start_temp = 100,
                   name = "Kokkärl",
                   id = "bk",
                   scheduler=apsched,
                   sensor_id=config.get("tempjs", "bk_sensor", fallback=""),
                   pid = bk_pid,
                   notify_change = notify_change)

hlt_heater = Heater(10,
                    "Hetvattenskärl",
                    id = "hlt",
                    sensor=hlt_sensor,
                    pid=hlt_pid,
                    scheduler = apsched,
                    notify_change = notify_change)

bk_heater = Heater(11,
                   "Kokkärl",
                   id = "bk",
                   is_manual=True,
                   sensor=bk_sensor,
                   pid=bk_pid,
                   scheduler = apsched,
                   notify_change = notify_change)

mlt_heater = Heater(17,
                    "Mäskkärl",
                    id = "mlt",
                    sensor=mlt_sensor,
                    pid=mlt_pid,
                    scheduler = apsched,
                    notify_change = notify_change)

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

def get_stream():
    queue = Queue()

    def stream():
        stream_subscribers.append(queue.put)

        while True:
            tag, message = queue.get()
            data = encoder.sse(tag, message)
            yield data

    return flask.Response(stream_with_context(stream()), mimetype="text/event-stream")

def post_vessel_chart(vesselId, window):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel = state["vessels"][vesselId]

    return vessel.sensor.tempHistory

def get_vessel_temperature(vesselId):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel = state["vessels"][vesselId]

    return vessel.sensor.temperature

def get_vessel_mode(vesselId):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel = state["vessels"][vesselId]

    return vessel.heater.mode

def put_vessel_mode(vesselId, mode):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel = state["vessels"][vesselId]
    mode = HeaterMode(mode["mode"])
    if mode == HeaterMode.ON:
        vessel.heater.enable()
    elif mode == HeaterMode.OFF:
        vessel.heater.disable()
    elif mode == HeaterMode.PID:
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

    vessel.heater.publish_state()

def put_vessel_setpoint(vesselId, setpoint):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel = state["vessels"][vesselId]

    vessel.pid.setpoint = setpoint["temperature"]
    vessel.heater.publish_state()

def get_vessel_setpoint(vesselId, setpoint):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel = state["vessels"][vesselId]

    return Temperature(vessel.pid.setpoint)

def get_vessel_pid(vesselId):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel = state["vessels"][vesselId]

    return vessel.pid

def verify_api_key(apikey, required_scopes=None):
    return {"sub": "admin"}
