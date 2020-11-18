import json
import requests


class ServerData:
    def __init__(self):
        self.MONGODB_SERVER = 'https://rst-web.herokuapp.com'
        self.UUID = "0000000000000000"
        try:
            f = open('/proc/cpuinfo', 'r')
            for line in f:
                if line[0:6] == 'Serial':
                    self.UUID = line[10:26]
                    print(self.UUID)
            f.close()
        except:
            self.UUID = "ERROR000000000"
            print("[UUID]Error searching for UUID")

    def get_UUID(self):
        return self.UUID

    def reboot_reset(self):
        try:
            URL = '{}/devices/{}'.format(self.MONGODB_SERVER, self.UUID)
            response = requests.get(URL)
            response = response.content.decode('utf-8')
            data_json = json.loads(response)
            data_json.pop('_id', None)
            data_json.pop('createdAt', None)
            data_json.pop('updatedAt', None)
            data_json.pop('__v', None)
            data_json["reboot"] = "0"

            URL = '{}/devices/update'.format(self.MONGODB_SERVER)
            newHeaders = {'Content-type': 'application/json',
                          'Accept': 'text/plain'}
            response = requests.post(
                URL, headers=newHeaders, data=json.dumps(data_json))
        except:
            print("[REBOOT]Error getting api value")

    def get_api_vals(self):
        '''
            Data Codes
            0 - OK
            1 - DEVICE NOT FOUND
            2 - ERROR CONNECTING TO API
            3 - INTERNET CONNECTION LOST
        '''
        data = {"code": 0}
        try:
            URL = '{}/devices/{}'.format(self.MONGODB_SERVER, self.UUID)
            response = requests.get(URL)
            response = response.content.decode('utf-8')
            if (response == 'null'):
                data["code"] = 1
            else:
                data_json = json.loads(response)
                data["DeviceNumber"] = int(data_json["DeviceNumber"])
                data["IPAddress"] = data_json["IPAddress"]
                data["dataInterval"] = int(data_json["dataInterval"])
                data["reboot"] = int(data_json["reboot"])
                data["tempUnit"] = data_json["tempUnit"]
                data["minTemp"] = float(data_json["minTemp"])
                data["maxTemp"] = float(data_json["maxTemp"])
                data["minHum"] = float(data_json["minHum"])
                data["maxHum"] = float(data_json["maxHum"])

                if (not(data["tempUnit"] == 'C' or data["tempUnit"] == 'F')):
                    data["tempUnit"] = 'C'
        except:
            if (internet_check()):
                data["code"] = 2
            else:
                data["code"] = 3

        return data

    def internet_check(self):
        try:
            requests.get('http://216.58.192.142', timeout=1)
            return True
        except requests.exceptions.Timeout:
            return False
