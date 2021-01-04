#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capture images.

You can simulate the hardware used here by using a simulate.py file.
See description in the test/simulate module.

"""

__copyright__ = "Copyright (C) 2020 Nordetect"

from typing import Tuple, List, Optional
try:
    from simulate import fake_capture
except ImportError:
    fake_capture = {}
from time import sleep, time, clock_gettime, CLOCK_MONOTONIC
import lightcontrol
from lightcontrol import RGB
import cv2
import numpy as np
if not fake_capture:
    from picamera import PiCamera
    from picamera.array import PiRGBArray
else:
    class FakePiRGBArray:
        """Fake class to make it easier to work without picamera."""
        def __init__(self) -> None:
            self.array = None

        def truncate(self, position: int) -> None:
            pass

WINDOW = Tuple[int, int, int, int]


class Camera:

    """Handling of everything related to capture images.

    This includes initializing the camera, setting up the light, capturing
    images and running preview.

    It keeps track of camera warmup time and light settle time for you and
    will automatically wait with a capture until it is ready.

    Images are stored and saved in png format.

    """

    uv_shutter = 5000
    """Shutter speed used with UV light."""
    uv_gains = (1.2, 1.2)
    """Gain settings used with UV light."""
    rgb_shutter = 500
    """Shutter speed used with RGB light."""
    rgb_gains = (1.0, 1.0)
    """Gain settings used with RGB light."""
    light_settle_time = 0.5
    """Time needed from setting the light until it is ready."""
    camera_warmup_time = 15
    """Time needed from initializing the camera until it is ready."""
    capture_resulution = (640, 480)

    def __init__(self) -> None:
        """Constructor. The camera warmup time is counted from here.
        So if you want to minimize wait time, make the Camera object early."""
        self.light_change = clock_gettime(CLOCK_MONOTONIC)
        self.light_settled = False
        self.cam_inittime = self.light_change
        self.cam_ready = False
        if not fake_capture:
            self.cam = PiCamera()
            self.cam_inittime = clock_gettime(CLOCK_MONOTONIC)
            self.cam.exposure_mode = 'off'
            self.cam.awb_mode = 'off'
            self.cam.resolution = Camera.capture_resulution
            self.cam.iso = 100
            # Not sure why there is a sleep here
            sleep(1)
            self.cam.shutter_speed = Camera.rgb_shutter
            self.cam.awb_gains = Camera.rgb_gains
            self.buf = PiRGBArray(self.cam)
        else:
            self.buf = FakePiRGBArray()
        self.rgb = (-1, -1, -1)
        self.uv = -1
        self.timestamp = 0.0

    def setup_uv(self) -> None:
        """Change the camera to UV light mode."""
        if not fake_capture:
            self.cam.shutter_speed = Camera.uv_shutter
            self.cam.awb_gains = Camera.uv_gains

    def setup_rgb(self) -> None:
        """Change the camera to RGB light mode."""
        if not fake_capture:
            self.cam.shutter_speed = Camera.rgb_shutter
            self.cam.awb_gains = Camera.rgb_gains

    def setlight(self, rgb: RGB, uv: int = 0) -> None:
        """Switch the light.

        It will automatically keep track of the light set and only reset
        light settle time if the light changes.

        Parameters:
            rgb: RGB tuple describing the RGB part of the light we want.
            uv: The UV intensity we want. Only supporting 0 off and >=1 on.

        """
        changed = False
        if (rgb != self.rgb):
            self.rgb = rgb
            lightcontrol.setcolor(rgb)
            changed = True
        if uv != self.uv:
            self.uv = uv
            if uv > 0:
                lightcontrol.uv_on()
            else:
                lightcontrol.uv_off()
            changed = True
        if changed:
            self.light_change = clock_gettime(CLOCK_MONOTONIC)
            self.light_settled = False

    def wait_for_ready(self, wait_for_light: bool = True) -> float:
        """Wait until ready to capture an image.

        Returns:
            How long it waited.

        """
        waittime = 0.0
        now = 0.0
        if wait_for_light and not self.light_settled:
            now = clock_gettime(CLOCK_MONOTONIC)
            waittime = Camera.light_settle_time - (now - self.light_change)
            self.light_settled = True
        if not self.cam_ready:
            if now == 0:
                now = clock_gettime(CLOCK_MONOTONIC)
            waittime = max(waittime, Camera.camera_warmup_time - (now - self.cam_inittime))
            self.cam_ready = True
        if waittime > 0:
            sleep(waittime)
        return max(waittime, 0)

    def capture_image(self) -> None:
        """Capture a single image. Set a time stamp on it after capture."""
        # Start with a cleared image buffer
        self.buf.truncate(0)
        # Make sure the light have settled and the camera has warmed up
        self.wait_for_ready()
        # Take the picture
        if fake_capture:
            (r, b, g) = self.rgb
            color = (r, b, g, self.uv)
            if color not in fake_capture:
                color = (-1, -1, -1, -1)
            infilename = fake_capture[color]
            self.buf.array = cv2.imread(infilename)
        else:
            self.cam.capture(self.buf, 'bgr')
        self.timestamp = time()

    def capture_bayer_image(self, basename) -> None:
        """Capture a single image with appended bayer data. Set a time stamp on it after capture."""

        if fake_capture:
            raise Exception("Fake capture not supported when storing bayer data")

        # Start with a cleared image buffer
        self.buf.truncate(0)
        # Make sure the light have settled and the camera has warmed up
        self.wait_for_ready()

        self.timestamp = time()

        # Take the picture
        filename = "{0}_{1:.2f}.jpg".format(basename, self.timestamp)
        self.cam.capture(f"{filename}", 'jpeg', bayer=True)

    def save_image(self, filename: str) -> None:
        """Save the image to a file (in png format).

        Parameters:
            filename: The full path of where to store the image.

        """
        cv2.imwrite(filename, self.buf.array)

    def save_stamped_image(self, basename: str) -> None:
        """Save the image with the stamp as part of the name.

        It is expected that the stamp is the one set by the capture function.
        This is seconds since epoch and will be rounded to an integer.

        Parameters:
            basename: The full filepath will be <basename>_<stamp>.png

        """
        # We round of the timestamp to two decimals to avoid too long names.
        filename = "{0}_{1:.2f}.png".format(basename, self.timestamp)
        self.save_image(filename)

    def capture_average(self, timelist: Optional[List[float]] = None, starttime: Optional[float] = None) -> None:
        """capture images and save an average over them.

        It will count the timing from right after entering this function
        or from the time given as parameter.
        If the capture can not keep up with the times given, it will just
        capture as fast as possible.

        Parameters:
            timelist: A list of times counted as seconds since calling this.
            starttime: Time to count from. If None, count from calling this.

        """
        if starttime is None:
            start_run_time = clock_gettime(CLOCK_MONOTONIC)
        else:
            start_run_time = starttime
        if timelist is None:
            # Just used three images captured as fast as possible
            timelist = [0, 0, 0]
        imagecount = len(timelist)
        # We need to cast from uint8 to something where we will not get
        # overruns.
        # Using np.float32 as that seems to be the fastest.
        # Image array dimensions is height, width, colorvalues.
        array_dimensions = (self.capture_resulution[1], self.capture_resulution[0], 3)
        imagesum = np.zeros(array_dimensions, np.float32)
        self.wait_for_ready()
        for index, delta_time in enumerate(timelist):
            run_time = clock_gettime(CLOCK_MONOTONIC) - start_run_time
            sleep_time = delta_time - run_time
            if sleep_time > 0:
                sleep(sleep_time)
            self.capture_image()
            imagesum += self.buf.array.astype(np.float32)
            if index == imagecount // 2:
                timestamp = self.timestamp
        imagesum /= imagecount
        self.buf.array = imagesum.astype(np.uint8)
        self.timestamp = timestamp

    def capture(self, basename: str, timelist: Optional[List[float]] = None, wait_first: bool = False, bayer=False) -> None:
        """Capture a series of images on specific times.

        TODO: Some better way of handling if the captures fall behind schedule.
            Maybe timestamps should not in whole seconds? It would help if they
            could be float instead of integers in save_stamped_image. Then it
            could be a simple check if it has pasted the next time stamp.

        Parameters:
            basename: Basename of image files stored.
                The full filepath will be <basename>_<timestamp>.png
            timelist: A list of times counted as seconds since calling this.
            wait_first: Should zero time be after waiting for the camera and
                light to be ready?

        """
        if timelist is None:
            timelist = [0]
        if wait_first:
            self.wait_for_ready()
        start_run_time = clock_gettime(CLOCK_MONOTONIC)
        for index, delta_time in enumerate(timelist):
            run_time = clock_gettime(CLOCK_MONOTONIC) - start_run_time
            sleep_time = delta_time - run_time
            skip = False
            if sleep_time > 0:
                sleep(sleep_time)
            else:
                # TODO: Make this handling better
                # If we are already past half a second before next capture,
                # skip it as it will most likely be overriden by the next image
                # anyway. This is just a rough hack to avoid too many
                # delayed and overriden images.
                if index < len(timelist) - 1:
                    if timelist[index+1] - run_time < 0.5:
                        skip = True
            if not skip:
                if bayer:
                    self.capture_bayer_image(basename)
                else:
                    self.capture_image()
                    self.save_stamped_image(basename)

    def start_preview(self, fullscreen: bool = False, window: WINDOW = (400, 0, 400, 400)) -> None:
        """Start a preview window.

        Parameters:
            fullscreen: Should the preview run in fullscreen mode?
            window: Tuple of (x, y, width, height) defining placement and size.

        """
        if not fake_capture:
            self.cam.start_preview(fullscreen=fullscreen, window=window)

    def stop_preview(self) -> None:
        """Stop a running preview."""
        if not fake_capture:
            self.cam.stop_preview()


if __name__ == '__main__':
    print("Testing capture")
    camera = Camera()
    camera.setlight((255, 0, 0))
    print("Taking series of red photos")
    camera.capture('test_red', [1, 2, 7, 9, 14])
    camera.setlight((0, 0, 0), 255)
    print("Taking single uv photo")
    camera.capture('test_uv')
    camera.setlight((0, 0, 255))
    print("Taking single blue photo")
    camera.capture('test_blue_1')
    print("Taking average blue photo")
    camera.capture_average([2, 4, 5, 6, 7, 8])
    camera.save_image('test_blue_average.png')
    print("Taking single blue photo")
    camera.capture('test_blue_2')
    camera.setlight((0, 0, 0))
