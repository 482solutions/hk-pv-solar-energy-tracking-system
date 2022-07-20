# solar-panel-connector
There are a set of solar panels housed SIT (Singapore Institute of Technology @ Nanyang Polytechnic). All raw data are overseed by their managment hub (Laurel). The research engineer there have created a MQTT Broker and topic for us to subscribe.  

# How does it work?
The set of solar panels in SIT have been equipped with multiple sensors to detect current, power, etc for monitoring purposes. These sensors will feed the data to Laurel in a .json format. The data are further broke down and are housed in a database at SIT. Selected data will be fed to MQTT broker by publishing topics. A MQTT client is set up to subscribe to these topics to obtain raw data every minute.

# Current development
A simple MQTT client script has been written to subscribe to MQTT broker. The topic is "Power_Monitoring". For testing purposes, a default username and password have been hardcoded into the script. In the future, we'll have to take that out.

# What we are receiving now
1) Power
2) Current
3) Voltage
