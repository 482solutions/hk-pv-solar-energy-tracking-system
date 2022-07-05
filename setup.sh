#!/bin/bash 
(./robonomics --dev) &
read -p "Local robonomics node created. Ensure that you've created service account for both local and westmint nodes.\
	\nOnce, you've done that. Press any key to continue"
python3 service.py
