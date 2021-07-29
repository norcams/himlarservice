NAME=himlarservice
VERSION=1.1
PACKAGE_VERSION=1
DESCRIPTION="Set of services used for himlar cloud"
URL="https://github.com/norcams/himlarservice"
MAINTAINER="https://github.com/norcams"
RELVERSION=7
INSTALL_DIR=/opt/himlarservice

.PHONY: default
default: deps build rpm
package: rpm

.PHONY: clean
clean:
	rm -fr /installdir
	rm -f $(NAME)-$(VERSION)-*.rpm
	rm -Rf /vendor

.PHONY: deps
deps:
	yum install -y gcc rpm-build openldap-devel centos-release-scl openssl-devel
	yum install -y rh-ruby23 rh-ruby23-ruby-devel
	source /opt/rh/rh-ruby23/enable; gem install -N fpm
	yum install -y python-devel python-virtualenv git libyaml-devel PyYAML libffi-devel

.PHONY: build
build:
	mkdir /vendor
	mkdir -p /installdir${INSTALL_DIR}

	cd /vendor; git clone ${URL}
	rsync -avh --exclude '.git' /vendor/himlarservice/ /installdir${INSTALL_DIR}
	cd /installdir${INSTALL_DIR}; virtualenv --clear .
	# cd /installdir${INSTALL_DIR}; bin/python setup.py install
	cd /installdir${INSTALL_DIR}; bin/pip install --upgrade pip
	cd /installdir${INSTALL_DIR}; bin/pip install -r requirements.txt
	cd /installdir${INSTALL_DIR}; virtualenv --relocatable .
	#echo "${INSTALL_DIR}" > /installdir${INSTALL_DIR}/lib/python2.7/site-packages/himlarservice.egg-link
	echo "${INSTALL_DIR}/src/himlarcli"  > /installdir${INSTALL_DIR}/lib/python2.7/site-packages/himlarcli.egg-link
	echo "${INSTALL_DIR}/src/himlarcli" > /installdir${INSTALL_DIR}/lib/python2.7/site-packages/easy-install.pth

.PHONY: rpm
rpm:
	source /opt/rh/rh-ruby23/enable; fpm -s dir -t rpm \
		-n $(NAME) \
		-v $(VERSION) \
		--iteration "$(PACKAGE_VERSION).el$(RELVERSION)" \
		--description ${DESCRIPTION} \
		--url ${URL} \
		--maintainer ${MAINTAINER} \
		-C /installdir/ \
		.
