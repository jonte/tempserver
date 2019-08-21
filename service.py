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

mlt_sensor = Sensor(start_temp = 80,
                    name = "Mäskkärl",
                    id = "mlt",
                    scheduler=apsched,
                    sensor_id=config.get("tempjs", "mlt_sensor", fallback=""),
                    pid = mlt_pid)

hlt_sensor = Sensor(start_temp = 80,
                    name = "Hetvattenskärl",
                    id = "hlt",
                    scheduler=apsched,
                    sensor_id=config.get("tempjs", "hlt_sensor", fallback=""),
                    pid = hlt_pid)

bk_sensor = Sensor(start_temp = 100,
                   name = "Kokkärl",
                   id = "bk",
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

def get_stream():
    memory = {}

    def has_changed(memory, tag, new):
        if tag not in memory:
            memory[tag] = new
            return True

        change = (memory[tag] != new)
        memory[tag] = new
        return change

    def stream_vessel_chart():
        for vessel in state["vessels"].values():
            tag = "vessel-chart-%s" % vessel.id
            if vessel.sensor.tempHistory:
                data = encoder.sse(tag, vessel.sensor.tempHistory[-1])
                if has_changed(memory, tag, data):
                    yield data

    def stream_vessel_temperature():
        for vessel in state["vessels"].values():
            tag = "vessel-temperature-%s" % vessel.id
            data = encoder.sse(tag, vessel.sensor.temperature)
            yield data

    def stream_vessel_power():
        for vessel in state["vessels"].values():
            tag = "vessel-power-%s" % vessel.id
            data = encoder.sse(tag, vessel.heater.heating_element.value * 100)
            yield data

    def stream_vessel_heater():
        for vessel in state["vessels"].values():
            tag = "vessel-heater-%s" % vessel.id
            data = encoder.sse(tag, vessel.heater)
            yield data

    def stream_vessel_list():
        tag = "vessels"
        data = encoder.sse("vessels", list(state["vessels"].keys()))
        yield data

    def stream_vessels():
        for vessel in state["vessels"].values():
            tag = "vessel-%s" % vessel.id
            data = encoder.sse(tag, vessel)
            yield data

    def stream():
        while True:
            yield from stream_vessels()
            yield from stream_vessel_power()
            yield from stream_vessel_list()
            yield from stream_vessel_temperature()
            yield from stream_vessel_chart()
            yield from stream_vessel_heater()
            time.sleep(1)

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

def put_vessel_setpoint(vesselId, setpoint):
    if vesselId not in state["vessels"]:
        return {"error": "Invalid vessel ID"}, 400

    vessel = state["vessels"][vesselId]

    vessel.pid.setpoint = setpoint["temperature"]

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
