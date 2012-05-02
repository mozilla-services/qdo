APPNAME = qdo
DEPS =
HERE = $(shell pwd)
BIN = $(HERE)/bin
VIRTUALENV = virtualenv-2.6
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
	--use-mirrors -f https://github.com/mozilla-services/qdo/downloads \
	-f https://github.com/hannosch/clint/downloads
CASSANDRA_VERSION = 1.0.9
NGINX_VERSION = 1.1.19
ZOOKEEPER_VERSION = 3.4.3

ifdef PYPIEXTRAS
	PYPIOPTIONS += -e $(PYPIEXTRAS)
	INSTALLOPTIONS += -f $(PYPIEXTRAS)
endif

ifdef PYPISTRICT
	PYPIOPTIONS += -s
	ifdef PYPIEXTRAS
		HOST = `python2.6 -c "import urlparse; print urlparse.urlparse('$(PYPI)')[1] + ',' + urlparse.urlparse('$(PYPIEXTRAS)')[1]"`

	else
		HOST = `python2.6 -c "import urlparse; print urlparse.urlparse('$(PYPI)')[1]"`
	endif

endif

INSTALL += $(INSTALLOPTIONS)

SW = sw
CASSANDRA = $(BIN)/cassandra/bin/cassandra
NGINX = $(BIN)/nginx
BUILD_DIRS = bin build deps include lib lib64 man


.PHONY: all build test build_rpms mach
.SILENT: lib python pip $(CASSANDRA) cassandra $(NGINX) nginx

all: build-dev

$(BIN)/python:
	python2.6 $(SW)/virtualenv.py --distribute . >/dev/null 2>&1
	rm distribute-0.6.*.tar.gz

$(BIN)/pip: $(BIN)/python

lib: $(BIN)/pip
	@echo "Installing package pre-requisites..."
	$(INSTALL) -r dev-reqs.txt
	@echo "Installing production pre-requisites..."
	$(INSTALL) -r prod-reqs.txt

$(CASSANDRA):
	@echo "Installing Cassandra"
	mkdir -p bin
	cd bin && \
	curl --silent http://archive.apache.org/dist/cassandra/$(CASSANDRA_VERSION)/apache-cassandra-$(CASSANDRA_VERSION)-bin.tar.gz | tar -zx
	mv bin/apache-cassandra-$(CASSANDRA_VERSION) bin/cassandra
	cp etc/cassandra/cassandra.yaml bin/cassandra/conf/cassandra.yaml
	cp etc/cassandra/log4j-server.properties bin/cassandra/conf/log4j-server.properties
	cd bin/cassandra/lib && \
	curl --silent -O http://java.net/projects/jna/sources/svn/content/trunk/jnalib/dist/jna.jar >/dev/null 2>&1
	@echo "Finished installing Cassandra"

cassandra: $(CASSANDRA)

$(NGINX):
	@echo "Installing Nginx"
	mkdir -p bin
	cd bin && \
	curl --silent http://nginx.org/download/nginx-$(NGINX_VERSION).tar.gz | tar -zx
	mv bin/nginx-$(NGINX_VERSION) bin/nginx
	cd bin/nginx && \
	./configure --prefix=$(HERE)/bin/nginx --with-http_ssl_module \
	--conf-path=../../etc/nginx/nginx.conf --pid-path=../../var/nginx.pid \
	--lock-path=../../var/nginx.lock --error-log-path=../../var/log/nginx-error.log \
	--http-log-path=../../var/log/nginx-access.log >/dev/null 2>&1 && \
	make >/dev/null 2>&1 && make install >/dev/null 2>&1
	@echo "Finished installing Nginx"

nginx: $(NGINX)

clean-env:
	rm -rf $(BUILD_DIRS)

clean-cassandra:
	rm -rf cassandra bin/cassandra

clean-nginx:
	rm -rf bin/nginx

clean: clean-env

build: lib cassandra nginx
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
	--cover-inclusive $(APPNAME) \
	--set-env-variables="{'REQUESTS_CA_BUNDLE': '$(HERE)/etc/ssl/localhost.crt'}" \
	$(ARG)
