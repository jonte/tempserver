import logging
import os

from enum import Enum

if os.environ.get("DUMMY", False):
    from tempserver.gpiozero_dummy import PWMOutputDevice
else:
    from gpiozero import PWMOutputDevice


class HeaterMode(Enum):
    PID = "PID"
    OFF = "OFF"
    ON = "ON"


class Heater:
    def __init__(self, gpio_pin, name="Unknown", is_manual=False, sensor=None, pid=None, scheduler=None,
                 notify_change=None, id_=None):
        self.heating = False
        self.mode = HeaterMode.OFF
        self.name = name
        self.is_manual = is_manual
        self.heating_element = PWMOutputDevice(gpio_pin, frequency=1)
        self.sensor = sensor
        self.pid = pid
        self.scheduler = scheduler
        self.notify_change = notify_change
        self.id = id_
        self.scheduler.add_job(self.process_pid, 'interval', seconds=1, id="pid_iteration %s" % name)
        self.previous_level = -1

    def _set_mode(self, mode):
        if mode == HeaterMode.OFF:
            self.stop_heating()

        self.mode = mode
        self.publish_state()

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
        self.publish_state()

        logging.info("Heating element %s level: %f" % (self.name, level))
        self.heating = (level > 0)
        self.previous_level = level

    def stop_heating(self):
        return self._set_heating_level(0)

    def start_heating(self, level):
        return self._set_heating_level(level)

    def process_pid(self):
        self._set_heating_level(self.pid.output / 100.0)

    def publish_state(self):
        if self.notify_change:
            self.notify_change(("vessel-power-" + self.id,
                                self.heating_element.value * 100))
            self.notify_change(("vessel-heater-" + self.id, self))
