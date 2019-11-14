import random


class W1ThermSensor:
    THERM_SENSOR_DS18B20 = "ds18b20"

    def __init__(self, type_=None, id=None):
        self.type = type_
        self.id = id
        self.prev_temp = 40

    def get_temperature(self):
        self.prev_temp = self.prev_temp + random.uniform(-2, 2)
        return self.prev_temp
