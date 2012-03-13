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

all:	build

$(BIN)/python:
	python2.6 $(SW)/virtualenv.py --no-site-packages --distribute .
	rm distribute-0.6.24.tar.gz

$(BIN)/pip: $(BIN)/python

lib: $(BIN)/pip
	$(INSTALL) -r dev-reqs.txt

$(CASSANDRA):
	mkdir -p bin
	cd bin && \
	curl --silent http://archive.apache.org/dist/cassandra/1.0.6/apache-cassandra-1.0.6-bin.tar.gz | tar -zvx
	mv bin/apache-cassandra-1.0.6 bin/cassandra
	cp etc/cassandra/cassandra.yaml bin/cassandra/conf/cassandra.yaml
	cp etc/cassandra/log4j-server.properties bin/cassandra/conf/log4j-server.properties
	cd bin/cassandra/lib && \
	curl -O http://java.net/projects/jna/sources/svn/content/trunk/jnalib/dist/jna.jar

cassandra: $(CASSANDRA)

$(NGINX):
	mkdir -p bin
	cd bin && \
	curl --silent http://nginx.org/download/nginx-1.1.15.tar.gz | tar -zvx
	mv bin/nginx-1.1.15 bin/nginx
	cd bin/nginx && \
	./configure --prefix=$(HERE)/bin/nginx --with-http_ssl_module \
	--conf-path=../../etc/nginx/nginx.conf --pid-path=../../var/nginx.pid \
	--lock-path=../../var/nginx.lock --error-log-path=../../var/log/nginx-error.log \
	--http-log-path=../../var/log/nginx-access.log && \
	make && make install

nginx: $(NGINX)

$(ZOOKEEPER):
	mkdir -p bin
	cd bin && \
	curl --silent http://mirrors.ibiblio.org/apache//zookeeper/stable/zookeeper-3.3.4.tar.gz | tar -zvx
	mv bin/zookeeper-3.3.4 bin/zookeeper
	cd bin/zookeeper && ant compile
	cd bin/zookeeper/src/c && \
	./configure && \
	make
	cd bin/zookeeper/src/contrib/zkpython && \
	mv build.xml old_build.xml && \
	cat old_build.xml | sed 's|executable="python"|executable="../../../../../bin/python"|g' > build.xml && \
	ant install
	cp etc/zoo.cfg bin/zookeeper/conf/
	cd bin/zookeeper/bin && \
	mv zkServer.sh old_zkServer.sh && \
	cat old_zkServer.sh | sed 's|    $$JAVA "-Dzoo|    exec $$JAVA "-Dzoo|g' > zkServer.sh && \
	chmod a+x zkServer.sh
	mkdir -p zookeeper/server1/data && echo "1" > zookeeper/server1/data/myid
	mkdir -p zookeeper/server2/data && echo "2" > zookeeper/server2/data/myid
	mkdir -p zookeeper/server3/data && echo "3" > zookeeper/server3/data/myid

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
	$(PYTHON) setup.py develop
	$(BUILDAPP) -c $(CHANNEL) $(PYPIOPTIONS) $(DEPS)

html:
	cd docs && make html

test:
	$(PYTHON) runtests.py

test-python:
	$(NOSE) --with-coverage --cover-package=$(APPNAME) --cover-erase \
	--cover-inclusive $(APPNAME) \
	--set-env-variables="{'REQUESTS_CA_BUNDLE': '$(HERE)/etc/ssl/localhost.crt'}"
