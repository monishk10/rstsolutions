from base64 import b64encode, b64decode
from hashlib import sha256
from urllib.parse import quote_plus, urlencode
from hmac import HMAC
from datetime import datetime
from requests.auth import HTTPBasicAuth 
import Adafruit_DHT
import requests
import json
import os
import time
 
# Temperature Sensor
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

# Azure IoT Hub
URI = 'temp-data.azure-devices.net'
KEY = '5XS/8hcMsGrM3nWhAl/UdNW+GrGbcbQD5ZukByV2h28='
IOT_DEVICE_ID = 'mypi'
POLICY = 'iothubowner'

# JD Edwards API
JDEDWARDS_API_URL = 'http://50.243.34.141:3345/jderest/v3/orchestrator/IoTDeviceTelemetry?'
JDEDWARDS_USER = 'Vivek'
JDEDWARDS_PASS = 'Vivek@1'
DEVICE_NUMBER = '100'
IP_ADDRESS = '192.168.1.106'

def getserial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:6]=='Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"

    return cpuserial


def generate_sas_token():
    expiry = str(int(time.time() + 3600))
    sign_key = (URI + '\n' + expiry).encode('utf-8')
    signature = b64encode(HMAC(b64decode(KEY), sign_key, sha256).digest())

    rawtoken = {
        'sr' :  URI,
        'sig': signature,
        'se' : expiry
    }

    rawtoken['skn'] = POLICY

    return 'SharedAccessSignature ' + urlencode(rawtoken)

def read_temp(unit):
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    if temperature is None or humidity is None:
        return (0,0)
    if(unit == "F"):
        temperature = temperature * (9 / 5) + 32
    return (temperature, humidity)

def get_api_vals():
    try:
        url = 'http://192.168.1.106:7777/device/{0}'.format(UUID)
        response = requests.get(url)
        response = response.content.decode('utf-8')
        data_json = json.loads(response)
        if (data_json["message"] == 'Device not found'):
            return (0,0)
        else:
            return int(data_json["data"]["dataInterval"]), data_json["data"]["tempUnit"], data_json["data"]["reboot"]
    except:
        return (-1,-1,-1)

def send_message_azure(token, message):
    try:
        url = 'https://{0}/devices/{1}/messages/events?api-version=2016-11-14'.format(URI, IOT_DEVICE_ID)
        headers = {
            "Content-Type": "application/json",
            "Authorization": token
        }
        data = json.dumps(message)
        print(data)
        response = requests.post(url, data=data, headers=headers)
    except:
        print("Connection error with Azure")

def send_message_jdedwards(temp, temp_unit, humidity):
    try:
        iot_universal_id = 'IOTUniversalID=' + UUID
        device_id_api = 'DeviceNumber=' + DEVICE_NUMBER
        ip_address = 'IPAddress=' + IP_ADDRESS
        temp_api = 'Temperature={:0.2f}&TemperatureUM={}'.format(temp,temp_unit)
        humidity_api = 'Humidity={:0.2f}&HumidityUM=%'.format(humidity)
        
        request_url = JDEDWARDS_API_URL + iot_universal_id + '&' + device_id_api + '&' + ip_address + '&' + temp_api + '&' + humidity_api
        print(request_url)
        response = requests.get(request_url, 
                    auth = HTTPBasicAuth(JDEDWARDS_USER, JDEDWARDS_PASS))
        print(response.content)
    except:
        print("Connection error with JD Edwards") 

if __name__ == '__main__':
    # 1. Generate UUID
    UUID = getserial()
    print("UUID: {}".format(UUID))

    # 2. Generate SAS Token
    token = generate_sas_token()

    # 3. Initialize variable
    counter = data_interval = reboot = 0
    temp_unit = 'C'
    
    # 4. Process all the info
    while True:
        # 5. Check api values every 10 sec
        if (counter % 10 == 0):
            data_interval, temp_unit, reboot = get_api_vals()
            if (reboot == '1'):
                os.system("sudo reboot")
            if (data_interval == -1):
                print("Invalid API")
                continue
            if (not(temp_unit == 'C' or temp_unit == 'F')):
                temp_unit = 'C'
        
        # 6. Read temperature and humidity values
        temp, humidity = read_temp(temp_unit) 

        # 7. Send data to azure and JD Edwards if data interval time matches
        if (counter == 0):
            message = { "temp": str(round(temp,2)) , "humidity": str(round(humidity,2)), "time": str(datetime.now())}
            send_message_azure(token, message)
            send_message_jdedwards(temp, temp_unit, humidity)
        
        print(counter, data_interval)
        time.sleep(1)
        counter = counter + 1
        if(counter >= data_interval):
            counter = 0
