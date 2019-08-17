class Vessel:
    def __init__(self, id, name, sensor=None, pid=None, heater=None):
        self.id = id
        self.name = name
        self.sensor = sensor
        self.pid = pid
        self.heater = heater
