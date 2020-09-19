import yagmail
import keyring.backend
from keyrings.alt.file import PlaintextKeyring
from datetime import datetime


class EmailEventTrigger:
    def __init__(self):
        keyring.set_keyring(PlaintextKeyring())
        self.yag = yagmail.SMTP('monish.nyu')
        self.email_list = ['monish.kapadia@rstsolutions.com']

    def trigger_email(self, data):
        try:
            subject = '{} {} Alert'.format(data["state"], data["name"])
            content = [
                '<h2>{} Alert </h2>'.format(data["name"]),
                '<p>{}: {}{} </p>'.format(data["name"],
                                          data["value"], data["unit"]),
                '<p>Device Number: {}</p>'.format(data["device_number"]),
                '<p>UUID: {}</p>'.format(data["UUID"]),
                '<p>Location: {}({},{})</p>'.format(
                    data["location"], data["lat"], data["lon"]),
                '<p>Time: {}</p>'.format(datetime.now()),
                '<a href="http://www.google.com">Link</a>'
            ]

            self.yag.send(self.email_list, subject, content)
            print("{} EMAIL SENT".format(data["name"]))
        except Exception as e:
            print(e)
            print("Error sending {} email".format(data["name"]))
