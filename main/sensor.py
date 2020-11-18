import sys
import pigpio
import DHT

class DHT_SENSOR:
    def __init__(self):
        # Temperature Sensor
        self.PI = pigpio.pi()
        self.GPIO_PIN = 4

    def pi_connected(self):
        if not self.PI.connected:
            return False
        return True

    def close_pi_sensor(self):
        self.sensor.cancel()
        self.PI.stop()

    def read_temp_hum(self, unit):
        if self.pi_connected():
            self.sensor = DHT.sensor(self.PI, self.GPIO_PIN)
            data = self.sensor.read()
            temperature = data[2]
            humidity = data[3]
            if(unit == "F"):
                temperature = temperature * (9 / 5) + 32
            self.close_pi_sensor()
            return (round(temperature, 2), round(humidity, 2))
        else:
            return (-1000, -1000)
