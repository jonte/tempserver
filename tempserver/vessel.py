class Vessel:
    def __init__(self, id_, name, sensor=None, pid=None, heater=None):
        self.id = id_
        self.name = name
        self.sensor = sensor
        self.pid = pid
        self.heater = heater
