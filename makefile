ifeq (, $(shell which python))
	PYTHON=python3
else
	PYTHON=python
endif

PYTHON_VERSION_MIN=3.8
PYTHON_VERSION_CUR=$(shell $(PYTHON) -c 'import sys; print("%d.%d"% sys.version_info[0:2])')
PYTHON_VERSION_OK=$(shell $(PYTHON) -c 'import sys; cur_ver = sys.version_info[0:2]; min_ver = tuple(map(int, "$(PYTHON_VERSION_MIN)".split("."))); print(int(cur_ver >= min_ver))')
ifeq ($(PYTHON_VERSION_OK), 0)
    $(error "Need python version >= $(PYTHON_VERSION_MIN). Current version is $(PYTHON_VERSION_CUR)")
endif

SOURCES = $(shell find -type f -name '*.py')
ROBO_LOGS ?= logs/robonomics_logs.txt
SERVICE_LOGS ?= logs/service_logs.txt
PLUG_LOGS ?= logs/plug_logs.txt

default: stop clean download check setup

check:
	$(PYTHON) -m py_compile $(SOURCES)
	
download:
	$(PYTHON) -m pip install -r requirements.txt
	$(shell wget https://github.com/airalab/robonomics/releases/download/v2.1.0/robonomics-2.1.0-x86_64-unknown-linux-gnu.tar.gz)
	$(shell tar xf robonomics-2.1.0-x86_64-unknown-linux-gnu.tar.gz)
	$(shell chmod +x robonomics)
	$(shell rm robonomics-2.1.0-x86_64-unknown-linux-gnu.tar.gz)
	$(shell echo "#!/bin/bash \n(./robonomics --dev >& $(ROBO_LOGS)) & read -p 'Creating local robonomics node. Ensure that you have created service \
	account for both local and westmint nodes.\\nOnce, you have done that. Press enter to continue'\\n$(PYTHON) service.py >& $(SERVICE_LOGS) & \
	$(PYTHON) plug_device.py --yaml-station-data test/station_1.yaml --station-config config/config_station_1.yaml >& $(PLUG_LOGS) &" > setup.sh)	
	$(shell chmod +x setup.sh)

setup:
	$(shell ./setup.sh)

clean:
	$(shell cat /dev/null > $(ROBO_LOGS))
	$(shell cat /dev/null > $(SERVICE_LOGS))
	$(shell cat /dev/null > $(PLUG_LOGS))
	
stop:
	$(shell pkill -15 -f './robonomics --dev')
	$(shell pkill -15 -f 'python3 service.py')
	$(shell pkill -15 -f 'python3 plug_device.py --yaml-station-data test/station_1.yaml --station-config config/config_station_1.yaml')
