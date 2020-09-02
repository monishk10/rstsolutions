from base64 import b64encode, b64decode
from hashlib import sha256
from urllib.parse import quote_plus, urlencode
from hmac import HMAC
from datetime import datetime
from requests.auth import HTTPBasicAuth 
from geopy.geocoders import Nominatim
from keyrings.alt.file import PlaintextKeyring
import Adafruit_DHT
import requests
import json
import os
import time
import serial
import yagmail
import keyring.backend

 
# Temperature Sensor
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

# Serial port
SERIAL_PORT = "/dev/serial0"

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
IP_ADDRESS = '192.168.43.49'

# TRIGGER EVENT
EMAIL_TRIGGER_URL = 'https://maker.ifttt.com/trigger/temp_alert/with/key/dhdMjDRsVok5BEth3SmtTK'

# GPS
geolocator = Nominatim(user_agent="rst")

# EMAIL
keyring.set_keyring(PlaintextKeyring())
yag = yagmail.SMTP('monish.nyu')
email_list = ['monishk1001@gmail.com', 'mnk337@nyu.edu', 'vivek.patil1985@gmail.com']

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

def create_entry():
    URL = 'http://{}:7777/devices'.format(IP_ADDRESS)
    data = {
        "IOTUniversalID": UUID,
        "DeviceNumber": DEVICE_NUMBER,
        "IPAddress": IP_ADDRESS,
        "dataInterval": "300",
        "reboot": "0",
        "tempUnit": "F",
        "minTemp": "80",
        "maxTemp": "85"
    }

    response = requests.post(URL, data=data)     
    print(response.status_code)

# In the NMEA message, the position gets transmitted as:
# DDMM.MMMMM, where DD denotes the degrees and MM.MMMMM denotes
# the minutes. However, I want to convert this format to the following:
# DD.MMMM. This method converts a transmitted string to the desired format
def formatDegreesMinutes(coordinates, digits, direction):
    
    parts = coordinates.split(".")

    if (len(parts) != 2):
        return coordinates

    if (digits > 3 or digits < 2):
        return coordinates
    
    left = parts[0]
    right = parts[1]
    degrees = str(left[:digits])
    minutes = str(right[:3])

    sign = ""
    if (direction == 'S' or direction == 'W'):
        sign = "-"
    return sign + degrees + "." + minutes

# This method reads the data from the serial port, the GPS dongle is attached to,
# and then parses the NMEA messages it transmits.
# gps is the serial port, that's used to communicate with the GPS adapter
def getPositionData(gps):
    data = gps.readline().decode('utf-8')
    message = data[0:6]
    if (message == "$GPRMC"):
        # GPRMC = Recommended minimum specific GPS/Transit data
        # Reading the GPS fix data is an alternative approach that also works
        parts = data.split(",")
        if parts[2] == 'V':
            # V = Warning, most likely, there are no satellites in view...
            print("GPS receiver warning")
            return (-1.0,-1.0, "GPS Error")
        else:
            # Get the position data that was transmitted with the GPRMC message
            # In this example, I'm only interested in the longitude and latitude
            # for other values, that can be read, refer to: http://aprs.gids.nl/nmea/#rmc
            longitude = formatDegreesMinutes(parts[5], 3, parts[6])
            latitude = formatDegreesMinutes(parts[3], 2, parts[4])
            return (float(latitude), float(longitude), geolocator.reverse("{}, {}".format(latitude, longitude)))
    else:
        # Handle other NMEA messages and unsupported strings
        return (0.0,0.0, "No location")

def read_temp(unit):
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    if temperature is None or humidity is None:
        return (0,0)
    if(unit == "F"):
        temperature = temperature * (9 / 5) + 32
    return (temperature, humidity)

def get_api_vals():
    '''
        Data Codes
        0 - OK
        1 - DEVICE NOT FOUND
        2 - ERROR CONNECTING TO API
    '''
    data = {"code": 0}
    try:
        url = 'http://{}:7777/device/{}'.format(IP_ADDRESS,UUID)
        response = requests.get(url)
        response = response.content.decode('utf-8')
        data_json = json.loads(response)
        
        if (data_json["message"] == 'Device not found'):
            data["code"] = 1
        else:
            data["dataInterval"] = int(data_json["data"]["dataInterval"])
            data["tempUnit"] = data_json["data"]["tempUnit"]
            data["reboot"] = data_json["data"]["reboot"]
            data["minTemp"] = float(data_json["data"]["minTemp"])
            data["maxTemp"] = float(data_json["data"]["maxTemp"])
            data["minHum"] = float(data_json["data"]["minHum"])
            data["maxHum"] = float(data_json["data"]["maxHum"])
    except:
        data["code"] = 2

    return data

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
        print(response.content.decode('utf-8'))
    except:
        print("Connection error with Azure")

