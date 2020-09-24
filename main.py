from datetime import datetime
import json
import time
import concurrent.futures
import sensor
import location_service
import server_data
import send_data
import send_email
import caching


def wait():
    time.sleep(1)


if __name__ == '__main__':
    print('###############################')
    print('#                             #')
    print('#      IoT Device Tracker     #')
    print('#                             #')
    print('###############################')

    dht = sensor.DHT()
    gps = location_service.GPS()
    device_data = server_data.ServerData()
    data_uploader = send_data.DataUpload()
    email_trigger = send_email.EmailEventTrigger()
    cache_manager = caching.Caching()


    counter = data_interval = 0
    running = internet_connection = True
    prev_state = {"Temp": "ABNORMAL", "Hum": "ABNORMAL"}
    curr_state = {"Temp": "", "Hum": ""}
    curr_sensor_value = {"HumUnit": "%"}

    while running:
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                time_wait = executor.submit(wait)
                # Check api values every 10 sec
                if (counter % 10 == 0):
                    data = device_data.get_api_vals()
                    internet_connection = True

                    if(data["code"] == 1):
                        print("[MAIN]Device Not Found")
                        continue
                    elif(data["code"] == 2):
                        print("[MAIN]Invalid API. Check API again")
                        break
                    elif(data["code"] == 3):
                        internet_connection = False

                    if (data["reboot"] == 1 and internet_connection):
                        print("[MAIN]Rebooting")
                        device_data.reboot_reset()

                    data_interval = data["dataInterval"]
                    curr_sensor_value["TempUnit"] = "° {}".format(data["tempUnit"])

                    # Read temperature and humidity values
                    curr_sensor_value["Temp"], curr_sensor_value["Hum"] = dht.read_temp(data["tempUnit"])

                    # Check Trigger event
                    for key in curr_state:
                        if (curr_sensor_value[key] < data["min{}".format(key)]):
                            curr_state[key] = 'Low'
                        elif(curr_sensor_value[key] > data["max{}".format(key)]):
                            curr_state[key] = 'High'
                        else:
                            curr_state[key] = 'Normal'

                # Send data to azure and JD Edwards if data interval time matches
                if (counter <= 0):
                    counter = 0
                    curr_sensor_value["lat"], curr_sensor_value["lon"] = gps.getData()
                    message = {
                        "UUID": device_data.get_UUID(),
                        "temp": str(curr_sensor_value["Temp"]),
                        "temp_unit": data["tempUnit"],
                        "humidity": str(curr_sensor_value["Hum"]),
                        "humidity_unit": '%',
                        "lat": str(curr_sensor_value["lat"]),
                        "lon": str(curr_sensor_value["lon"]),
                        "time": str(datetime.now())
                    }
                    if (internet_connection):
                        cache_manager.upload_data()
                        executor.submit(data_uploader.send_message_azure, message)
                        executor.submit(data_uploader.send_message_jdedwards, message)
                    else:
                        print("[MAIN]No internet")
                        cache_manager.store_data(json.dumps(message))

                # Trigger email
                for key in curr_state:
                    if(prev_state[key] != curr_state[key] and curr_state[key] != 'Normal' and internet_connection):
                        device_info = {
                            "name": f"{'Temperature' if key=='Temp' else 'Humidity'}",
                            "UUID": device_data.get_UUID(),
                            "state": curr_state[key],
                            "value": curr_sensor_value[key],
                            "unit": curr_sensor_value["{}Unit".format(key)],
                            "device_number": data_uploader.DEVICE_NUMBER,
                            "location": gps.getLocation(curr_sensor_value["lat"], curr_sensor_value["lon"]),
                            "lat": curr_sensor_value["lat"],
                            "lon": curr_sensor_value["lon"]
                        }
                        executor.submit(email_trigger.trigger_email, device_info)

                time_wait.result()

                print('Time left: {} seconds'.format(data_interval - counter))
                counter = counter + 1

                for key in curr_state:
                    prev_state[key] = curr_state[key]

                if(counter >= data_interval):
                    counter = 0
        except KeyboardInterrupt:
            running = False
            print("Done")
