import paho.mqtt.client as mqtt
import time
import json

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    to_json = {}
    to_json = {}
    message = str(msg.payload.decode('utf-8'))
    message_split = message.split("\n") 
    for topic_message in message_split:
        if not topic_message:
            continue
        topic, message = topic_message.split(":", 1)
        to_json[topic]=message 
        
    print(to_json)
    print(f"msg topic = {msg.topic}")
    # print(f"msg payload = {}")
    # print(msg.topic+" "+str(msg.payload.decode("utf-8")))

def on_publish(mqttc, obj, mid):
    print("mid: " + str(mid))

def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(mqttc, obj, level, string):
    print("logs",string)

mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
# Uncomment to enable debug messages
# mqttc.on_log = on_log
mqttc.username_pw_set("etbuyegy", "1kAeZUnvChLy")
mqttc.connect("driver.cloudmqtt.com", 18833)
mqttc.subscribe("Power_Monitoring", 0)

mqttc.loop_forever()

