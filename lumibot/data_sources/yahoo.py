import logging
from datetime import datetime

import pandas as pd
import yfinance as yf

from lumibot.entities import Bars

from .data_source import DataSource


class YahooData(DataSource):
    MIN_TIMESTEP = "day"
    TIMESTEP_MAPPING = [
        {"timestep": "day", "represntations": ["1D", "day"]},
    ]

    def __init__(self):
        self.name = "yahoo"
        self._data_store = {}

    def _pull_source_symbol_bars(
        self, symbol, length, timestep=MIN_TIMESTEP, timeshift=None
    ):
        self._parse_source_timestep(timestep, reverse=True)
        if symbol in self._data_store:
            data = self._data_store[symbol]
        else:
            data = yf.Ticker(symbol).history(period="max")
            self._data_store[symbol] = data

        if timeshift:
            end = datetime.now() - timeshift
            data = data[data.index <= end]

        result = data.tail(length)
        return result

    def _pull_source_bars(
        self, symbols, length, timestep=MIN_TIMESTEP, timeshift=None
    ):
        """pull broker bars for a list symbols"""
        self._parse_source_timestep(timestep, reverse=True)
        missing_symbols = [
            symbol for symbol in symbols if symbol not in self._data_store
        ]
        tickers = yf.Tickers(" ".join(missing_symbols))
        for ticker in tickers.tickers:
            self._data_store[ticker.ticker] = ticker.history(period="max")

        result = {}
        for symbol in symbols:
            result[symbol] = self._pull_source_symbol_bars(
                symbol, length, timestep=timestep, timeshift=timeshift
            )
        return result

    def _parse_source_symbol_bars(self, response):
        df = response.copy()
        df.columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "dividend",
            "stock_splits",
        ]
        df["price_change"] = df["close"].pct_change()
        df["dividend_yield"] = df["dividend"] / df["close"]
        df["return"] = df["dividend_yield"] + df["price_change"]
        bars = Bars(df, raw=response)
        return bars

    def _parse_source_bars(self, response):
        result = {}
        for symbol, bars in response.items():
            result[symbol] = self._parse_source_symbol_bars(bars)
        return result