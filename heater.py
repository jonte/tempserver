import logging
from gpiozero import PWMOutputDevice

class Heater:
    def __init__(self, gpio_pin, name = "Unknown", is_manual = False, sensor=None):
        self.heating = False
        self.enabled = False
        self.name = name
        self.is_manual = is_manual
        self.heating_element = PWMOutputDevice(gpio_pin, frequency = (1.0 / 10))
        self.sensor = sensor

    def _set_enabled_state(self, enabled_state):
        if not enabled_state:
            self.stop_heating()

        self.enabled = enabled_state

    def enable(self):
        self._set_enabled_state(True)

    def disable(self):
        self._set_enabled_state(False)

    def _set_heating_level(self, level):
        if not self.enabled and level > 0:
            return "Heater not enabled"

        self.heating_element.value = level

        logging.info("Heating element level: %f" % level)
        self.heating = (level > 0)

    def stop_heating(self):
        return self._set_heating_level(0)

    def start_heating(self, level):
        return self._set_heating_level(level)
