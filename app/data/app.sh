#!/bin/sh
cd /usr/src/app/data
export DBUS_SYSTEM_BUS_ADDRESS=unix:path=/host/run/dbus/system_bus_socket
#export PYTHONPATH="/usr/src/app/pythonmodules"

terminate() {
    RUNNING=false
    kill -TERM ${PID}
}
trap terminate SIGTERM

RUNNING=true
while $RUNNING ; do
    python3 /usr/src/app/data/app.py &
    PID=$!
    wait ${PID}
done

echo "Controlled exit from app.sh"
