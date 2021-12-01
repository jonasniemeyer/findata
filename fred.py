import requests
import pandas as pd
import numpy as np
import datetime as dt
from bs4 import BeautifulSoup
from io import StringIO
from finance_data.utils import _headers

class FREDReader:
    _description_url = "https://fred.stlouisfed.org/series/{}"
    _dataset_url = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    def __init__(self, dataset) -> None:
        self._dataset = dataset
    
    def historical_data(
            self,
            timestamps = False
        ) -> pd.DataFrame:

        parameters = {
            "id": self.dataset
        }

        response = requests.get(
            url = self._dataset_url, 
            headers = _headers,
            params = parameters
        ).text

        df = pd.read_csv(StringIO(response), index_col=0)
        df.index = pd.to_datetime(df.index)
        if timestamps:
            df.index = [
                int((item - dt.datetime(1970,1,1)).total_seconds())
                for item in df.index
            ]
        df = df.replace(".", np.NaN)
        df = df.apply(pd.to_numeric)

        return df

    def name(self) -> str:
        if not hasattr(self, "_description_data"):
            self._get_description_data()
        return self._description_data["name"]

    def categories(self) -> str:
        if not hasattr(self, "_description_data"):
            self._get_description_data()
        return self._description_data["categories"]

    def description(self) -> str:
        if not hasattr(self, "_description_data"):
            self._get_description_data()
        return self._description_data["description"]

    def unit(self) -> str:
        if not hasattr(self, "_description_data"):
            self._get_description_data()
        return self._description_data["unit"]

    def _get_description_data(self) -> dict:        
        html = requests.get(
            url = self._description_url.format(self.dataset), 
            headers = _headers
        ).text

        soup = BeautifulSoup(html, "lxml")
        
        name = soup.find_all("span", {"id": "series-title-text-container"})[0].text.strip()
        category_tags = soup.find_all("a", {"class": "breadcrumb_link"})
        categories = [tag.text for tag in category_tags]
        categories.remove("Categories")
        try:
            description = soup.find_all("p", {"class": "series-notes"})[0].text.strip()
        except:
            description = None
        unit = soup.find_all("p", {"class": "col-xs-12 pull-left"})[0].text.strip("Units:").strip().replace("\xa0", " ")

        data = {
            "name": name,
            "categories": categories,
            "description": description,
            "unit": unit
        }
        self._description_data = data

        return data

    @property
    def dataset(self) -> dict:
        return self._dataset