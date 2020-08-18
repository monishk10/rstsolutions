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
TEMP_UNIT = 'Celsius'

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

UUID = getserial()
print(UUID)

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

def read_temp():
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    if temperature is None:
        return 0
    return temperature

def get_api_vals():
    try:
        url = 'http://192.168.1.106:7777/device/{0}'.format(UUID)
        response = requests.get(url)
        response = response.content.decode('utf-8')
        data_json = json.loads(response)
        if (data_json["message"] == 'Device not found'):
            return (0,0)
        else:
            return int(data_json["data"]["tempInterval"]), data_json["data"]["reboot"]
    except:
        return (-1,-1)

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

def send_message_jdedwards(temp):
    try:
        iot_universal_id = 'IOTUniversalID=' + UUID
        device_id_api = 'DeviceNumber=' + DEVICE_NUMBER
        ip_address = 'IPAddress=' + IP_ADDRESS
        temp_api = 'Temperature={:0.2f}&TemperatureUM={}'.format(temp,TEMP_UNIT)
        
        response = requests.get(JDEDWARDS_API_URL + iot_universal_id + '&' + device_id_api + '&' + ip_address + '&' + temp_api, 
                    auth = HTTPBasicAuth(JDEDWARDS_USER, JDEDWARDS_PASS))
        print(response.content)
    except:
        print("Connection error with JD Edwards") 

if __name__ == '__main__':
    # 1. Generate SAS Token
    token = generate_sas_token()
    counter = 0
    temp_interval = 0
    reboot = 0
    
    # 2. Send Temperature to IoT Hub
    while True:
        temp = read_temp() 
        if (counter % 10 == 0):
            temp_interval, reboot = get_api_vals()
            if (temp_interval == -1):
                print("Invalid API")
                continue
        if (counter == 0 or temp > 40):
            counter = 0
            message = { "temp": str(temp) , "time": str(datetime.now())}
            send_message_azure(token, message)
            send_message_jdedwards(temp)
        print(counter, temp_interval)
        time.sleep(1)
        counter = counter + 1
        if(counter >= temp_interval):
            counter = 0
