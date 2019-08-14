from flask.json import JSONEncoder
from sensor import Sensor
from heater import Heater

class Encoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Sensor):
            return {
                    "temp": obj.temperature,
                    "name": obj.name,
                    "setpoint": obj.setpoint,
                    "tempHistory": list(obj.tempHistory),
                    "heating_stages": obj.heating_stages,
                    "automation_state": obj.automation_state,
            }
        if isinstance(obj, Heater):
            return {
                    "active": obj.heating,
                    "enabled": obj.enabled,
                    "name": obj.name,
                    "is_manual": obj.is_manual,
                    "level": obj.heating_element.value * 100,
            }
        else:
            return JSONEncoder.default(self, obj)
