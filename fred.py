import requests
import pandas as pd
import numpy as np
import datetime as dt
from bs4 import BeautifulSoup
from io import StringIO
from utils import _headers


class FREDReader:
    _description_url = "https://fred.stlouisfed.org/series/{}"
    _dataset_url = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    def __init__(self, dataset) -> None:
        self._dataset = dataset

    def historical_data(self) -> pd.DataFrame:

        parameters = {
            "id": self.dataset
        }

        response = requests.get(
            url = self._dataset_url, 
            headers = _headers,
            params = parameters
        ).content

        df = pd.read_csv(StringIO(response.decode()), index_col=0)
        df.index = pd.to_datetime(df.index)
        df = df.replace(".", np.NaN)
        df = df.apply(pd.to_numeric)

        return df

    def name(self) -> str:
        return self._description_data["name"]

    def category(self) -> str:
        return self._description_data["category"]

    def description(self) -> str:
        return self._description_data["description"]

    def unit(self) -> str:
        return self._description_data["unit"]

    def _get_description_data(self) -> dict:
        if hasattr(self, "_descritpion_data"):
            return self._description_data
        
        html = requests.get(
            url = self._description_url.format(self.dataset), 
            headers = _headers
        ).text

        soup = BeautifulSoup(html, "lxml")

        name = soup.find_all("span", {"id": "series-title-text-container"})[0].text.strip()
        category = soup.find_all("p", {"class": "col-xs-12 col-md-6 pull-left"})[0].text.strip("Release:").strip()
        try:
            description = soup.find_all("p", {"class": "series-notes"})[0].text.strip()
        except:
            description = None
        unit = soup.find_all("p", {"class": "col-xs-12 pull-left"})[0].text.strip("Units:").strip().replace("\xa0", " ")

        data = {
            "name": name,
            "category": category,
            "description": description,
            "unit": unit
        }
        self._description_data = data

        return data

    @property
    def dataset(self) -> dict:
        return self._dataset