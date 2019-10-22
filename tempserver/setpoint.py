from temperature import Temperature

class Setpoint:
    def __init__(self, setpoint, unit = "C"):
        self.setpoint = Temperature(setpoint, unit)
