#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the complete process of checking a sample."""

__copyright__ = "Copyright (C) 2020 Nordetect"

import sys
from os import path, makedirs
import logging
from typing import Callable
from io import StringIO


class LoggerWriter(StringIO):

    """Class to use as replacement for sys.stdout and sys.stderr.

    It will write to with the function given on construction time instead of
    the normal writing to stdout/stderr.

    """

    def __init__(self, loggerfunc: Callable[[str], None]) -> None:
        """Constructor.

        Parameters:
            loggerfunc: The write function to use whenever write is called.

        """
        self.out = loggerfunc

    def write(self, message: str) -> int:
        """Write a message with the help of the logger function.

        Parameters:
            message: Text to write.
        Returns:
            To be compatible with StringIO write, this returns the length of
            the message given, indicating all data has been handled.

        """
        if message != '\n':
            self.out(message)
        return len(message)

    def flush(self) -> None:
        """An empty compatibility function."""
        pass


def setup_file_log(dirname: str, filename: str) -> None:
    """Setup to log to a file instead of writing to stdout and stderr.

    Parameters:
        dirname: Directory to put the log file.
        filename: Name of the logfile.

    """
    makedirs(path.abspath(dirname), exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s:%(levelname)s: %(message)s',
        filename=path.join(dirname, filename),
        filemode='a'
    )
    log = logging.getLogger('nordetect')
    sys.stdout = LoggerWriter(log.debug)
    sys.stderr = LoggerWriter(log.error)


if __name__ == '__main__':
    outfilename = "filelogtest.log"
    print("Starting test to log everything to {0}".format(outfilename))
    setup_file_log('.', outfilename)
    print("stdout test")
    print("")
    print("stderr test", file=sys.stderr)
