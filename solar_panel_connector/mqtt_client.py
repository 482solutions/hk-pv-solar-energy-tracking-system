from logging import NullHandler
import paho.mqtt.client as mqtt
from threading import Thread
import concurrent.futures
import time
import json

to_json = {}
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

# The callback for when a PUBLISH message is received from the server.
def enqueue(to_json):
    time.sleep(200)
    print("t2 enqueueing")

def on_message(mqttc, userdata, msg):
    global to_json
    message = str(msg.payload.decode('utf-8'))
    message_split = message.split("\n") 
    for topic_message in message_split:
        if not topic_message:
            continue
        topic, message = topic_message.split(":", 1)
        to_json[topic]=message 
    # print(to_json)
    mqttc.disconnect()
    # print(to_json)
    # print(f"msg topic = {msg.topic}")
    
    # print(f"msg payload = {}")
    # print(msg.topic+" "+str(msg.payload.decode("utf-8")))

def on_publish(mqttc, obj, mid):
    print("mid: " + str(mid))

def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(mqttc, obj, level, string):
    print("logs",string)

def run():
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
    return to_json
    
class custom_thread(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    def run(self):
        print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

if __name__ == "__main__":
    #For testing purposes
    a = custom_thread(target=run)
    b = custom_thread(target=run)
    print('starting a')
    a.start()
    print('starting b')
    b.start()
    print(a.is_alive())
    print(a.join())
    print(b.join())
        
    
    
    
    



