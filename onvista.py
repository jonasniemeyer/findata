import json
import requests
import pandas as pd
from finance_data.utils import HEADERS

class _OnvistaAbstractReader:
    def __init__(self, isin) -> None:
        self._isin = isin
        self._data = self._get_data()
        self._name = self._data["instrument"]["name"]

    def _get_data(self) -> dict:
        if self.__class__.__name__ == "OnvistaStockReader":
            section = "aktien" 
        elif self.__class__.__name__ == "OnvistaBondReader":
            section = "anleihen"
        else:
            raise NotImplementedError()

        html = requests.get(f"https://www.onvista.de/aktien/handelsplaetze/{self.isin}", headers=HEADERS).text
        data = json.loads(html.split('type="application/json">')[-1].split("</script>")[0])["props"]["pageProps"]["data"]["snapshot"]
        return data

    def historical_data(self) -> pd.DataFrame:
        identifier = self._data["quoteList"]["list"][0]["market"]["idNotation"]
        return _OnvistaAbstractReader.get_historical_data(identifier)

    @property
    def isin(self) -> str:
        return self._isin

    @property
    def name(self) -> str:
        return self._name
    
    def exchanges(self):
        return

    @staticmethod
    def get_historical_data(identifier) -> pd.DataFrame:
        js = requests.get(f"https://api.onvista.de/api/v1/instruments/STOCK/{identifier}/eod_history?idNotation={identifier}&range=5Y&startDate=2020-06-26", headers=HEADERS).json()
        return js


class OnvistaStockReader(_OnvistaAbstractReader):
    pass


class OnvistaBondReader(_OnvistaAbstractReader):
    pass