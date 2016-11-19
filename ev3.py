import re, sys
import paho.mqtt.client as mqtt
import threading
import time


class myThread(threading.Thread):
    def __init__(self, thread_id, run_event):
        # Thread init
        print("Initialising thread")
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.run_event = run_event

    def run(self):
        print("Thread started")
        # do something
        # TODO
        print("Thread stopped")


'''
Organization ID   p38zh6
Device Type    Lego
Device ID     LegoEV3
Authentication Method   token
Authentication Token   dejan123
'''

class MindstormBluemix():
    def __init__(self):
        # Ibm Bluemix cloud parameters
        self.org_id = "p38zh6"
        self.device_type = "LEgo"
        self.device_name = "LegoEV3"
        self.token = "dejan123"
        self.auth_type = "use-token-auth"
        self.port = 1883

        # program mode
        self.mode = "develop"  # change this to system when using on Mindstorm

    # format: d:<organisation-id>:<device-type>:<device-name>
    def make_mqtt_client_info(self):
        return "d:" + self.org_id + ":" + self.device_type + ":" + self.device_name

    def make_connect_info(self):
        return self.org_id + ".messaging.internetofthings.ibmcloud.com"

    # Callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

    # The callback for then a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))


mindBlue = MindstormBluemix()

# Script need to wait for system startup
if mindBlue.mode != "develop":
    time.sleep(20)

client = mqtt.Client(mindBlue.make_mqtt_client_info())
client.on_connect = mindBlue.on_connect
client.on_message = mindBlue.on_message
client.username_pw_set(mindBlue.auth_type, mindBlue.token)
client.connect(mindBlue.make_connect_info(), mindBlue.port, 15)



# Start thread
_run_event = threading.Event()
_run_event.set()
t = myThread(1, _run_event)
t.start()
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("Stopping thread ...")
    _run_event.clear()
    t.join()
    print("Disconnecting client.")
    client.disconnect()
    print("Goodbye!")
