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

check:
	$(PYTHON) -m py_compile $(SOURCES)
	

download:
	$(shell wget https://github.com/airalab/robonomics/releases/download/v2.1.0/robonomics-2.1.0-x86_64-unknown-linux-gnu.tar.gz)
	$(shell tar xf robonomics-2.1.0-x86_64-unknown-linux-gnu.tar.gz)
	$(shell chmod +x robonomics)
	$(shell echo "#!/bin/bash \n./robonomics --dev & $(PYTHON) service.py" > setup.sh)	
	$(shell chmod +x setup.sh)
	$(shell $(PYTHON) -m pip install -r requirements.txt)

setup:
	$(shell ./setup.sh)
	
	
