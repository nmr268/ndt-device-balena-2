#!/bin/bash

# set pythonmodules path
export PYTHONPATH=/usr/src/app/pythonmodules

# By default docker gives us 64MB of shared memory size but to display heavy
# pages we need more.
umount /dev/shm && mount -t tmpfs shm /dev/shm

# using local electron module instead of the global electron lets you
# easily control specific version dependency between your app and electron itself.
# the syntax below starts an X istance with ONLY our electronJS fired up,
# it saves you a LOT of resources avoiding full-desktops envs

rm /tmp/.X0-lock &>/dev/null || true

# Start the analyse process
if [ $DATA_GATHERING = "0" ]; then
    bash /usr/src/app/data/checksample.sh &
    ANALYSE_PID=$!
fi

# Install LED driver
#bash /usr/src/app/data/makeled.sh &

# Start the flask backend
bash /usr/src/app/data/app.sh &
FLASK_PID=$!

# Start the GUI frontend
if [ ! -c /dev/fb1 ] && [ "$TFT" = "1" ]; then
  modprobe spi-bcm2708 || true
  modprobe fbtft_device name=pitft verbose=0 rotate=${TFT_ROTATE:-0} || true
  sleep 1
  mknod /dev/fb1 c $(cat /sys/class/graphics/fb1/dev | tr ':' ' ') || true
  FRAMEBUFFER=/dev/fb1 startx /usr/src/app/node_modules/electron/dist/electron /usr/src/app --enable-logging &
else
  startx /usr/src/app/node_modules/electron/dist/electron /usr/src/app --enable-logging &
fi
FRONTEND_PID=$!

# Handler for SIGTERM to close nicely
terminate() {
    kill -TERM ${FRONTEND_PID}
    kill -TERM ${FLASK_PID}
    if [ $DATA_GATHERING = "0" ]; then
        kill -TERM ${ANALYSE_PID}
    fi
}
trap terminate SIGTERM

wait ${FRONTEND_PID}
wait ${FLASK_PID}
if [ $DATA_GATHERING = "0" ]; then
    wait ${ANALYSE_PID}
fi

echo "Controlled exit"
