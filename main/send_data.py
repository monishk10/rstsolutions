import subprocess
import requests
from requests.auth import HTTPBasicAuth
import json


class DataUpload:
    def __init__(self):
        self.DEVICE_IP = subprocess.check_output(
            "hostname -I", shell=True).decode('utf-8').split(" ")[0]

        # Azure IoT Hub
        self.URI = 'temp-data.azure-devices.net'
        self.IOT_DEVICE_ID = 'mypi'
        self.SAS_TOKEN = "SharedAccessSignature sr=temp-data.azure-devices.net%2Fdevices%2Fmypi&sig=GhR8HWnqDL68Na9ygvui5dpJqxg%2BkT4IepS0evIQrDw%3D&se=1758159828"

        # JD Edwards API
        self.JDEDWARDS_API_URL = 'http://50.243.34.141:3345/jderest/v3/orchestrator/IoTDeviceTelemetry?'
        self.JDEDWARDS_USER = 'Vivek'
        self.JDEDWARDS_PASS = 'Vivek@1'
        self.DEVICE_NUMBER = "100"

    def send_message_azure(self, message):
        try:
            url = 'https://{0}/devices/{1}/messages/events?api-version=2016-11-14'.format(
                self.URI, self.IOT_DEVICE_ID)
            headers = {
                "Content-Type": "application/json",
                "Authorization": self.SAS_TOKEN
            }
            data = json.dumps(message)
            print(data)
            response = requests.post(url, data=data, headers=headers)
            print("Data sent to Azure")
        except:
            print("Connection error with Azure")

    def send_message_jdedwards(self, message):
        try:
            PARAMS = {
                'DeviceNumber': self.DEVICE_NUMBER,
                'IOTUniversalID': message["UUID"],
                'IPAddress': self.DEVICE_IP,
                'Temperature': message["temp"],
                'TemperatureUM': message["temp_unit"],
                'Weight': '0',
                'WeightUM': 'kg',
                'Latitude': message["lat"],
                'Longitude': message["lon"],
                'Precipitation': '0',
                'PrecipitationUM': 'A',
                'Humidity': message["humidity"],
                'HumidityUM': message["humidity_unit"]
            }
            response = requests.get(url=self.JDEDWARDS_API_URL, params=PARAMS,
                                    auth=HTTPBasicAuth(self.JDEDWARDS_USER, self.JDEDWARDS_PASS))
            print("Data sent to JD Edwards")
        except Exception as e:
            print(e)
            print("Connection error with JD Edwards")
