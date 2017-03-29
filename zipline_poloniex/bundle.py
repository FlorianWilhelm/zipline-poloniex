#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Zipline bundle for Poloniex exchange
"""
import logging
from datetime import time, datetime, timedelta

from pytz import timezone
import requests
import pandas as pd
from zipline.utils.calendars import TradingCalendar, register_calendar
from zipline.data.bundles import register

__author__ = "Florian Wilhelm"
__copyright__ = "Florian Wilhelm"
__license__ = "new-bsd"

_logger = logging.getLogger(__name__)

API_URL = "https://poloniex.com/public"


class Pairs(object):
    usdt_btc = 'USDT_BTC'
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


class TradesExceeded(Exception):
    pass


class RequestError(Exception):
    pass


def unix_time(dt):
    """Convert datetime to seconds since epoch

    Args:
        dt: datetime object

    Returns:
        seconds since epoch
    """
    epoch = datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds()


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


def get_chart_data(pair, start, end, period=1800):
    valid_periods = (300, 900, 1800, 7200, 14400, 86400)
    assert period in valid_periods, "Invalid period"
    start, end = unix_time(start), unix_time(end)
    return call_api('returnChartData',
                    currencyPair=pair,
                    start=start,
                    end=end,
                    period=period)


def write_assets(asset_db_writer, asset_pairs):
    asset_pair_map = {pair.split("_")[1]: pair for pair in asset_pairs}
    all_assets = get_currencies()
    asset_df = all_assets.ix[asset_pair_map.keys()].reset_index()
    asset_df = asset_df[['index', 'name']].rename(
        columns={'index': 'symbol', 'name': 'asset_name'})
    asset_db_writer.write(equities=asset_df)
    asset_map = asset_df['symbol'].to_dict()
    return {k: asset_pair_map[v] for k, v in asset_map.items()}


def make_candle_stick(df):
    freq = '1T'
    volume = df['total'].resample(freq).sum()
    volume = volume.fillna(0)
    high = df['rate'].resample(freq).max()
    low = df['rate'].resample(freq).min()
    open = df['rate'].resample(freq).first()
    close = df['rate'].resample(freq).last()
    return pd.DataFrame(dict(open=open,
                             high=high,
                             low=low,
                             close=close,
                             volume=volume))


def fetch_trades(asset_pair, start, end):
    df = get_trade_hist(asset_pair, start, end)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date')
    return df


def prepare_data(start, end, sid_map, cache):
    def get_key(sid, day):
        return "{}_{}".format(sid, day.strftime("%Y-%m-%d"))

    for sid, asset_pair in sid_map.items():
        for day in pd.date_range(start, end, freq='D', closed='left'):
            key = get_key(sid, day)
            if key not in cache:
                next_day = day + timedelta(days=1)
                trades = fetch_trades(asset_pair, day, next_day)
                cache[key] = trades
            yield sid, cache[key]


def create_bundle(asset_pairs, start=None, end=None):
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

        sid_map = write_assets(asset_db_writer, asset_pairs)
        data = prepare_data(start, end, sid_map, cache)
        minute_bar_writer.write(data, show_progress=show_progress)
    return ingest


class PoloniexCalendar(TradingCalendar):
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
        return time(23, 59, 59)


register_calendar('POLONIEX', PoloniexCalendar())
register(
    'poloniex_eth_2016',
    create_bundle(
        (
            Pairs.usdt_eth
        ),
        pd.Timestamp('2016-01-01', tz='utc'),
        pd.Timestamp('2016-12-31', tz='utc'),
    ),
    calendar_name='POLONIEX',
    minutes_per_day=24*60
)
