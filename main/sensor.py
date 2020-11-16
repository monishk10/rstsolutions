import Adafruit_DHT


class DHT:
    def __init__(self):
        # Temperature Sensor
        self.DHT_SENSOR = Adafruit_DHT.DHT22
        self.DHT_PIN = 4

    def read_temp_hum(self, unit):
        humidity, temperature = Adafruit_DHT.read_retry(
            self.DHT_SENSOR, self.DHT_PIN)
        if temperature is None or humidity is None:
            return (0, 0)
        if(unit == "F"):
            temperature = temperature * (9 / 5) + 32
        return (round(temperature, 2), round(humidity, 2))
