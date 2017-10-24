# -*- coding: utf-8 -*-
"""
Zipline bundle for Poloniex exchange
"""
import logging
from datetime import time, timedelta, datetime

from pytz import timezone
import numpy as np
import pandas as pd
from pandas.tseries.offsets import CustomBusinessDay
from zipline.utils.calendars import (
    TradingCalendar, register_calendar, register_calendar_alias,
    deregister_calendar)
from zipline.utils.memoize import lazyval

from .api import get_currencies, get_trade_hist

__author__ = "Florian Wilhelm"
__copyright__ = "Florian Wilhelm"
__license__ = "new-bsd"

_logger = logging.getLogger(__name__)


class Pairs(object):
    """Record object holding most common US-$ / crypto-currency pairs
    """
    usdt_btc = 'USDT_BTC'
    usdt_btc = 'USDT_BCH'
    usdt_eth = 'USDT_ETH'
    usdt_dash = 'USDT_DASH'
    usdt_etc = 'USDT_ETC'
    usdt_xmr = 'USDT_XMR'
    usdt_zec = 'USDT_ZEC'
    usdt_xrp = 'USDT_XRP'
    usdt_ltc = 'USDT_LTC'
    usdt_rep = 'USDT_REP'
    usdt_nxt = 'USDT_NXT'
    usdt_str = 'USDT_STR'


def fetch_assets(asset_pairs):
    """Fetch given asset pairs

    Args:
        asset_pairs (list): list of asset pairs

    Returns:
        pandas.DataFrame: dataframe of asset pairs
    """
    asset_pair_map = {pair.split("_")[1]: pair for pair in asset_pairs}
    all_assets = get_currencies()
    asset_df = all_assets.ix[asset_pair_map.keys()].reset_index()
    asset_df = asset_df[['index', 'name']].rename(
        columns={'index': 'symbol', 'name': 'asset_name'})
    asset_df['exchange'] = 'Poloniex'  # needed despite documented as optional
    return asset_df


def make_candle_stick(trades, freq='1T'):
    """Make a candle stick like chart

    Check [1] for resample rules:
    [1]: http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

    Args:
        trades (pandas.DataFrame): dataframe containing trades
        freq (str): frequency for resampling (default 1 minute)

    Returns:
        pandas.DataFrame: chart data
    """
    volume = trades['amount'].resample(freq).sum()
    volume = volume.fillna(0)
    high = trades['rate'].resample(freq).max()
    low = trades['rate'].resample(freq).min()
    open = trades['rate'].resample(freq).first()
    close = trades['rate'].resample(freq).last()
    return pd.DataFrame(
        dict(open=open, high=high, low=low, close=close, volume=volume))


def fetch_trades(asset_pair, start, end):
    """Helper function to fetch trades for a single asset pair

    Does all necessary conversions, sets `date` as index and assures
    that `start` and `end` are in the index.

    Args:
        asset_pair: name of the asset pair
        start (pandas.Timestamp): start of period
        end (pandas.Timestamp): end of period

    Returns:
        pandas.DataFrame: dataframe containing trades of asset
    """
    df = get_trade_hist(asset_pair, start, end)
    df['date'] = df['date'].apply(lambda x: datetime.strptime(
        x, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone('UTC')))
    for col in ('total', 'rate', 'amount'):
        df[col] = df[col].astype(np.float32)
    df = df.set_index('date')
    if start not in df.index:
        df.loc[start] = np.nan
    if end not in df.index:
        df.loc[end] = np.nan
    return df


def prepare_data(start, end, sid_map, cache):
    """Retrieve and prepare trade data for ingestion

    Args:
        start (pandas.Timestamp): start of period
        end (pandas.Timestamp): end of period
        sid_map (dict): mapping from symbol id to asset pair name
        cache: cache object as provided by zipline

    Returns:
        generator of symbol id and dataframe tuples
    """
    def get_key(sid, day):
        return "{}_{}".format(sid, day.strftime("%Y-%m-%d"))

    for sid, asset_pair in sid_map.items():
        for start_day in pd.date_range(start, end, freq='D', closed='left', tz='utc'):
            key = get_key(sid, start_day)
            if key not in cache:
                # This block of code splits the day into three 8 hour periods, fetches trades for each, then combines

                td1 = timedelta(hours=8, seconds=-1)
                td2 = timedelta(hours=8)

                end1 = start_day + td1
                start2 = start_day + td2
                end2 = end1 + td2
                start3 = start2 + td2
                end_day = start3 + td2

                print("Fetching data for {} from {} to {}".format(asset_pair, start_day, end_day))

                trades = pd.concat([fetch_trades(asset_pair, start_day, end1), fetch_trades(asset_pair, start2, end2), fetch_trades(asset_pair, start3, end_day)])
                cache[key] = make_candle_stick(trades)
            yield sid, cache[key]


def create_bundle(asset_pairs, start=None, end=None):
    """Create a bundle ingest function

    Args:
        asset_pairs (list): list of asset pairs
        start (pandas.Timestamp): start of trading period
        end (pandas.Timestamp): end of trading period

    Returns:
        ingest function needed by zipline's register.
    """
    def ingest(environ,
               asset_db_writer,
               minute_bar_writer,
               daily_bar_writer,
               adjustment_writer,
               calendar,
               start_session,
               end_session,
               cache,
               show_progress,
               output_dir,
               # pass these as defaults to make them 'nonlocal' in py2
               start=start,
               end=end):
        if start is None:
            start = start_session
        if end is None:
            end = end_session

        adjustment_writer.write()
        asset_df = fetch_assets(asset_pairs)
        asset_db_writer.write(equities=asset_df)
        # generate the mapping between sid and symbol name
        asset_map = asset_df['symbol'].to_dict()
        asset_pair_map = {pair.split("_")[1]: pair for pair in asset_pairs}
        sid_map = {k: asset_pair_map[v] for k, v in asset_map.items()}

        data = prepare_data(start, end, sid_map, cache)
        minute_bar_writer.write(data, show_progress=show_progress)
    return ingest


class PoloniexCalendar(TradingCalendar):
    """Trading Calender of Poloniex Exchange
    """
    @property
    def name(self):
        return "POLONIEX"

    @property
    def tz(self):
        return timezone('UTC')

    @property
    def open_time(self):
        return time(0, 0)

    @property
    def close_time(self):
        return time(23, 59)

    @lazyval
    def day(self):
        return CustomBusinessDay(
            weekmask='Mon Tue Wed Thu Fri Sat Sun'
        )


register_calendar('POLONIEX', PoloniexCalendar())
# The following is necessary because zipline's developer hard-coded NYSE
# everywhere in run_algo._run, *DOH*!!!
deregister_calendar('NYSE')
register_calendar_alias('NYSE', 'POLONIEX', force=False)
# Deleted the register function as the built in zipline register function plays better with other data bundles
