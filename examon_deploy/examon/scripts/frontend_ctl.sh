#!/bin/bash

set -a
source examon.conf
set +a

# examon deploy path
if [ -z ${EXAMON_HOME+x} ]
then 
	EXAMON_HOME=/etc/examon_deploy/examon
fi
SCRIPTS_DIR=$EXAMON_HOME/scripts
HOSTS_LIST=""


/usr/bin/supervisord

