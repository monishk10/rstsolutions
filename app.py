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
JDEDWARDS_API_URL = 'http://50.243.34.141:3345/jderest/v3/orchestrator/F55IOT?'
JDEDWARDS_USER = 'Vivek'
JDEDWARDS_PASS = 'Vivek@1'

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

def send_message_azure(token, message):
    url = 'https://{0}/devices/{1}/messages/events?api-version=2016-11-14'.format(URI, IOT_DEVICE_ID)
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    data = json.dumps(message)
    print(data)
    response = requests.post(url, data=data, headers=headers)

def send_message_jdedwards(temp):
    temp_api = 'mnTemperature={:0.2f}'.format(temp)
    device_id_api = 'szDeviceFile=' + IOT_DEVICE_ID
    response = requests.get(JDEDWARDS_API_URL + temp_api + '&' + device_id_api, 
                auth = HTTPBasicAuth(JDEDWARDS_USER, JDEDWARDS_PASS))
    print(response.content) 

if __name__ == '__main__':
    # 1. Generate SAS Token
    token = generate_sas_token()

    # 2. Send Temperature to IoT Hub
    while True:
        temp = read_temp() 
        message = { "temp": str(temp) , "time": str(datetime.now())}
        send_message_azure(token, message)
        send_message_jdedwards(temp)
        time.sleep(1)
