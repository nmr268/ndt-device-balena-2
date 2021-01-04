# -*- coding: utf-8 -*-
"""Some small helpers for communicing with checksample."""

__copyright__ = "Copyright (C) 2020 Nordetect"

import commonconfig
from os import path, makedirs, kill
import signal


def store_daemon_pid(pid: int) -> None:
    """Store the given PID in a file for the Control class to find.

    Parameters:
        pid: The PID to store.

    """
    with open(commonconfig.checksample_pid_file, 'w') as outfile:
        outfile.write(str(pid))


class Control:

    """Class to control the checksample process."""

    @staticmethod
    def _send_signal(sig: int) -> bool:
        """Send a signal to the checksample process.

        Parameters:
            sig: The signal to send.
        Returns:
            True if successful. False if the PID could not be found.

        """
        try:
            with open(commonconfig.checksample_pid_file, 'r') as infile:
                pid = int(infile.read())
        except (IOError, ValueError):
            return False
        kill(pid, sig)
        return True

    @staticmethod
    def analyse() -> bool:
        """Ask the checksample process to start capture and analysis.

        Returns:
            True if successful. False if the PID could not be found.

        """
        return Control._send_signal(signal.SIGUSR1)

    @staticmethod
    def stop() -> bool:
        """Ask the checksample process to exit.

        Returns:
            True if successful. False if the PID could not be found.

        """
        return Control._send_signal(signal.SIGTERM)

    @staticmethod
    def abort() -> bool:
        """Ask the checksample process to abort current check.

        Returns:
            True if successful. False if the PID could not be found.

        """
        return Control._send_signal(signal.SIGHUP)


class Status:

    """Class to get and set the status of the checksample process."""

    READY = 'Ready'
    RUNNING = 'Checking sample'
    DONE = 'Done'
    ERROR = 'Error'
    UNAVAILABLE = 'Not running'

    @staticmethod
    def setup() -> None:
        """Make some initial setup."""
        makedirs(path.dirname(commonconfig.checksample_status_file), exist_ok=True)

    @staticmethod
    def set_status(status: str) -> None:
        """Set the current status so the GUI frontend can get it.

        Parameters:
            status: The status to set. Use the constants defined.

        """
        with open(commonconfig.checksample_status_file, 'w') as outfile:
            outfile.write(status)

    @classmethod
    def get_status(cls) -> str:
        """Get the current status of the analysis.

        Returns:
            A status string indication the current status.

        """
        try:
            with open(commonconfig.checksample_status_file, 'r') as infile:
                return infile.read()
        except IOError:
            return cls.UNAVAILABLE
