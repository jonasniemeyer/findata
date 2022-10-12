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

    def _get_company_information(self) -> None:
        url = f"{self._company_url}/company/"
        html = requests.get(url=url, headers=HEADERS).text
        self._company_soup = BeautifulSoup(html)

    def _get_financial_information(self) -> None:
        url = f"{self._company_url}/financials/"
        html = requests.get(url=url, headers=HEADERS).text
        self._financial_soup = BeautifulSoup(html)
    
    def _parse_header(self) -> None:
        if self._header_parsed:
            return
        if hasattr(self, "_financial_soup"):
            soup = self._financial_soup
        elif hasattr(self, "_company_soup"):
            soup = self._company_soup
        else:
            self._get_financial_information()
            soup = self._financial_soup
        
        ticker, isin = soup.find("div", {"class": "bc_pos"}).find("span", {"class": "bc_add"}).find_all("span")
        self._ticker = ticker.text.strip()
        self._isin = isin.text.strip()
        
        self._name = re.findall("(.+)\(.+\)", soup.find("h1").parent.text.strip())[0].strip()
        
        price_tag = soup.find("span", {"class": "last variation--no-bg txt-bold"})
        self._price = float(price_tag.text)
        self._currency = price_tag.find_next("td").text.strip()
        
        self._header_parsed = True