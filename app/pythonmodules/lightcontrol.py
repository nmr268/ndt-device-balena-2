#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Control of light."""

__copyright__ = "Copyright (C) 2020 Nordetect"

import sys
try:
    from simulate import fake_light
except ImportError:
    fake_light = False
from os.path import basename
from time import sleep
from sys import argv
import subprocess
from typing import Tuple
from colortable import colortable
if not fake_light:
    import RPi.GPIO as GPIO


RGB = Tuple[int,  int,  int]

SUCCESS = 0
WRONG_ARGUMENT = 1
UNKNOWN_ERROR = 2


def uv_on() -> None:
    """Turn on the UV light."""
    if not fake_light:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(6, GPIO.OUT)
        GPIO.output(6, GPIO.HIGH)


def uv_off() -> None:
    """Turn off the UV light."""
    if not fake_light:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(6, GPIO.OUT)
        GPIO.output(6, GPIO.LOW)


def colorstring(rgb: RGB) -> str:
    """Transform an RGB tuple to a string usable for the setlight program.

    The setlight program expects a string RRGGBB where RR, GG, BB is
    red, green and blue hex values.
    No bound checks are made on the rgb values.

    Parameters:
        rgb: A tuple of bytes (red, green, blue)
    Returns:
        A proper formatted string for the setlight program.

    """
    r_part = rgb[0] << 16
    g_part = rgb[1] << 8
    b_part = rgb[2]
    return hex(r_part | g_part | b_part)


def setcolorvalue(colorvalue: str, wait_ms: int = 10) -> None:
    """Set the color of the LED's using the external setlight program.

    Parameters:
        colorvalue: The color string representing the color we want.
            The function colorstring(rgb) will return a proper string.
        wait_ms: Wait many milliseconds after setting the color.

    """
    if not fake_light:
        res = subprocess.run(['setlight', '{0}'.format(colorvalue)])
        if res.returncode != 0:
            raise Exception("Could not change the LED color")
    sleep(wait_ms/1000.0)


def setcolor(rgb: RGB, wait_ms: int = 10) -> None:
    """Set the color of the LED's using the exteranl setlight program.

    Parameters:
        rgb: An RGB tuple representing the coler to set.
        wait_ms: Wait many milliseconds after setting the color.

    """
    setcolorvalue(colorstring(rgb), wait_ms)


def usage(commandname: str) -> None:
    """Print some usage information.

    Parameters:
        commandname: The name used to call this program.

    """
    known_keys = colortable.keys()
    last_color = list(known_keys)[-1]
    print("You can use '{0}' in three ways:".format(commandname))
    print("1) Call it with three arguments: Red, green and blue.")
    print("   Each value should be in the interval [0-255].")
    print("   E.g.: {0} 123 0 200".format(commandname))
    print("2) Call it with one argument, a color name.")
    print("   Known colors:")
    print("   {0}".format(",".join(known_keys)))
    print("   E.g.: {0} {1}".format(commandname, last_color))
    print("3) Let the color name be part of the command name.")
    print("   The first three letters is skipped and the last three are skipped.")
    print("   This is best accomplished by making a softlink to the command.")
    print("   E.g.: ln -s {0} epi{1}.py ; epi{1}.py".format(commandname, last_color))


def is_byte(value: int) -> bool:
    """Check if an integer value is in the interval [0-255].

    Parameters:
        value: Value to check.
    Returns:
        True or False depending on result of check.

    """
    return (value >= 0) and (value <= 255)


def _colorname_to_rgb(colorname: str) -> RGB:
    """Helper function for main to converting a color name to an RGB tuple.

    Note this function exit the program on exit, hence the private nature and
    only supposed to be used by the main function.

    Parameters:
        colorname: A named color, e.g. red.
    Returns:
        An RGB tuple.

    """
    if colorname not in colortable:
        usage(callname)
        sys.exit(WRONG_ARGUMENT)
    return colortable[colorname]


if __name__ == '__main__':
    try:
        callname = basename(__file__)
        argc = len(argv)-1
        if argc == 0:
            # The color is part of the command name
            # Strip epi in beginning and .py in the end
            color = _colorname_to_rgb(callname[3:-3])
        elif argc == 1:
            # The argument is the color name
            color = _colorname_to_rgb(argv[1])
        elif argc == 3:
            # The three arguments should be red, green and blue values
            try:
                red = int(argv[1])
                green = int(argv[2])
                blue = int(argv[3])
            except ValueError:
                usage(callname)
                sys.exit(WRONG_ARGUMENT)
            if not (is_byte(red) and is_byte(blue) and is_byte(green)):
                usage(callname)
                sys.exit(WRONG_ARGUMENT)
            color = (red, green, blue)
        else:
            usage(callname)
            sys.exit(WRONG_ARGUMENT)
        setcolor(color)
    except Exception:
        sys.exit(UNKNOWN_ERROR)
