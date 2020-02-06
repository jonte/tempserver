#!/usr/bin/env python3
import configparser
import logging
import os
import sys

from asyncio import Queue, QueueFull
from simple_pid import PID
from pkg_resources import resource_string
from quart import request, jsonify, Quart, stream_with_context,\
                  render_template_string

from tempserver.heater import (Heater, HeaterMode)
from tempserver.jsonencoding import Encoder
from tempserver.pump import (Pump, PumpMode)
from tempserver.sensor import Sensor
from tempserver.temperature import Temperature
from tempserver.vessel import Vessel

# Maximum length of a subscribers' queue before considering it inactive and
# eventually removing it
MAX_SUBSCRIBER_QUEUE_LEN = 200

logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING"))
log = logging.getLogger('werkzeug')
log.setLevel(os.environ.get("LOGLEVEL", "WARNING"))

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
    print('Failed to read config. Tried the following locations: ' +
          ', '.join(conf_candidates))
    sys.exit(-1)

stream_subscribers = []


def notify_change(elem):
    for subscriber in stream_subscribers:
        try:
            subscriber.put_nowait(elem)
        except QueueFull:
            # Its likely full because nobody listens anymore. Clean up.
            stream_subscribers.remove(subscriber)


state = {
    "vessels": {},
    "pumps": {}
}


def populate_vessels():
    config_sections = filter(lambda x: x.startswith("vessels/"),
                             config.sections())
    vessels = [x.split("/")[1] for x in config_sections]

    for vessel_id in set(vessels):
        name = config.get("vessels/" + vessel_id,
                          "name", fallback="Unknown name")
        pid = PID(float(config.get("vessels/" + vessel_id + "/pid", "p")),
                  float(config.get("vessels/" + vessel_id + "/pid", "i")),
                  float(config.get("vessels/" + vessel_id + "/pid", "d")),
                  setpoint=1, output_limits=(0, 100))

        # Monkey-patch last seen output value into PID objects. This is for
        # convenience since the PID objects are used by both Sensor and Heater.
        pid.output = 0

        sensor_id = config.get("vessels/" + vessel_id,
                               "sensor_id", fallback="")
        temp_offset = float(config.get("vessels/" + vessel_id +
                                       "/sensor/" + sensor_id,
                                       "temp_offset", fallback=0.0))
        gpio_pin = config.get("vessels/" + vessel_id + "/heater", "gpio_pin")

        sensor = Sensor(name=name,
                        id_=vessel_id,
                        sensor_id=sensor_id,
                        temp_offset=temp_offset,
                        pid=pid,
                        notify_change=notify_change)

        heater = Heater(gpio_pin,
                        name,
                        id_=vessel_id,
                        sensor=sensor,
                        pid=pid,
                        notify_change=notify_change)

        vessel = Vessel(vessel_id,
                        name,
                        heater=heater,
                        sensor=sensor,
                        pid=pid)

        state["vessels"][vessel_id] = vessel


def populate_pumps():
    config_sections = filter(lambda x: x.startswith("pumps/"),
                             config.sections())
    pumps = [x.split("/")[1] for x in config_sections]

    for pump_id in set(pumps):
        name = config.get("pumps/" + pump_id, "name", fallback="Unknown name")

        pump = Pump(config.get("pumps/" + pump_id, "gpio_pin"),
                    name,
                    id_=pump_id,
                    notify_change=notify_change)

        state["pumps"][pump_id] = pump


