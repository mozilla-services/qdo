APPNAME = qdo
DEPS =
HERE = $(shell pwd)
BIN = $(HERE)/bin
VIRTUALENV = virtualenv
NOSE = bin/nosetests -s --with-xunit
TESTS = $(APPNAME)/tests
PYTHON = $(HERE)/bin/python
BUILDAPP = $(HERE)/bin/buildapp
BUILDRPMS = $(HERE)/bin/buildrpms
PYPI = http://pypi.python.org/simple
PYPIOPTIONS = -i $(PYPI)
DOTCHANNEL := $(wildcard .channel)
ifeq ($(strip $(DOTCHANNEL)),)
	CHANNEL = dev
	RPM_CHANNEL = prod
else
	CHANNEL = `cat .channel`
	RPM_CHANNEL = `cat .channel`
endif
INSTALL = $(HERE)/bin/pip install
PIP_DOWNLOAD_CACHE ?= /tmp/pip_cache
INSTALLOPTIONS = --download-cache $(PIP_DOWNLOAD_CACHE) -U -i $(PYPI) \
	--use-mirrors

ifdef PYPIEXTRAS
	PYPIOPTIONS += -e $(PYPIEXTRAS)
	INSTALLOPTIONS += -f $(PYPIEXTRAS)
endif

ifdef PYPISTRICT
	PYPIOPTIONS += -s
	ifdef PYPIEXTRAS
		HOST = `python -c "import urlparse; print urlparse.urlparse('$(PYPI)')[1] + ',' + urlparse.urlparse('$(PYPIEXTRAS)')[1]"`

	else
		HOST = `python -c "import urlparse; print urlparse.urlparse('$(PYPI)')[1]"`
	endif

endif

INSTALL += $(INSTALLOPTIONS)

SW = sw
BUILD_DIRS = bin build deps include lib lib64 man


.PHONY: all build test build_rpms mach
.SILENT: lib python pip

all: build

$(BIN)/python:
	python $(SW)/virtualenv.py --distribute . >/dev/null 2>&1
	rm distribute-0.6.*.tar.gz

$(BIN)/pip: $(BIN)/python

lib: $(BIN)/pip
	@echo "Installing package pre-requisites..."
	$(INSTALL) -r dev-reqs.txt
	echo "Running setup.py develop"
	$(PYTHON) setup.py develop

clean-env:
	rm -rf $(BUILD_DIRS)

clean: clean-env

build: lib
	$(BUILDAPP) -c $(CHANNEL) $(PYPIOPTIONS) $(DEPS)

html:
	cd docs && make html

test:
	@echo "Running tests..."
	rm -f $(HERE)/.coverage*
	$(PYTHON) runtests.py
	$(HERE)/bin/coverage combine
	$(HERE)/bin/coverage report -m --omit="qdo/test*" --include="qdo/*"
	@echo "Finished running tests"

test-python:
	$(NOSE) --with-coverage --cover-package=$(APPNAME) \
	--cover-inclusive $(APPNAME) $(ARG)
