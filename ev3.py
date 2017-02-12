import re, sys
import paho.mqtt.client as mqtt
import threading
import time
import ev3dev.ev3 as ev3
import json


class myThread(threading.Thread):
    def __init__(self, thread_id, run_event):
        # Thread init
        print("Initialising thread")
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.run_event = run_event

    def run(self):
        print("Thread started")
        publish_data(self.run_event)
        print("Thread stopped")


class MindstormBluemix():
    def __init__(self):
        # Ibm Bluemix cloud parameters
        self.org_id = "OrgId"  # Your organization ID
        self.device_type = "Lego"  # Device type (you've defined it on Bluemix iot platform)
        self.device_name = "LegoEV3"  # Device name (you've defined it on Bluemix iot platform)
        self.token = "Password"  # Authentication token (you've defined it on Bluemix iot platform)
        self.auth_type = "use-token-auth"  # Do not change
        self.port = 1883  # Do not change
        self.subscriber_topic = "iot-2/cmd/get_data/fmt/json"
        self.publisher_topic = "iot-2/evt/mindstorm-status/fmt/json"

        # Program mode
        self.mode = "develop"  # change this to system, if you start script on system startup (on robot)

    # Format: d:<organisation-id>:<device-type>:<device-name>
    def make_mqtt_client_info(self):
        return "d:" + self.org_id + ":" + self.device_type + ":" + self.device_name

    # Make connect info
    def make_connect_info(self):
        return self.org_id + ".messaging.internetofthings.ibmcloud.com"

    # Callback when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        ev3.Sound.speak("I robot connected to Bluemix. Welcome to IBM Innovation center Ljubljana").wait()

    # Callback when robot subscribes to a topic
    def on_subscribe(self, client, userdata, mid, granted_qos):
        print("On subscribe: " + str(mid) + " " + str(granted_qos))

    # Callback when robot publishes a message
    def on_publish(self, client, userdata, mid):
        print("On publish: " + str(mid))

    # Callback when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        # print("Topic: " + msg.topic + "Payload: " + str(msg.payload))
        # ev3.Sound.speak('Message received').wait()
        handle_message(msg)


# Parse received message. Execute action defined in payload
def handle_message(msg):
    decoded_msg = msg.payload.decode("utf-8")
    payload = json.loads(decoded_msg)
    if 'voice' in payload:
        ev3.Sound.speak(payload['voice']).wait()
    if 'robotControl' in payload:
        arm_control(payload)
    if 'moveRobot' in payload:
        move_robot(payload)


# Move robot (direction and speed is defined in payload)
def move_robot(payload):
    if 'direction' and 'speed' and 'time' in payload['moveRobot']:
        speed = int(payload['moveRobot']['speed'])
        duration = int(payload['moveRobot']['time'])
        direction = payload['moveRobot']['direction']

        left = ev3.LargeMotor('outB')
        right = ev3.LargeMotor('outC')
        speed_l, speed_r = 0, 0

        if direction == 'fwd':
            speed_l = speed
            speed_r = speed
        elif direction == 'left':
            speed_l = -speed
            speed_r = speed
        elif direction == 'right':
            speed_l = speed
            speed_r = -speed
        elif direction == 'back':
            speed_l = -speed
            speed_r = -speed
        else:
            ev3.Sound.speak('Please tell me direction').wait()

        if left.connected and right.connected:
            left.run_timed(time_sp=duration, speed_sp=speed_l)
            right.run_timed(time_sp=duration, speed_sp=speed_r)

            # When motor is stopped, its `state` attribute returns empty list.
            # Wait until both motors are stopped:
            while any(left.state) or any(right.state):
                time.sleep(0.1)


# Move robot arm (Speed and duration is defined in payload)
def arm_control(payload):
    m = ev3.MediumMotor('outA')
    speed = int(payload['robotControl']['speed'])
    duration = int(payload['robotControl']['time'])
    if m.connected:
        m.run_timed(time_sp=duration, speed_sp=speed)
        while any(m.state):
            time.sleep(0.1)
        print("done")
    else:
        print("Motor not connected")


# On button press, send payload to Bluemix (MQTT)
def publish_data(run_event):
    while run_event.is_set():
        ts = ev3.TouchSensor()
        if ts.connected and ts.value() == 1:
            try:
                ev3.Leds.set_color(ev3.Leds.LEFT, (ev3.Leds.GREEN, ev3.Leds.RED)[ts.value()])
                payload = ("{\"touchSensorValue\": \"%d\"}" % ts.value())
                client.publish(mindBlue.publisher_topic, payload)
                print("Data sent")
            except:
                print("Err")
        else:
            ev3.Leds.set_color(ev3.Leds.LEFT, (ev3.Leds.GREEN, ev3.Leds.RED)[ts.value()])


mindBlue = MindstormBluemix()

# Script need to wait for system startup
if mindBlue.mode != "develop":
    time.sleep(20)


# Make new MQTT client
client = mqtt.Client(mindBlue.make_mqtt_client_info())
# Define callbacks
client.on_connect = mindBlue.on_connect
client.on_message = mindBlue.on_message
client.on_subscribe = mindBlue.on_subscribe
client.on_publish = mindBlue.on_publish
# Set username and password
client.username_pw_set(mindBlue.auth_type, mindBlue.token)
# Connect to Bluemix iot platform
client.connect(mindBlue.make_connect_info(), mindBlue.port, 60)
# Subscribe to topic
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
