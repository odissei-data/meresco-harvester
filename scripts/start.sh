#!/bin/bash

# Start the harvester server
./bin/meresco-harvester-server -p "$PORT_NUMBER" --dataPath "$DATA_PATH" --logPath "$LOG_PATH" --statePath "$STATE_PATH" --externalUrl "$EXTERNAL_URL" &

# Start cron
cron -f