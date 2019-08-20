from flask.json import JSONEncoder
#from sensor import Sensor
from heater import (Heater, HeaterMode)
from simple_pid import PID
from vessel import Vessel
from collections import deque
from temperature import Temperature
from power import Power
from pidtunings import PIDTunings
from flask import json

class Encoder(JSONEncoder):
    def sse(self, event, obj):
        s = "event: %s\ndata: %s\n\n" % (event, json.dumps(obj))
        return bytes(s, encoding="UTF-8")

    def default(self, obj):
#        if isinstance(obj, Sensor):
#            return {
#                    "temp": obj.temperature,
#                    "name": obj.name,
#                    "setpoint": obj.pid.setpoint if obj.pid else -1,
#                    "tempHistory": list(obj.tempHistory),
#                    "heating_stages": obj.heating_stages,
#                    "automation_state": obj.automation_state,
#            }
        if isinstance(obj, Heater):
            return {
                    "active": obj.heating,
                    "mode": {"mode": obj.mode.value},
                    "name": obj.name,
                    "is_manual": obj.is_manual,
                    "level": obj.heating_element.value * 100,
                    "pid": obj.pid,
            }
        if isinstance(obj, PID):
            return {
                    "setpoint": Temperature(obj.setpoint),
                    "output": obj.output,
                    "components": PIDTunings(obj.components),
                    "tunings": PIDTunings(obj.tunings),
            }
        if isinstance(obj, Vessel):
            return {
                    "id": obj.id,
                    "name": obj.name,
            }
        if isinstance(obj, deque):
            return list(obj)
        if isinstance(obj, Temperature):
            return {"temperature": obj.temperature,
                    "unit": obj.unit}
        if isinstance(obj, Power):
            return {"power": obj.power}
        if isinstance(obj, PIDTunings):
            return {
                    "Kp": obj.Kp,
                    "Ki": obj.Ki,
                    "Kd": obj.Kd}
        if isinstance(obj, HeaterMode):
            if obj == HeaterMode.ON:
                return {"mode:" "OFF"}
            elif obj == HeaterMode.OFF:
                return {"mode:" "ON"}
            elif obj == HeaterMode.PID:
                return {"mode:" "PID"}
            else:
                raise TypeError("Illegal heater mode")
        else:
            return JSONEncoder.default(self, obj)
