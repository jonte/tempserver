from enum import Enum

class PumpMode(Enum):
    OFF = "OFF"
    ON = "ON"


class Pump:
    def __init__(self, gpio_pin, name, id_ = None, scheduler = None, notify_change = None):
        self.id = id_
        self.name = name
        self.mode = PumpMode.OFF
        self.notify_change = notify_change

    def set_mode(self, mode):
        self.mode = mode
        self.publish_state()

    def enable(self):
        self.set_mode(PumpMode.ON)

    def disable(self):
        self.set_mode(PumpMode.OFF)

    def publish_state(self):
        if self.notify_change:
            self.notify_change(("pump-mode-" + self.id, self.mode))
