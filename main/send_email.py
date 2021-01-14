import yagmail
import json
import requests
import keyring.backend
from keyrings.alt.file import PlaintextKeyring
from datetime import datetime


class EmailEventTrigger:
    def __init__(self):
        keyring.set_keyring(PlaintextKeyring())
        self.yag = yagmail.SMTP(
            {'info.rstsolutions@gmail.com': 'RSTSolutions-IoT Hub'})
        self.email_list = ['monish.kapadia@rstsolutions.com']

    def send_alert(self, data):
        try:
            url = 'https://rst-web.herokuapp.com/alerts/add'
            # url = 'http://10.0.0.214:5000/alerts/add'
            headers = {
                "Content-Type": "application/json",
            }
            data = json.dumps(data)
            response = requests.post(url, data=data, headers=headers)
            print("Alert sent")
        except Exception as e:
            print("Error creating an alert")

    def trigger_email(self, data):
        try:
            subject = '{} {} Alert'.format(data["state"], data["sensor"])
            content = [
                '<h2>{} {} Alert </h2>'.format(data["state"], data["sensor"]),
                '<p>{}: {}{} </p>'.format(data["sensor"],
                                          data["value"], data["unit"]),
                '<p>Device Number: {}</p>'.format(data["device_number"]),
                '<p>UUID: {}</p>'.format(data["UUID"]),
                '<p>Location: {}({},{})</p>'.format(
                    data["location"], data["lat"], data["lon"]),
                '<p>Time: {}</p>'.format(datetime.now()),
                '<a href="http://www.google.com">Link</a>'
            ]

            self.yag.send(self.email_list, subject, content)
            print("{} EMAIL SENT".format(data["sensor"]))
        except Exception as e:
            print("Error sending {} email".format(data["sensor"]))
