import calendar
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from finance_data.utils import HEADERS, DatasetError

class MarketscreenerReader:
    _base_url = "https://www.marketscreener.com"
    
    def __init__(self, identifier) -> None:
        params = {
            "q": identifier
        }
        html = requests.get(url=f"{self._base_url}/search/", params=params, headers=HEADERS).text
        soup = BeautifulSoup(html)
        
        try:
            company_tag = soup.find("table", {"class": "table table--small table--hover table--centered table--bordered"}).find("tbody").find_all("tr")[0].find("td").find("a")
        except AttributeError:
            raise DatasetError(f"no stock found for identifier '{identifier}'")
        
        self._company_url = f"{self._base_url}{company_tag.get('href')}"
        self._header_parsed = False