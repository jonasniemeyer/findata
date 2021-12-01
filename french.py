import requests
from bs4 import BeautifulSoup
from tempfile import TemporaryFile
from zipfile import ZipFile
from io import StringIO
import pandas as pd
import numpy as np
import datetime as dt
import re
from finance_data.utils import HEADERS

class FrenchReader:
    _base_url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html"
    _dataset_url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{}_CSV.zip"
    def __init__(
        self,
        dataset
    ):
        self._dataset = dataset
          
    def read(self) -> dict:
        time_series = {}
        response = requests.get(url = self._dataset_url.format(self.dataset), headers = HEADERS).content
        data = self._read_zip(response)
        data = data.split("\r\n\r\n")
        for chunk in data:
            try:
                start = chunk.index(",")
            except:
                continue
            if chunk.startswith("\r\n"):
                name = chunk[:start]
            else:
                name = chunk[:start].split("\r\n")[0]
            name = re.sub("([^\s])[\s\t]{2,}([^\s])", r"\1 \2", name).strip()
            name = name.replace("-- ", "")
            name = name.replace(" from January to December", "").replace(": January-December", "")
            name = name.strip(":")
            if name == "":
                name = "Main"
            chunk = chunk[start:]
            if "Breakpoints" in self._dataset: # breakpoints datasets have no column headers
                name = "Main"
                if self._dataset == "ME_Breakpoints":
                    chunk = "Count,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100\r\n" + chunk
                elif self._dataset == "Prior_2-12_Breakpoints":
                    chunk = "no_stocks,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100\r\n" + chunk
                elif self._dataset in ("OP_Breakpoints", "INV_Breakpoints"):
                    chunk = "Count,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100\r\n" + chunk.strip(",Count")
                else:
                    chunk = re.sub("<=0,>0\r\n", "<=0,>0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100\r\n", chunk)
            try:
                df = pd.read_csv(StringIO(chunk), index_col=0)
                df = df[df.index.notna()]
                df.index = [int(number) for number in df.index]
            except:
                continue
            df = df.replace([-99.99, -999], np.NaN)
            if len(df.index) == 0:
                continue # ignore empty dataframes
            elif all([len(str(date)) == 6 for date in df.index]):
                df.index = [
                    dt.datetime.strptime(str(date), "%Y%m")
                    for date in df.index
                ]
            elif all([len(str(date)) == 8 for date in df.index]):
                df.index = [
                    dt.datetime.strptime(str(date), "%Y%m%d")
                    for date in df.index
                ]
            elif not all([len(str(date)) == 4 for date in df.index]):
                continue # ignore dataframes that contain dataset description
            if "For portfolios formed in June of year t" in name:
                name = re.findall("(Value Weight Average of [^\s]+)", name)[0]
            df.columns = [col.strip() for col in df.columns]
            time_series[name] = df
        return time_series
        
    def _read_zip(self, http_response) -> str:
        with TemporaryFile() as temp_file:
            temp_file.write(http_response)
            with ZipFile(temp_file, "r") as zip_file:
                raw_data = zip_file.open(zip_file.namelist()[0]).read().decode(encoding = "cp1252")
                return raw_data
    
    @classmethod
    def datasets(cls) -> list:
        response = requests.get(cls._base_url).content
        soup = BeautifulSoup(response, "lxml")
        datasets = [a_tag.get("href") for a_tag in soup.find_all("a")]
        datasets = [
            dataset.replace("ftp/", "").replace("_CSV.zip", "") for dataset in datasets
            if dataset is not None and dataset.endswith("_CSV.zip")
        ]
        return datasets
    
    @property
    def dataset(self):
        return self._dataset