class TemperatureService():
    app = Quart(__name__)
    app.json_encoder = Encoder
    encoder = Encoder()

    @app.before_serving
    def initialize():
        # We launch this from qithin Quart to ensure we get the same event loop
        populate_vessels()
        populate_pumps()

    @app.route("/v1/vessel")
    async def vessel():
        response = list(state["vessels"].values())
        return jsonify(response)

    @app.route("/v1/vessel/<vesselId>/temperature")
    async def vessel_temperature(vesselId):
        if vesselId not in state["vessels"]:
            return {"error": "Invalid vessel ID"}, 400

        vessel_ = state["vessels"][vesselId]
        response = vessel_.sensor.temperature

        return jsonify(response)

    @app.route('/v1/vessel/<vesselId>/mode', methods=['GET', 'PUT'])
    async def vessel_mode(vesselId):
        if vesselId not in state['vessels']:
            return {'error': 'Invalid vessel ID'}, 400

        vessel_ = state['vessels'][vesselId]

        if request.method == 'GET':
            return jsonify(vessel_.heater.mode)
        elif request.method == 'PUT':
            mode = await request.get_json(force=True)
            mode = HeaterMode(mode["mode"])
            if mode == HeaterMode.ON:
                vessel_.heater.enable()
            elif mode == HeaterMode.OFF:
                vessel_.heater.disable()
            elif mode == HeaterMode.PID:
                vessel_.heater.enable_pid()
            else:
                return {"error": "Invalid mode"}, 400
            return {}, 200
        else:
            return {}, 405

    @app.route('/v1/vessel/<vesselId>/pid', methods=['GET', 'PUT'])
    async def vessel_pid(vesselId):
        if vesselId not in state["vessels"]:
            return {"error": "Invalid vessel ID"}, 400

        vessel_ = state["vessels"][vesselId]

        if request.method == 'GET':
            return jsonify(vessel_.pid)
        elif request.method == 'PUT':
            tunings = await request.get_json(force=True)

            vessel_.pid.tunings = (
                tunings["Kp"],
                tunings["Ki"],
                tunings["Kd"])

            vessel_.heater.publish_state()
            return {}, 200
        else:
            return {}, 405

    @app.route('/v1/vessel/<vesselId>/setpoint', methods=['GET', 'PUT'])
    async def vessel_setpoint(vesselId):
        if vesselId not in state["vessels"]:
            return {"error": "Invalid vessel ID"}, 400

        vessel_ = state["vessels"][vesselId]

        if request.method == 'GET':
            return jsonify(Temperature(vessel_.pid.setpoint))
        elif request.method == 'PUT':
            setpoint = await request.get_json(force=True)
            vessel_.pid.setpoint = setpoint["temperature"]
            vessel_.heater.publish_state()
            return {}, 200
        else:
            return {}, 405

    @app.route('/v1/pump/<pumpId>/mode', methods=['GET', 'PUT'])
    async def pump_mode(pumpId):
        if pumpId not in state["pumps"]:
            return {"error": "Invalid pump ID"}, 400

        pump_ = state["pumps"][pumpId]

        if request.method == 'GET':
            return jsonify(pump_.mode)
        elif request.method == 'PUT':
            mode = await request.get_json(force=True)
            mode = PumpMode(mode["mode"])
            if mode == PumpMode.ON:
                pump_.enable()
            elif mode == PumpMode.OFF:
                pump_.disable()
            else:
                return {"error": "Invalid mode"}, 400
            return {}, 200
        else:
            return {}, 405

    @app.route('/v1/pump')
    def pump():
        return jsonify(list(state["pumps"].values()))

    @app.route('/v1/stream')
    async def stream():
        # If many events are queued, most likely the listener has disconnected.
        queue = Queue(MAX_SUBSCRIBER_QUEUE_LEN)

        @stream_with_context
        async def __stream():
            stream_subscribers.append(queue)

            while True:
                tag, message = await queue.get()
                data = TemperatureService.encoder.sse(tag, message)
                yield data

        return __stream(), {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Transfer-Encoding': 'chunked',
        }

    @app.route("/")
    async def get_landing_page():
        template = resource_string(__name__,
                                   'data/web-ui/templates/index.html')
        template = template.decode('utf-8')
        return await render_template_string(template)

    @app.route("/static/<file>")
    async def get_static(file):
        template = resource_string(__name__, 'data/web-ui/static/' + file)
        template = template.decode('utf-8')
        return template
