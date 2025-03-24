#!/bin/bash

docker cp ./examon_deploy examon_0:/etc
docker cp ./supervisor.conf examon_0:/etc/supervisor/conf.d
