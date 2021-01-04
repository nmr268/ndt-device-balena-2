###
# Build stage
##
FROM balenalib/raspberrypi3-node:10-build as build

# Move to app dir
WORKDIR /usr/src/app

# Install build dependencies
RUN install_packages \
  apt-utils \
  clang \
  libxcb-image0 \
  libxcb-util0 \
  xdg-utils \
  libdbus-1-dev \
  libgtk2.0-dev \
  libnotify-dev \
  libgnome-keyring-dev \
  libgconf2-dev \
  libasound2-dev \
  libcap-dev \
  libcups2-dev \
  libxtst-dev \
  libxss1 \
  libnss3-dev \
  libsmbclient \
  libssh-4 \
  libexpat-dev

# Move package.json to filesystem
COPY ./app/package.json .

# Install npm modules for the application
RUN    JOBS=MAX npm install --unsafe-perm --production \
    && node_modules/.bin/electron-rebuild

###
# Build stage for setlight program
##
FROM balenalib/raspberrypi3-node:10-build as build_lightcontrol

RUN install_packages scons

COPY ./app/lightcontrol ./

# Make and install setlight
RUN make \
  && make install

###
# Runtime
##
FROM balenalib/raspberrypi3-node:10-run

# Move to app dir
WORKDIR /usr/src/app

# Copy the modules from the build step
COPY --from=build /usr/src/app/node_modules ./node_modules

# Copy setlight program from build step
COPY --from=build_lightcontrol /usr/local/bin/setlight /usr/local/bin

# Install runtime dependencies
RUN install_packages \
x11-apps \
dbus-x11 \
python3-pip \
libatlas-base-dev \
python3-numpy \
python3-pandas \
python3-scipy \
python3-requests \
python3-picamera \
python3-rpi.gpio \
python3-opencv \
python3-skimage \
python3-serial \
python3-tqdm \
python3-flask-cors \
xserver-xorg-core \
xserver-xorg-input-all \
xserver-xorg-video-fbdev \
xorg \
libxcb-image0 \
libxcb-util0 \
xdg-utils \
libdbus-1-3 \
libgtk2.0 \
libnotify4 \
libgnome-keyring0 \
libgconf-2-4 \
libasound2 \
libcap2 \
libcups2 \
libxtst6 \
libxss1 \
libnss3 \
libsmbclient \
libssh-4 \
fbset \
libexpat1 \
ssh

RUN pip3 install numpy==1.17.2 scikit-learn==0.21.3 Flask==0.10.1 Flask-cors dbus-python==1.2.8 pycairo==1.17.0 python-networkmanager==2.1 six==1.11.0

RUN echo "#!/bin/bash" > /etc/X11/xinit/xserverrc \
  && echo "" >> /etc/X11/xinit/xserverrc \
  && echo 'exec /usr/bin/X -s 0 dpms -nocursor -nolisten tcp "$@"' >> /etc/X11/xinit/xserverrc

# Move app to filesystem
COPY ./app ./

# Skip barcode scanning for now.
# TODO: Remove this when barcode scanning should be enabled.
#RUN echo 'fake_barcode = "000000000000"' > data/simulate.py

ENV DATA_GATHERING 0
ENV NITRATE_MODEL "1"
ENV PHOSPHATE_MODEL "1"
ENV URL_LAUNCHER_HEIGHT 480
ENV URL_LAUNCHER_WIDTH 800
ENV UDEV 1
ENV URL_LAUNCHER_URL http://localhost:5000
ENV DBUS_SYSTEM_BUS_ADDRESS unix:path=/host/run/dbus/system_bus_socket

# Start app
CMD ["bash", "/usr/src/app/start.sh"]
