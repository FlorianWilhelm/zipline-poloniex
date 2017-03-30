# -*- coding: utf-8 -*-
"""
Additional utilities
"""
import logging
from datetime import datetime

from pytz import timezone

__author__ = "Florian Wilhelm"
__copyright__ = "Florian Wilhelm"
__license__ = "new-bsd"

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

