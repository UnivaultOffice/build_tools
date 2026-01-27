FROM univaultoffice/documentserver:latest
RUN apt-get update -y && \ 
	apt-get install git -y \
			python3 -y \
			openjdk-11-jdk -y \
			bzip2 -y \
			npm -y && \
	npm install -g grunt grunt-cli -y && \
	ln -s /usr/bin/python3 /usr/bin/python && \
	ln -s /usr/bin/pip3 /usr/bin/pip && \
	git clone --depth 1 https://github.com/UNIVAULTOFFICE/build_tools.git var/www/univaultoffice/documentserver/build_tools && \
	sed -i '/documentserver-static-gzip.sh ${UNIVAULTOFFICE_DATA_CONTAINER}/d' /app/ds/run-document-server.sh && \
	#Set Up Debug Logging
	sed -i 's/WARN/ALL/g' /etc/univaultoffice/documentserver/log4js/production.json && \
	#Start test example
	if [ -s /etc/supervisor/conf.d/ds-example.conf ] ; then sed -i 's,autostart=false,autostart=true,' /etc/supervisor/conf.d/ds-example.conf; fi && \
	if [ -s /app/ds/setup/config/supervisor/ds/ds-example.conf ] ; then sed -i 's,autostart=false,autostart=true,' /app/ds/setup/config/supervisor/ds/ds-example.conf; fi && \
	rm -rf /var/lib/apt/lists/*
ENTRYPOINT python3 /var/www/univaultoffice/documentserver/build_tools/develop/run_build_js.py /var/www/univaultoffice/documentserver $@ && /bin/sh -c /app/ds/run-document-server.sh 
