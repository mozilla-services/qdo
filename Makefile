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
INSTALLOPTIONS = --download-cache $(PIP_DOWNLOAD_CACHE) -U -i $(PYPI) --use-mirrors
CASSANDRA_VERSION = 1.0.8

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
ZOOKEEPER = $(BIN)/zookeeper
BUILD_DIRS = bin build deps include lib lib64 man


.PHONY: all build test build_rpms mach
.SILENT: lib python pip $(CASSANDRA) cassandra $(NGINX) nginx $(ZOOKEEPER) zookeeper

all:	build

$(BIN)/python:
	python2.6 $(SW)/virtualenv.py --no-site-packages --distribute . >/dev/null 2>&1
	rm distribute-0.6.*.tar.gz

$(BIN)/pip: $(BIN)/python

lib: $(BIN)/pip
	@echo "Installing package pre-requisites..."
	$(INSTALL) -r dev-reqs.txt >/dev/null 2>&1
	@echo "Running setup.py develop"
	$(PYTHON) setup.py develop >/dev/null 2>&1

$(CASSANDRA):
	@echo "Installing Cassandra"
	mkdir -p bin
	cd bin && \
	curl --silent http://archive.apache.org/dist/cassandra/$(CASSANDRA_VERSION)/apache-cassandra-$(CASSANDRA_VERSION)-bin.tar.gz | tar -zvx >/dev/null 2>&1
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
	curl --silent http://nginx.org/download/nginx-1.1.15.tar.gz | tar -zvx >/dev/null 2>&1
	mv bin/nginx-1.1.15 bin/nginx
	cd bin/nginx && \
	./configure --prefix=$(HERE)/bin/nginx --with-http_ssl_module \
	--conf-path=../../etc/nginx/nginx.conf --pid-path=../../var/nginx.pid \
	--lock-path=../../var/nginx.lock --error-log-path=../../var/log/nginx-error.log \
	--http-log-path=../../var/log/nginx-access.log >/dev/null 2>&1 && \
	make >/dev/null 2>&1 && make install >/dev/null 2>&1
	@echo "Finished installing Nginx"

nginx: $(NGINX)

$(ZOOKEEPER):
	@echo "Installing Zookeeper"
	mkdir -p bin
	cd bin && \
	curl --silent http://mirrors.ibiblio.org/apache//zookeeper/stable/zookeeper-3.3.4.tar.gz | tar -zvx >/dev/null 2>&1
	mv bin/zookeeper-3.3.4 bin/zookeeper
	cd bin/zookeeper && ant compile >/dev/null 2>&1
	cd bin/zookeeper/src/c && \
	./configure >/dev/null 2>&1 && \
	make >/dev/null 2>&1
	cd bin/zookeeper/src/contrib/zkpython && \
	mv build.xml old_build.xml && \
	cat old_build.xml | sed 's|executable="python"|executable="../../../../../bin/python"|g' > build.xml && \
	ant install >/dev/null 2>&1
	cd bin/zookeeper/bin && \
	mv zkServer.sh old_zkServer.sh && \
	cat old_zkServer.sh | sed 's|    $$JAVA "-Dzoo|    exec $$JAVA "-Dzoo|g' > zkServer.sh && \
	chmod a+x zkServer.sh
	mkdir -p zookeeper/server1/data && echo "1" > zookeeper/server1/data/myid
	mkdir -p zookeeper/server2/data && echo "2" > zookeeper/server2/data/myid
	mkdir -p zookeeper/server3/data && echo "3" > zookeeper/server3/data/myid
	@echo "Finished installing Zookeeper"

zookeeper: $(ZOOKEEPER)

clean-env:
	rm -rf $(BUILD_DIRS)

clean-cassandra:
	rm -rf cassandra bin/cassandra

clean-nginx:
	rm -rf bin/nginx

clean-zookeeper:
	rm -rf zookeeper bin/zookeeper

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
	$(HERE)/bin/coverage report -m --omit="qdo/test*"
	@echo "Finished running tests"

test-python:
	$(NOSE) --with-coverage --cover-package=$(APPNAME) \
	--cover-inclusive $(APPNAME) \
	--set-env-variables="{'REQUESTS_CA_BUNDLE': '$(HERE)/etc/ssl/localhost.crt'}"
