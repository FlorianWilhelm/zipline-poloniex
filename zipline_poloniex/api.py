# -*- coding: utf-8 -*-
"""
API of Poloniex
"""
import logging

import requests
import pandas as pd

from .utils import unix_time

__author__ = "Florian Wilhelm"
__copyright__ = "Florian Wilhelm"
__license__ = "new-bsd"

_logger = logging.getLogger(__name__)

API_URL = "https://poloniex.com/public"


class TradesExceeded(Exception):
    pass


class RequestError(Exception):
    pass


def call_api(command, **kwargs):
    payload = dict(command=command)
    payload.update(kwargs)
    r = requests.get(API_URL, params=payload)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and 'error' in data.keys():
        raise RequestError(data['error'])
    return pd.DataFrame(data)


def get_currencies():
    return call_api('returnCurrencies').transpose()


def get_trade_hist(pair, start, end):
    start, end = unix_time(start), unix_time(end)
    trades = call_api('returnTradeHistory',
                      currencyPair=pair,
                      start=start,
                      end=end)
    if trades.shape[0] >= 50000:
        raise TradesExceeded("Number of trades exceeded")
    return trades


def get_chart_data(pair, start, end, period=1800):
    valid_periods = (300, 900, 1800, 7200, 14400, 86400)
    assert period in valid_periods, "Invalid period"
    start, end = unix_time(start), unix_time(end)
    return call_api('returnChartData',
                    currencyPair=pair,
                    start=start,
                    end=end,
                    period=period)
