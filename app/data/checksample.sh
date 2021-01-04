#!/bin/sh
cd /usr/src/app/data

terminate() {
    python3 -c 'from checksample_com import Control;Control.stop()'
}
trap terminate SIGTERM

python3 -c 'from checksample_com import Status ; Status.setup() ; Status.set_status(Status.UNAVAILABLE)'


python3 checksample.py daemon &
PID=$!
wait ${PID}
