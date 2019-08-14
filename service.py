#!/usr/bin/env python3
import configparser
import os
import logging
import threading
import time
from gpiozero import LED
from flask import (request, render_template, Flask, jsonify)
from apscheduler.schedulers.background import BackgroundScheduler
from simple_pid import PID
from sensor import Sensor
from heater import Heater
from jsonencoding import Encoder

app = Flask(__name__)

logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING"))
log = logging.getLogger('werkzeug')
log.setLevel(os.environ.get("LOGLEVEL", "WARNING"))

#pid = PID(90.48239697647787, 0.3300269798534147, 391.69353427975284, setpoint=1)
pid = PID(100, 0.3300269798534147, 391.69353427975284, setpoint=1)

app.json_encoder = Encoder

apsched = BackgroundScheduler()
config = configparser.ConfigParser()
with open(os.path.expanduser("~/.tempjs.conf"), "r") as f:
    config.read_file(f)

mlt_sensor = Sensor(start_temp = 80,
                    name = "Mäskkärl",
                    setpoint = 35,
                    scheduler=apsched,
                    sensor_id=config.get("tempjs", "mlt_sensor", fallback=""))

hlt_sensor = Sensor(start_temp = 80,
                    name = "Hetvattenskärl",
                    setpoint = 75,
                    scheduler=apsched,
                    sensor_id=config.get("tempjs", "hlt_sensor", fallback=""))

bk_sensor = Sensor(start_temp = 100,
                   name = "Kokkärl",
                   setpoint = 100,
                   scheduler=apsched,
                   sensor_id=config.get("tempjs", "bk_sensor", fallback=""))

graph_log = open("/tmp/graph_log","w")


state = {
        "sensors": {
            "mlt": mlt_sensor,
            "hlt": hlt_sensor,
            "bk": bk_sensor,
            "fermentor": Sensor(start_temp = 20, name = "Jäskyl", setpoint = 23, scheduler=apsched),
        },
        "pumps": {
            "mlt": {
                "name": "Mäskpump",
                "active": False
            },
            "general-purpose": {
                "name": "Pump",
                "active": False
            },
        },
        "heaters": {
            "hlt": Heater(10, "Hetvattenskärl", sensor=hlt_sensor),
            "bk": Heater(11, "Kokkärl", is_manual=True, sensor=bk_sensor),
            "mlt": Heater(17, "Mäskkärl", sensor=mlt_sensor),
        },
        "coolers": {
            "fermentor": {
                "name": "Jäskyl",
                "active": False
            }
        },
}


def update_temps():
    for sensor in state["sensors"].values():
        before = time.time() 
        sensor.update_temp()
        logging.info("Updating sensor '{}' took {} s".format(sensor.name, time.time() - before))

@app.route('/')
def landing_page():
    return render_template('index.html')

@app.route('/state')
def get_state():
    return jsonify(state)

@app.route('/state/heater/<heaterName>', methods = ['PUT'])
def put_heater(heaterName):
    success = False
    error = None
    req = request.get_json()

    if not heaterName in state["heaters"]:
        return {}, 400

    heater = state["heaters"][heaterName]

    if "enabled" in req:
        if req["enabled"]:
            error = heater.enable()
        else:
            error = heater.disable()

    if not error and "setpoint" in req:
        error = heater.sensor.setSetpoint(req["setpoint"])

    if not heater.is_manual and "active" in req:
        error = "Heater does not support manual operation"

    if not error and "active" in req:
        if req["active"]:
            error = heater.start_heating(1)
        else:
            error = heater.stop_heating()

    if error:
        return {"error": error}, 400
    else:
        return state

@app.route('/state/pump/<pump>', methods = ['PUT'])
def put_pump(pump):
    if pump in state["pumps"]:
        if (request.get_json()["active"] == "on"):
            state["pumps"][pump]["active"] = True;
        else:
            state["pumps"][pump]["active"] = False;

    response = state["pumps"][pump]

    return response

@app.route('/state/sensor/<sensor_name>', methods = ['PUT'])
def put_sensor(sensor_name):
    success = False
    error = None
    req = request.get_json()
    sensor = None

    if sensor_name not in state["sensors"]:
        error = "Unknown sensor"

    if not error:
        sensor = state["sensors"][sensor_name]

    if not error and "automation_state" in req:
        if req["automation_state"] == "STOPPED":
            sensor.stop_automation()
        elif req["automation_state"] == "STARTED":
            sensor.start_automation()
        elif req["automation_state"] == "PAUSED":
            sensor.pause_automation()
        else:
            error = "Unknown automation state"

    if error:
        return {"error": error}, 400
    else:
        return state

def initialize_pid():
    pid.sample_time = None
    pid.output_limits = (0, 100.0)

def pid_iteration():
    pid.setpoint = state["sensors"]["mlt"].setpoint
    output = pid(state["sensors"]["mlt"].temperature)
    state["heaters"]["mlt"].start_heating(output/100.0)
    graph_log.write("%f, %f\n" % (output, state["sensors"]["mlt"].temperature))
    graph_log.flush()

@app.before_first_request
def initialize():
    initialize_pid()
    apsched.start()
    apsched.add_job(update_temps,
                    'interval',
                    seconds=len(state["sensors"]),
                    id="update_temps",
                    replace_existing=True)
    apsched.add_job(pid_iteration, 'interval', seconds=3, id="pid_iteration", replace_existing=True)

    state["sensors"]["mlt"].add_heating_stage("Protein rest", 20*60, 50)
    state["sensors"]["mlt"].add_heating_stage("Sacchrification rest", 30*60, 62)
    state["sensors"]["mlt"].add_heating_stage("Mash out", 5*60, 75)

if __name__ == "__main__":
    def flask_thread():
        app.run(host="0.0.0.0")

    threading.Thread(target=flask_thread).start()
