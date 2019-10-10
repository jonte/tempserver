import logging, os, time
from collections import deque
from temperature import Temperature
from power import Power
from jsonencoding import Encoder

if os.environ.get("DUMMY", False):
    from w1thermsensor_dummy import W1ThermSensor
else:
    from w1thermsensor import W1ThermSensor

class Sensor:
    def __init__(self, id = None, name = "Unknown", setpoint = 10, scheduler=None, sensor_id="", pid = None, notify_change = None):
        self.temperature = Temperature(0)
        self.name = name
        self.w1_sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, sensor_id)
        self.setpoint = setpoint
        self.tempHistory = deque(maxlen=500)
        self.heating_stages = []
        self.automation_state = "STOPPED"
        self.scheduler = scheduler
        self.pid = pid
        self.id = id
        self.notify_change = notify_change
#        scheduler.add_job(self.automation_iteration, 'interval', seconds=1)
        scheduler.add_job(self.update_temp, 'interval', seconds=5)
        if sensor_id == "":
            logging.warn("Sensor ID for %s is blank - using first available sensor" % name)
        logging.debug("Sensor ID for %s: %s" % (name, sensor_id))

#    def automation_iteration(self):
#        def should_run(stage, curr_temp):
#            if stage["time_remaining"] <= 0:
#                return False
#
#            if abs(stage["temp"] - curr_temp) < 1:
#                return True
#
#
#        if self.automation_state != "STARTED":
#            return
#
#
#        for stage in self.heating_stages:
#            if stage["time_remaining"] > 0:
#                self.setpoint = stage["temp"]
#                break
#
#        for i in range(0, len(self.heating_stages)):
#            if should_run(self.heating_stages[i], self.temperature):
#                self.heating_stages[i]["active"] = True
#
#            if self.heating_stages[i]["active"]:
#                self.heating_stages[i]["time_remaining"] = self.heating_stages[i]["time_remaining"] - 1
#                if self.heating_stages[i]["time_remaining"] <= 0:
#                    self.heating_stages[i]["active"] = False
#
#    def start_automation(self):
#        self.automation_state = "STARTED"
#        self.automation_iteration()
#
#    def stop_automation(self):
#        self.automation_state = "STOPPED"
#        self.automation_iteration()
#
#    def pause_automation(self):
#        self.automation_state = "PAUSED"
#        self.automation_iteration()

    def add_heating_stage(self, name, time, temp):
        id = 0

        if (self.heating_stages):
            id = 1 + self.heating_stages[-1]["id"]

        stage = {
            "id": id,
            "name": name,
            "time": time,
            "temp": temp,
            "time_remaining": time,
            "active": False
        }

        self.heating_stages.append(stage)

    def remove_heating_stage(self, id):
        self.heating_stages = [x for x in self.heating_stages if x["id"] != id]

    def update_temp(self):
        before = time.time()
        self.temperature.temperature = self.w1_sensor.get_temperature()
        history_obj = {
                    "temperature": self.temperature,
                    "heater_level": Power(self.pid.output) if self.pid else 0,
                    "setpoint": Temperature(self.pid.setpoint) if self.pid else 0,
                    "date": int(time.time())}

        if self.notify_change:
            self.notify_change(("vessel-temperature-" + self.id, self.temperature))
            self.notify_change(("vessel-chart-" + self.id, history_obj))

        if self.pid:
            self.pid.output = self.pid(self.temperature.temperature)

        logging.info("Updating sensor '{}' took {} s".format(self.name, time.time() - before))
