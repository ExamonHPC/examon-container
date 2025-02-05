FROM amd64/python:2.7.13-stretch
MAINTAINER Francesco Beneventi (francesco.beneventi@unibo.it)


RUN echo "deb http://archive.debian.org/debian stretch main non-free" > /etc/apt/sources.list && \
	echo "Acquire::Check-Valid-Until no;" > /etc/apt/apt.conf.d/100disablechecks

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
	pypy \
	pypy-dev \
	sshpass \
	supervisor \
	nano \
    apt-transport-https \
    ca-certificates \
	&& rm -rf /var/lib/apt/lists/*

COPY ./examon_deploy /etc/examon_deploy

COPY ./supervisor.conf /etc/supervisor/conf.d
	
RUN echo "nameserver 8.8.8.8" >> /etc/resolv.conf
 
ENV EXAMON_HOME /etc/examon_deploy/examon

WORKDIR $EXAMON_HOME/scripts

RUN virtualenv -p pypy --no-pip ve  && \
	./ve/bin/easy_install pip==20.1.1 && \
	./ve/bin/pip install paho-mqtt==1.4.0
		
RUN chmod +x ./frontend_ctl.sh

EXPOSE 1883 9001

CMD ["./frontend_ctl.sh", "start"]
	
 