def send_message_jdedwards(temp, temp_unit, humidity, lat, lon):
    try:
        device_id_api = 'DeviceNumber=' + DEVICE_NUMBER
        iot_universal_id = 'IOTUniversalID=' + UUID
        ip_address = 'IPAddress=' + IP_ADDRESS
        temp_api = 'Temperature={:0.2f}&TemperatureUM={}'.format(temp,temp_unit)
        weight_api ='Weight=0&WeightUM=kg'
        location_api = 'Latitude={}&Longitude={}'.format(lat,lon)
        precipitation_api = 'Precipitation=0&PrecipitationUM=A'
        humidity_api = 'Humidity={:0.2f}&HumidityUM=%'.format(humidity)
        
        request_url = JDEDWARDS_API_URL + device_id_api + '&' + iot_universal_id + '&' + ip_address + '&' + temp_api + '&' + weight_api + '&' + location_api + '&' + precipitation_api + '&' + humidity_api
        response = requests.get(request_url, 
                    auth = HTTPBasicAuth(JDEDWARDS_USER, JDEDWARDS_PASS))
        print(response.content.decode('utf-8'))
    except:
        print("Connection error with JD Edwards") 

def trigger_temp_email(temp, temp_unit, state, location, lat, lon):
    try:
        subject = '{} Temp Alert'.format(state)
        content = [
            '<h2>Temperature Alert </h2>', 
            '<p>Temperature: {}° {} </p>'.format(round(temp,2), temp_unit), 
            '<p>Device Number: {}</p>'.format(DEVICE_NUMBER),
            '<p>UUID: {}</p>'.format(UUID),
            '<p>Location: {}({},{})</p>'.format(location, lat, lon),
            '<p>Time: {}</p>'.format(datetime.now()),
            '<a href="http://www.google.com">Link</a>'
            ]

        yag.send(email_list, subject, content)
        print("TEMP EMAIL SENT")
    except:
        print("Error sending temp email")

def trigger_hum_email(humidity, state, location, lat, lon):
    try:
        
        subject = '{} Humidity Alert'.format(state)
        content = [
            '<h2>Humidity Alert </h2>', 
            '<p>Humidity: {}{} </p>'.format(round(humidity,2), '%'), 
            '<p>Device Number: {}</p>'.format(DEVICE_NUMBER),
            '<p>UUID: {}</p>'.format(UUID),
            '<p>Location: {}({},{})</p>'.format(location, lat, lon),
            '<p>Time: {}</p>'.format(datetime.now()),
            '<a href="http://www.google.com">Link</a>'
            ]

        yag.send(email_list, subject, content)
        print("HUM EMAIL SENT")
    except:
        print("Error sending hum email")

if __name__ == '__main__':
    # 1. Generate UUID
    UUID = getserial()
    print("UUID: {}".format(UUID))

    # 2. Generate SAS Token
    token = generate_sas_token()

    # 3. Initialize variable
    counter = data_interval = reboot = lat = lon = 0
    temp_unit = 'C'
    prev_temp_state = 'ABNORMAL'
    curr_temp_state = ''
    prev_hum_state = 'ABNORMAL'
    curr_hum_state = ''
    running = True
    
    # 4. Create an entry
    # create_entry()

    gps = serial.Serial(SERIAL_PORT, baudrate = 9600, timeout = 0.5)
    while running:
        try:
            # 5. Check api values every 10 sec
            if (counter % 10 == 0):
                data = get_api_vals()

                # Check codes
                if(data["code"] == 1):
                    print("Device Not Found")
                    time.sleep(1)
                    continue
                elif(data["code"] == 2):
                    print("Invalid API. Check API again")
                    time.sleep(1)
                    break

                if (data["reboot"] == '1'):
                    os.system("sudo reboot")
                
                if (not(data["tempUnit"] == 'C' or data["tempUnit"] == 'F')):
                    temp_unit = 'C'
                else:
                    temp_unit = data["tempUnit"]

                data_interval = data["dataInterval"]
            
            # 6. Read temperature and humidity values
            temp, humidity = read_temp(temp_unit) 

            # 7. Send data to azure and JD Edwards if data interval time matches
            if (counter == 0):
                while (lon == 0 or lon == -1):
                    lat, lon, location = getPositionData(gps)

                print(location)
                message = { 
                    "temp": str(round(temp,2)), 
                    "tempUnit": temp_unit,
                    "humidity": str(round(humidity,2)),
                    "humidityUnit": '%', 
                    "lat": str(lat),
                    "lon": str(lon),
                    "time": str(datetime.now())
                }
                send_message_azure(token, message)
                send_message_jdedwards(temp, temp_unit, humidity, lat, lon)
            
            # 8. Trigger event if temp<minTemp or temp>maxTemp
            if (temp < data["minTemp"]):
                curr_temp_state = 'Low'
            elif(temp > data["maxTemp"]):
                curr_temp_state = 'High'
            else:
                curr_temp_state = 'Normal'

            
            if(prev_temp_state != curr_temp_state and curr_temp_state != 'Normal'):
                trigger_temp_email(temp, temp_unit, curr_temp_state, location, lat, lon)
            
            
            if (humidity < data["minHum"]):
                curr_hum_state = 'Low'
            elif(humidity > data["maxHum"]):
                curr_hum_state = 'High'
            else:
                curr_hum_state = 'Normal'

            
            if(prev_hum_state != curr_hum_state and curr_hum_state != 'Normal'):
                trigger_hum_email(humidity, curr_hum_state, location, lat, lon)
            

            print(counter, data_interval)
            time.sleep(0.7)
            counter = counter + 1
            prev_hum_state = curr_hum_state
            prev_temp_state = curr_temp_state
            if(counter >= data_interval):
                counter = 0
        except KeyboardInterrupt:
            gps.close()
            running = False
            print("Done")
