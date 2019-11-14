from collections import deque
from flask import json
from flask.json import JSONEncoder
from simple_pid import PID

from tempserver.heater import (Heater, HeaterMode)
from tempserver.pidtunings import PIDTunings
from tempserver.power import Power
from tempserver.temperature import Temperature
from tempserver.vessel import Vessel


class Encoder(JSONEncoder):
    def sse(self, event, obj):
        s = "event: %s\ndata: %s\n\n" % (event, json.dumps(obj))
        return bytes(s, encoding="UTF-8")

    def default(self, obj):
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
