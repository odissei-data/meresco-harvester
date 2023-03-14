#!/bin/bash
echo "$(date) - Running harvester.sh"
env > /tmp/env.txt
/app/bin/meresco-harvester --url=http://localhost:8888 --set-process-timeout=3600 --concurrency=2 --domain=ODISSEI --runOnce
