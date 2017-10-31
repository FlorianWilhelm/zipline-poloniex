# -*- coding: utf-8 -*-
"""
Additional utilities
"""
import sys
import time
import logging
import functools
from math import fabs
from datetime import datetime

from pytz import timezone

__author__ = "Florian Wilhelm"
__copyright__ = "Florian Wilhelm"
__license__ = "mit"

_logger = logging.getLogger(__name__)


def unix_time(dt):
    """Convert datetime to seconds since epoch

    Args:
        dt: datetime object

    Returns:
        seconds since epoch
    """
    epoch = datetime.utcfromtimestamp(0).replace(tzinfo=timezone('UTC'))
    dt = dt.replace(tzinfo=timezone('UTC'))
    return (dt - epoch).total_seconds()


def throttle(calls, seconds=1):
    """Decorator for throttling a function to number of calls per seconds

    Args:
        calls (int): number of calls per interval
        seconds (int): number of seconds in interval

    Returns:
        wrapped function
    """
    assert isinstance(calls, int), 'number of calls must be integer'
    assert isinstance(seconds, int), 'number of seconds must be integer'

    def wraps(func):
        # keeps track of the last calls
        last_calls = list()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            curr_time = time.time()
            if last_calls:
                # remove calls from last_calls list older then interval in seconds
                idx_old_calls = [i for i, t in enumerate(last_calls) if t < curr_time - seconds]
                if idx_old_calls:
                    del last_calls[:idx_old_calls[-1]]
            if len(last_calls) >= calls:
                idx = len(last_calls) - calls
                delta = fabs(1 - curr_time + last_calls[idx])
                logger = logging.getLogger(func.__module__)
                logger.debug("Stalling call to {} for {}s".format(func.__name__, delta))
                time.sleep(delta)
            resp = func(*args, **kwargs)
            last_calls.append(time.time())
            return resp

        return wrapper

    return wraps


def activate_live_debugging():
    """Activates live debugging with IPython's pdb
    """
    _logger.info("Activating live debugging...")
    from IPython.core import ultratb
    sys.excepthook = ultratb.FormattedTB(mode='Verbose', color_scheme='Linux', call_pdb=1)


def setup_logging(loglevel):
    """Setup basic logging
    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")
