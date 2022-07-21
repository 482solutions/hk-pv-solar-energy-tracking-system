#  solar-panel-connector

There are a set of solar panels housed SIT (Singapore Institute of Technology @ Nanyang Polytechnic). All raw data are overseed by their managment hub (Laurel). The research engineer there have created a MQTT Broker and topic for us to subscribe.  

# How does it work?

The set of solar panels in SIT have been equipped with multiple sensors to detect current, power, etc for monitoring purposes. These sensors will feed the data to Laurel in a .json format. The data are further broke down and are housed in a database at SIT. Selected data will be fed to MQTT broker by publishing topics. A MQTT client is set up to subscribe to these topics to obtain raw data every minute.


# Current development

A simple MQTT client script has been written to subscribe to MQTT broker. The topic is "Power_Monitoring". For testing purposes, a default username and password have been hardcoded into the script. In the future, we'll have to take that out.


# What we are receiving now

1) Power = Current X Voltage. Power is the rate of energy generated or used. This is needed to calculate energy(electricity usage) where Energy = Power X Time
2) Current = Current is the rate at which electric charge flows past a point in a circuit. Current is needed to calculate Power.
3) Voltage = Voltage, also called electromotive force, is the potential difference in charge between two points in an electrical field which is required to calculate Power.

## TL;DR
Current connection looks like this: SIT@NYP &rarr; Solar Panels &rarr; Management Hub(Laurel) &rarr; SIT Database &rarr; MQTT Broker &rarr; MQTT Client

Here's a simple diagram to understand the relationship between Power, Current and Voltage.
<img src="https://www.freeingenergy.com/wp-content/uploads/2019/11/Electricity-101-v2.png" width="600" height="300"/>
