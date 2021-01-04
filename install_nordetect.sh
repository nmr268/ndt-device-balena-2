#!/bin/bash
APPUSER=pi
APPGROUP=pi
APPHOME="/usr/src/app"
LOGFILE="${APPHOME}"/postinstall-log.txt
MADEFOR="Raspbian GNU/Linux 10 (stretch)"
DIRECTORY="$( cd "$(dirname "$0")" ; pwd -P )"

# check if user is root
if [[ $EUID -ne 0 ]]; then
    printf "This script must be run as root"
    exit 1
fi

printf "install-nordetect.sh script ran on $(date)\n" >> $LOGFILE

# Clean up old versions
rm -rf "${APPHOME}"/app
rm -rf "${APPHOME}"/application
rm -rf "${APPHOME}"/pythonmodules
rm -rf "${APPHOME}"/appdata

printf "installing light control\n"
printf "####### Light Control INSTALL LOG #######\n\n" >> $LOGFILE
cd $DIRECTORY/lightcontrol
sudo -u $APPUSER make &> /dev/null &&
printf "make: Succes\n" >> $LOGFILE ||
printf "make: Failed\n" >> $LOGFILE
make install &> /dev/null &&
printf "make install: Succes\n" >> $LOGFILE ||
printf "make install: Failed\n" >> $LOGFILE

printf "###############################\n" >> $LOGFILE
printf "\n\n" >> $LOGFILE

# copy content
sudo -u $APPUSER cp -r $DIRECTORY/application "${APPHOME}"/ &&
printf "Copy flask-app: Succes\n" >> $LOGFILE ||
printf "Copy flask-app: Failed\n" >> $LOGFILE

sudo -u $APPUSER cp -r $DIRECTORY/pythonmodules "${APPHOME}"/ &&
printf "Copy python modules: Succes\n" >> $LOGFILE ||
printf "Copy python modules: Failed\n" >> $LOGFILE

if [[ -d "${APPHOME}"/Desktop/ ]] ; then
    install -o $APPUSER -g $APPGROUP -t "${APPHOME}"/Desktop/ $DIRECTORY/testapp.sh &&
    printf "Install a test script on the desktop: Succes\n" >> $LOGFILE ||
    printf "Install a test script on the desktop: Failed\n" >> $LOGFILE
fi

# Setup data storage
mkdir -p /mnt/data/$APPUSER &&
chown $APPUSER:$APPGROUP /mnt/data/$APPUSER &&
if [[ ! -e "${APPHOME}"/data ]] ; then
    sudo -u $APPUSER ln -sf /mnt/data/$APPUSER "${APPHOME}"/data
fi &&
printf "Setting up data dir: Succes\n" >> $LOGFILE ||
printf "Setting up data dir: Failed\n" >> $LOGFILE

# Make it easy to run other scripts then the main application
grep -q "# Setup python path for local modules" "${APPHOME}"/.profile
if [[ $? -ne 0 ]] ; then
    sudo -u $APPUSER echo >> "${APPHOME}"/.profile &&
    sudo -u $APPUSER echo '# Setup python path for local modules' >> "${APPHOME}"/.profile &&
    sudo -u $APPUSER echo 'export PYTHONPATH="$PYTHONPATH:'${APPHOME}'/pythonmodules"' >> "${APPHOME}"/.profile
fi

printf "Setting up boot config\n"
printf "####### BOOT SETUP LOG #######\n\n" >> $LOGFILE

sudo -u $APPUSER mkdir -p "${APPHOME}"/appdata

cd $DIRECTORY/splash_screen &&
sudo -u $APPUSER cp plymouth/nordetect/splash.png "${APPHOME}"/appdata/ &&
mkdir -p /usr/share/plymouth/themes/ &&
rm -rf /usr/share/plymouth/themes/nordetect &&
cp -r plymouth/nordetect /usr/share/plymouth/themes/ &&
mkdir -p /etc/plymouth/ &&
cp plymouth/plymouthd.conf /etc/plymouth/ &&
printf "Installing splash screen: Succes\n" >> $LOGFILE ||
printf "Installing splash screen: Failed\n" >> $LOGFILE

printf "Setting up hidden mouse cursors\n"
printf "####### HIDDEN MOUSE LOG #######\n\n" >> $LOGFILE

ERRORS=0
cd $DIRECTORY/blank_cursors &&
sudo -u $APPUSER ./gen.sh &&
sudo -u $APPUSER mv cursors "${APPHOME}"/appdata/blankcursors ||
((ERRORS++))
if [[ $ERRORS -eq 0 ]] ; then
    if [ -z "${DEVSYSTEM+x}" ] ; then
        # Only make cursors blank/transparent if not a dev system
        rm -rf "${APPHOME}"/.icons/default/cursors &&
        sudo -u $APPUSER mkdir -p "${APPHOME}"/.icons/default &&
        sudo -u $APPUSER ln -s "${APPHOME}"/appdata/blankcursors "${APPHOME}"/.icons/default/cursors &&
        sudo -u $APPUSER cp blankrootcursor "${APPHOME}"/appdata/ ||
        ((ERRORS++))
    else
        # If we have a blank cursor theme, remove it
        if [[ -f "${APPHOME}"/.icons/default/cursors/blank ]] ; then
            rm -rf "${APPHOME}"/.icons/default/cursors
            ((ERRORS++))
        fi
    fi
