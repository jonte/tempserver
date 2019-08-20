import random

class W1ThermSensor:
    THERM_SENSOR_DS18B20 = "ds18b20"

    def __init__(self, type = None, id = None):
        self.type = type
        self.id = id

    def get_temperature(self):
        return random.uniform(0, 100)
