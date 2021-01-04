This is code to control the LED strip used as light for the camera.

The rpi_ws281x directory is the upstream library found at:
https://github.com/pimoroni/rpi_ws281x
The current used version is commit:
1e900b2c1af5d9365e275ad4f77ee01270851483

The program setlight made from setlight.c is very simple.
It just sets the color given as one hexidecimal argument: RRGGBB (Red, Green, Blue).
If the hardware setup changes, you need to change the value in the start of setlight.c
The setlight program is install suid, which means it will always run as root.
This is needed because the library needs access to '/dev/mem'.
By installing it suid, the user do not need to be root to use it.

Compile:
make
Install:
sudo make install
