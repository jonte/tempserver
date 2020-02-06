import asyncio
import concurrent
import logging
import os
import time
from collections import deque

from tempserver.power import Power
from tempserver.temperature import Temperature

if os.environ.get("DUMMY", False):
    from tempserver.w1thermsensor_dummy import W1ThermSensor
else:
    from w1thermsensor import W1ThermSensor


class Sensor:
    def __init__(self, id_=None, name="Unknown", setpoint=10, sensor_id="",
                 temp_offset=0.0, pid=None, notify_change=None):
        self.temperature = Temperature(0)
        self.name = name
        self.w1_sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20,
                                       sensor_id, offset=temp_offset)
        self.setpoint = setpoint
        self.tempHistory = deque(maxlen=500)
        self.heating_stages = []
        self.automation_state = "STOPPED"
        self.pid = pid
        self.id = id_
        self.notify_change = notify_change
        if sensor_id == "":
            logging.warning("Sensor ID for %s is blank - " +
                            "using first available sensor" % name)
        logging.debug("Sensor ID for %s: %s" % (name, sensor_id))

        asyncio.create_task(self.update_temp())

    def add_heating_stage(self, name, time_, temp):
        id_ = 0

        if self.heating_stages:
            id_ = 1 + self.heating_stages[-1]["id"]

        stage = {
            "id": id_,
            "name": name,
            "time": time_,
            "temp": temp,
            "time_remaining": time_,
            "active": False
        }

        self.heating_stages.append(stage)

    def remove_heating_stage(self, id_):
        self.heating_stages = [x for x in self.heating_stages
                               if x["id"] != id_]

    async def update_temp(self):
        loop = asyncio.get_running_loop()

        while True:
            before = time.time()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                self.temperature.temperature =\
                    await loop.run_in_executor(pool,
                                               self.w1_sensor.get_temperature)

            history_obj = {
                "temperature": self.temperature,
                "heater_level": Power(self.pid.output) if self.pid else 0,
                "setpoint": Temperature(self.pid.setpoint) if self.pid else 0,
                "date": int(time.time())}

            if self.notify_change:
                self.notify_change(("vessel-temperature-" + self.id,
                                    self.temperature))
                self.notify_change(("vessel-chart-" + self.id, history_obj))

            if self.pid:
                self.pid.output = self.pid(self.temperature.temperature)

            logging.info("Updating sensor '{}' took {} s".format(self.name,
                         time.time() - before))
