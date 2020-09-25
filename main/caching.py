import json
import send_data


class Caching:
    def __init__(self):
        with open('/home/pi/rstsolutions/main/cache.txt', 'r') as file:
            self.lines = len(file.readlines())
        self.data_uploader = send_data.DataUpload()

    def store_data(self, data):
        print("[Caching]Storing the data")
        with open('/home/pi/rstsolutions/main/cache.txt', 'a') as file:
            file.write(data)
            file.write("\n")
            self.lines = self.lines+1

    def upload_data(self):
        if (self.lines > 0):
            print("[Caching]Uploading data")
            while (self.lines > 0):
                with open('/home/pi/rstsolutions/main/cache.txt', 'r') as file:
                    self.data = file.readlines()
                    message = json.loads(self.data[0])
                    print("[Caching]Uploading")
                    self.data_uploader.send_message_azure(message)
                    self.data_uploader.send_message_jdedwards(message)
                    self.data = self.data[1:]
                with open('/home/pi/rstsolutions/main/cache.txt', 'w') as file:
                    file.writelines(self.data)
                    self.lines = self.lines - 1
