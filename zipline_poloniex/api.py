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


def get_trade_hist_alias(asset_pair, start, end):
    """Helper function to run api.get_trade_hist

    If a TradesExceeded exception is raised, it splits the timerange of
    (start) to (end) in half and calls itself with the new timeranges.

    This prevents any 'hotspots' where there is extremely high trading
    activity in a short period of time - eg on usdt_btc

    This also protects against any HTTPErrors (such as 404) that pop up
    seemingly at random.

    This function has the possibility of generating an endless loop, as it
    calls itself if any error is raised from get_trade_hist(). In practice,
    however, the HTTPError should not occur more than once (per API call),
    and the TradesExceeded error is limited to the amount of trades per day.

    Args:
        asset_pair: name of the asset pair
        start (pandas.Timestamp): start of period
        end (pandas.Timestamp): end of period

    Returns:
        pandas.DataFrame: dataframe containing trades of asset
    """
    original_timedelta = end - start
    try:
        df = get_trade_hist(asset_pair, start, end)
    except requests.exceptions.HTTPError:
        df = get_trade_hist_alias(asset_pair, start, end)
    except TradesExceeded:
        new_timedelta = original_timedelta / 2
        df = pd.concat([
            get_trade_hist_alias(asset_pair, start,start + new_timedelta - pd.offsets.Second()),
            get_trade_hist_alias(asset_pair, start + new_timedelta, end)])
    return df


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
