import json
import requests
import pandas as pd
import numpy as np
from typing import Union
from finance_data.utils import HEADERS

class _OnvistaAbstractReader:
    """
    _OnvistaAbstractReader is the base class for OnvistaStockReader and OnvistaBondReader.
    It implements shared attributes and methods across all readers and how the historical price data is parsed, while
    the derived classes implement their own security-specific methods (e.g. OnvistaBondReader.duration and OnvistaStockReader.income_statement).
    """
    def __init__(self, isin) -> None:
        self._isin = isin
        self._data = self._get_data()
        self._name = self._data["instrument"]["name"]

    def _get_data(self) -> dict:
        if self.__class__.__name__ == "OnvistaStockReader":
            section = "aktien"
        elif self.__class__.__name__ == "OnvistaBondReader":
            section = "anleihen"
        elif self.__class__.__name__ == "OnvistaFundReader":
            section = "fonds"
        else:
            raise NotImplementedError()

        html = requests.get(f"https://www.onvista.de/{section}/handelsplaetze/{self.isin}", headers=HEADERS).text
        data = json.loads(html.split('type="application/json">')[-1].split("</script>")[0])["props"]["pageProps"]["data"]["snapshot"]
        return data

    @property
    def isin(self) -> str:
        return self._isin

    @property
    def name(self) -> str:
        return self._name

    def historical_data(
        self,
        start: Union[int, str],
        end: Union[int, str] = pd.to_datetime("today").date().isoformat()
    ) -> dict:
        identifier = self._data["quoteList"]["list"][1]["market"]["idNotation"]
        return _OnvistaAbstractReader.get_historical_data(identifier, start, end)
    
    def exchanges(self):
        return

    @staticmethod
    def get_historical_data(
        identifier: int,
        start: Union[int, str],
        end: Union[int, str] = pd.to_datetime("today").date().isoformat()
    ) -> dict:
        if isinstance(start, int):
            start = pd.to_datetime(start, unit="s")
        elif isinstance(start, str):
            start = pd.to_datetime(start)

        if isinstance(end, int):
            end = pd.to_datetime(end, unit="s")
        elif isinstance(end, str):
            end = pd.to_datetime(end)

        js = requests.get(f"https://api.onvista.de/api/v1/instruments/STOCK/{identifier}/eod_history?idNotation={identifier}&range=5Y&startDate=1900-01-01", headers=HEADERS).json()
        dataset_start = pd.to_datetime(pd.to_datetime(js["datetimeStartAvailableHistory"]).date())
        dataset_end = pd.to_datetime(pd.to_datetime(js["datetimeEndAvailableHistory"]).date())

        information = {
            "instrument_id": js["idInstrument"],
            "dataset_id": js["idNotation"],
            "start": dataset_start.date().isoformat(),
            "end": dataset_end.date().isoformat(),
            "exchange": {
                "name": js["market"]["name"],
                "code": js["market"]["codeMarket"],
                "country": js["market"]["isoCountry"]
            },
            "currency": js["isoCurrency"]
        }

        if start < dataset_start:
            start = dataset_start

        end_reached = False
        subsamples = []
        while not end_reached:
            js = requests.get(f"https://api.onvista.de/api/v1/instruments/STOCK/{identifier}/eod_history?idNotation={identifier}&range=5Y&startDate={start}", headers=HEADERS).json()
            start = start + pd.offsets.DateOffset(years=5)
            if start >= end or start >= dataset_end:
                end_reached = True

            df = pd.DataFrame(index=js["datetimeLast"])
            df.index = pd.to_datetime(df.index, unit="s")
            df["open"] = js["first"]
            df["high"] = js["high"]
            df["low"] = js["low"]
            df["close"] = js["last"]
            df["simple_returns"] = df["close"].pct_change()
            df["log_returns"] = np.log(df["close"]/df["close"].shift(1))
            subsamples.append(df)
        data = pd.concat(subsamples)

        return {
            "information": information,
            "data": data
        }


class OnvistaStockReader(_OnvistaAbstractReader):
    pass


class OnvistaBondReader(_OnvistaAbstractReader):
    pass


class OnvistaFundReader(_OnvistaAbstractReader):
    pass