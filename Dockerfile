FROM python:3.12

RUN echo "deb https://deb.debian.org/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
	libblas-dev \
	liblapack-dev \
	liblapacke-dev \
	gfortran \
	ipmitool \
	mosquitto \
	mosquitto-clients \
	snmp \
	snmp-mibs-downloader \
	pypy3 \
	pypy3-dev \
	sshpass \
	supervisor \
	nano \
    apt-transport-https \
    ca-certificates \
	python3-virtualenv \
	&& rm -rf /var/lib/apt/lists/*

COPY ./examon_deploy /etc/examon_deploy

COPY ./supervisord.conf /etc/supervisor
COPY ./supervisor.conf /etc/supervisor/conf.d
	
RUN echo "nameserver 8.8.8.8" >> /etc/resolv.conf

ENV EXAMON_HOME /etc/examon_deploy/examon

WORKDIR $EXAMON_HOME/scripts
RUN virtualenv -p pypy3 ve
ENV PIP $EXAMON_HOME/scripts/ve/bin/pip

WORKDIR $EXAMON_HOME/lib/examon-common
RUN $PIP install .

WORKDIR $EXAMON_HOME/subscribers/mqtt2kairosdb_queue
RUN $PIP install -r requirements.txt

WORKDIR $EXAMON_HOME/scripts
RUN chmod +x ./frontend_ctl.sh

EXPOSE 1883 9001

CMD ["./frontend_ctl.sh", "start"]
	
 
