# -*- coding: utf-8 -*-
"""
API of Poloniex
"""
import logging

import requests
import pandas as pd

from .utils import unix_time, throttle

__author__ = "Florian Wilhelm"
__copyright__ = "Florian Wilhelm"
__license__ = "mit"

_logger = logging.getLogger(__name__)

API_URL = "https://poloniex.com/public"


class TradesExceeded(Exception):
    pass


class RequestError(Exception):
    pass


@throttle(6)
def call_api(command, **kwargs):
    """Call to Poloniex API

    Args:
        command (str): API command
        **kwargs: additional request parameters

    Returns:
        pandas.DataFrame: dataframe containing the results
    """
    payload = dict(command=command)
    payload.update(kwargs)
    r = requests.get(API_URL, params=payload)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and 'error' in data.keys():
        raise RequestError(data['error'])
    return pd.DataFrame(data)


def get_currencies():
    """Fetch all available currency pairs, i.e. asset pairs

    Returns:
        pandas.DataFrame: dataframe containing asset pairs
    """
    return call_api('returnCurrencies').transpose()


def get_trade_hist(pair, start, end):
    """Fetch trade history of an asset pair in given period

    Args:
        pair (str): asset pair name
        start (pandas.Timestamp): start of period
        end (pandas.Timestamp): end of period

    Returns:
        pandas.DataFrame: dataframe containing period's trades
    """
    start, end = unix_time(start), unix_time(end)
    trades = call_api('returnTradeHistory',
                      currencyPair=pair,
                      start=start,
                      end=end)
    if trades.empty:  # make sure we add the expected columns
        trades = pd.DataFrame(
            columns=["globalTradeID", "tradeID", "date", "type",
                     "rate", "amount", "total"])
    if trades.shape[0] >= 50000:
        raise TradesExceeded("Number of trades exceeded")
    return trades


def get_chart_data(pair, start, end, period=1800):
    """Fetch chart data for asset pair in given period

    Args:
        pair (str): asset pair name
        start (pandas.Timestamp): start of period
        end (pandas.Timestamp): end of period
        period: period span in seconds

    Returns:
        pandas.DataFrame: dataframe containing candle stick data
    """
    valid_periods = (300, 900, 1800, 7200, 14400, 86400)
    assert period in valid_periods, "Invalid period"
    start, end = unix_time(start), unix_time(end)
    return call_api('returnChartData',
                    currencyPair=pair,
                    start=start,
                    end=end,
                    period=period)
