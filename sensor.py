import logging
from w1thermsensor import W1ThermSensor
from gpiozero import LED
import time
from collections import deque

class Sensor:
    def __init__(self, start_temp = 0, name = "Unknown", setpoint = 10, scheduler=None, sensor_id=""):
        self.temperature = start_temp
        self.name = name
        self.w1_sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, sensor_id)
        self.setpoint = setpoint
        self.tempHistory = deque(maxlen=500)
        self.heating_stages = []
        self.automation_state = "STOPPED"
        self.scheduler = scheduler
        scheduler.add_job(self.automation_iteration, 'interval', seconds=1)
        if sensor_id == "":
            logging.warn("Sensor ID for %s is blank - using first available sensor" % name)
        logging.debug("Sensor ID for %s: %s" % (name, sensor_id))

    def automation_iteration(self):
        def should_run(stage, curr_temp):
            if stage["time_remaining"] <= 0:
                return False

            if abs(stage["temp"] - curr_temp) < 1:
                return True


        if self.automation_state != "STARTED":
            return


        for stage in self.heating_stages:
            if stage["time_remaining"] > 0:
                self.setpoint = stage["temp"]
                break

        for i in range(0, len(self.heating_stages)):
            if should_run(self.heating_stages[i], self.temperature):
                self.heating_stages[i]["active"] = True

            if self.heating_stages[i]["active"]:
                self.heating_stages[i]["time_remaining"] = self.heating_stages[i]["time_remaining"] - 1
                if self.heating_stages[i]["time_remaining"] <= 0:
                    self.heating_stages[i]["active"] = False

    def start_automation(self):
        self.automation_state = "STARTED"
        self.automation_iteration()

    def stop_automation(self):
        self.automation_state = "STOPPED"
        self.automation_iteration()

    def pause_automation(self):
        self.automation_state = "PAUSED"
        self.automation_iteration()

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
        self.temperature = self.w1_sensor.get_temperature()
        self.tempHistory.append(
                {
                    "temp": self.temperature,
                    "date": int(time.time())},
                )

    def setSetpoint(self, setpoint):
        if self.automation_state != "STOPPED":
            return "Sensor is controlled by automation, will not override setpoint"
        if not setpoint.isnumeric():
            return "Setpoint is not numeric"

        self.setpoint = float(setpoint)
