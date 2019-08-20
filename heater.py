import logging, os
from enum import Enum

if os.environ.get("DUMMY", False):
    from gpiozero_dummy import PWMOutputDevice
else:
    from gpiozero import PWMOutputDevice

class HeaterMode(Enum):
    PID = "PID"
    OFF = "OFF"
    ON = "ON"

class Heater:
    def __init__(self, gpio_pin, name = "Unknown", is_manual = False, sensor=None, pid = None, scheduler = None):
        self.heating = False
        self.mode = HeaterMode.OFF
        self.name = name
        self.is_manual = is_manual
        self.heating_element = PWMOutputDevice(gpio_pin, frequency = 1)
        self.sensor = sensor
        self.pid = pid
        self.scheduler = scheduler
        self.scheduler.add_job(self.process_pid, 'interval', seconds=1, id="pid_iteration %s" % name)

    def _set_mode(self, mode):
        if mode == HeaterMode.OFF:
            self.stop_heating()

        self.mode = mode

    def enable_pid(self):
        self._set_mode(HeaterMode.PID)

    def enable(self):
        self._set_mode(HeaterMode.ON)

    def disable(self):
        self._set_mode(HeaterMode.OFF)

    def _set_heating_level(self, level):
        if (self.mode == HeaterMode.OFF) and level > 0:
            return "Heater not enabled"

        self.heating_element.value = level

        logging.info("Heating element %s level: %f" % (self.name, level))
        self.heating = (level > 0)

    def stop_heating(self):
        return self._set_heating_level(0)

    def start_heating(self, level):
        return self._set_heating_level(level)

    def process_pid(self):
        self._set_heating_level(self.pid.output/100.0)
