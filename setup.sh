#!/bin/bash 
(./robonomics --dev >& logs/robonomics_logs.txt) & read -p 'Creating local robonomics node. Ensure that you have created service account for both local and westmint nodes.
Once, you have done that. Press enter to continue'
python3 service.py >& logs/service_logs.txt & python3 plug_device.py --yaml-station-data test/station_1.yaml --station-config config/config_station_1.yaml >& logs/plug_logs.txt &
