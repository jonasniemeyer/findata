import requests
import pandas as pd
import numpy as np
import datetime as dt
import re
from bs4 import BeautifulSoup
from io import StringIO
from .utils import HEADERS


class NasdaqReader:
    _base_url = "https://www.nasdaq.com/market-activity/stocks/{}/{}"
    def __init__(self, ticker) -> None:
        self._ticker = ticker.upper()

    def _get_earnings_data(self):
        
        data = requests.get(
            url=self._base_url.format(self.ticker, "earnings"),
            headers=HEADERS
        ).content
        soup = BeautifulSoup(data, "lxml")
        earnings_estimates_tables = soup.find_all("tbody", {"class": "earnings-forecast__table-body"})

        yearly_estimates = []
        print(earnings_estimates_tables[1].find_all("tr"))
        for row in earnings_estimates_tables[0].find_all("tr"):
            year = row.find_all("th")[0].text
            #print(year)
            #year = re.sub("[A-Z]+ ([0-9]+)", "\1", year)
            #print(year)

    @property
    def ticker(self):
        return self._ticker