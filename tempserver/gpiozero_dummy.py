class PWMOutputDevice:
    value = 0

    def __init__(self, pin, frequency):
        self.pin = pin
        self.frequency = frequency