fi
if [ -n "${DEVSYSTEM+x}" ] ; then
    printf "Development system: Hidden X mouse cursors not activated\n" >> $LOGFILE
fi
if [[ $ERRORS -eq 0 ]] ; then
    printf "Installing hidden X mouse cursors: Succes\n" >> $LOGFILE
else
    printf "Installing hidden X mouse cursors: Failed\n" >> $LOGFILE
fi    

printf "Setting up systemd\n"
printf "####### SYSTEMD LOG #######\n\n" >> $LOGFILE

cd $DIRECTORY/xlogin &&
make install &&
printf "Installing X login daemon: Succes\n" >> $LOGFILE ||
printf "Installing X login daemon: Failed\n" >> $LOGFILE

# Stop service for the case this is an upgrade
systemctl -q is-active frontend
if [[ $? -eq 0 ]] ; then
    systemctl stop frontend
fi
systemctl -q is-active backend
if [[ $? -eq 0 ]] ; then
    systemctl stop backend
fi
systemctl -q is-active checksample
if [[ $? -eq 0 ]] ; then
    systemctl stop checksample
fi
# The xlogin@$APPUSER and frontend in user home is not used any more.
# The following related lines is for making a smooth upgrade.
systemctl -q is-active xlogin@$APPUSER
if [[ $? -eq 0 ]] ; then
    systemctl stop xlogin@$APPUSER
    systemctl disable xlogin@$APPUSER
fi
if [[ -f "${APPHOME}"/.config/systemd/user/frontend.service ]] ; then
    # The following do not work as the systemd dbus session do not get transfered through sudo.
    # Not sure how to do it.
    # Anyway, it is just a nice things for developer upgrades from pre release versions.
    #systemctl -q --user is-active frontend
    #if [[ $? -eq 0 ]] ; then
    #    systemctl --user stop frontend
    #fi
    printf "If this is an upgrade of an earlier release, you should manually stop the old frontend or reboot.\n"
    # Clean out old files if present
    rm -rf "${APPHOME}"/.config/systemd/user/frontend.service
    rm -rf "${APPHOME}"/.config/systemd/user/default.target.wants/frontend.service
fi
# setup services
cp $DIRECTORY/backend.service /etc/systemd/system/ &&
cp $DIRECTORY/checksample.service /etc/systemd/system/ &&
cp $DIRECTORY/frontend.service /etc/systemd/system/ &&
printf "Copy .service files: Succes\n" >> $LOGFILE ||
printf "Copy .service files: Failed\n" >> $LOGFILE
systemctl daemon-reload

if [ -z "${DEVSYSTEM+x}" ] ; then
    # Only setup for auto start if not a dev system
    # Set the backend and frontend to auto start
    sudo -u $APPUSER cp $DIRECTORY/xinitrc "${APPHOME}"/.xinitrc &&
    systemctl enable backend &&
    systemctl enable checksample &&
    systemctl enable frontend &&
    printf "Enable services: Succes\n" >> $LOGFILE ||
    printf "Enable services: Failed\n" >> $LOGFILE
    # For now, simulate barcode to skip that part.
    # TODO: Remove simulate barcode when GUI is ready
    echo 'fake_barcode = "000000000000"' > ${APPHOME}/application/simulate.py
    chown $APPUSER:$APPGROUP ${APPHOME}/application/simulate.py
else
    systemctl disable frontend &&
    systemctl enable backend &&
    systemctl enable checksample &&
    systemctl start backend &&
    systemctl start checksample &&
    printf "Development system: Enabled and started the backend and checksample daemon\n" >> $LOGFILE ||
    printf "Enable services: Failed\n" >> $LOGFILE
fi

if [ -z "${SIMULATE+x}" ] ; then
    if [ -n "${DEVSYSTEM+x}" ] ; then
        echo "Setting up to run with simulated power off"
        echo "fake_power = True" > "${APPHOME}"/application/simulate.py
    fi
else
    echo "Setting up to run with full simulated hardware"
    sudo -u $APPUSER cp $DIRECTORY/test/* "${APPHOME}"/application/
fi

# Change ownership of logfile
chown $APPUSER:$APPGROUP $LOGFILE

if [ -z "${DEVSYSTEM+x}" ] ; then
    echo "Installation has finished"
    echo "Please use the command 'passwd' to set a proper password!"
else
    echo "You can start the frontend now by running the testapp.sh on the desktop."
    echo "Using power off in the gui will just kill all chromium browsers and thus exit the gui."
fi
