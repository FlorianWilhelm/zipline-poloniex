# -*- coding: utf-8 -*-
"""
Little dummy agent for testing
"""
import logging

from zipline.api import order, record, symbol
from zipline_poloniex.utils import setup_logging

__author__ = "Florian Wilhelm"
__copyright__ = "Florian Wilhelm"
__license__ = "new-bsd"

# setup logging and all
setup_logging(logging.INFO)
_logger = logging.getLogger(__name__)
_logger.info("Dummy agent loaded")


def initialize(context):
    _logger.info("Initializing agent...")
    # There seems no "nice" way to set the emission rate to minute
    context.sim_params._emission_rate = 'minute'


def handle_data(context, data):
    _logger.debug("Handling data...")
    order(symbol('ETH'), 10)
    record(ETH=data.current(symbol('ETH'), 'price'))
