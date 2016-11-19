import re, sys
import paho.mqtt.client as mqtt
import threading
import time
import ev3dev.ev3 as ev3
import json

'''
Organization ID   p38zh6
Device Type    Lego
Device ID     LegoEV3
Authentication Method   token
Authentication Token   dejan123
'''


class myThread(threading.Thread):
    def __init__(self, thread_id, run_event):
        # Thread init
        print("Initialising thread")
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.run_event = run_event

    def run(self):
        print("Thread started")
        publishData(self.run_event)
        print("Thread stopped")


class MindstormBluemix():
    def __init__(self):
        # Ibm Bluemix cloud parameters
        self.org_id = "p38zh6"
        self.device_type = "Lego"
        self.device_name = "LegoEV3"
        self.token = "dejan123"
        self.auth_type = "use-token-auth"
        self.port = 1883
        self.subscriber_topic = "iot-2/cmd/get_data/fmt/json"
        self.publisher_topic = "iot-2/evt/mindstorm-status/fmt/json"

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

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print("On subscribe: " + str(mid) + " " + str(granted_qos))

    def on_publish(self, client, userdata, mid):
        print("On publish: " + str(mid))

    # The callback for then a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        #print("Topic: " + msg.topic + "Payload: " + str(msg.payload))
        # ev3.Sound.speak('Message received').wait()
        handle_message(msg)


def handle_message(msg):
    decoded_msg = msg.payload.decode("utf-8")
    payload = json.loads(decoded_msg)
    # print(payload['voice'])
    if 'voice' in payload:
        ev3.Sound.speak(payload['voice']).wait()
    if 'robotControl' in payload:
        print("Spinning motor")
        m = ev3.MediumMotor('outA')
        m.run_timed(time_sp=3000, speed_sp=500)



def publishData(run_event):
    while run_event.is_set():
        try:
            data = 123
            payload = ("{\"d\": \"%d\"}" % data)
            client.publish(mindBlue.publisher_topic, payload)
            # print("Data sent")
            time.sleep(10)
        except:
            print("Err")


mindBlue = MindstormBluemix()

# Script need to wait for system startup
if mindBlue.mode != "develop":
    time.sleep(20)

client = mqtt.Client(mindBlue.make_mqtt_client_info())
client.on_connect = mindBlue.on_connect
client.on_message = mindBlue.on_message
client.on_subscribe = mindBlue.on_subscribe
client.on_publish = mindBlue.on_publish
client.username_pw_set(mindBlue.auth_type, mindBlue.token)
client.connect(mindBlue.make_connect_info(), mindBlue.port, 60)
client.subscribe(mindBlue.subscriber_topic, 0)


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
