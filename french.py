import requests
from bs4 import BeautifulSoup
from tempfile import TemporaryFile
from zipfile import ZipFile, BadZipFile
from io import StringIO
import pandas as pd
import numpy as np
import re
from finance_data.utils import HEADERS, DatasetError

class FrenchReader:
    _base_url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html"
    _dataset_url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{}_CSV.zip"
    _factor_datasets = {
        "US 3-Factors": "F-F_Research_Data_Factors",
        "US 3-Factors weekly": "F-F_Research_Data_Factors_weekly",
        "US 3-Factors daily": "F-F_Research_Data_Factors_daily",
        "US 5-Factors": "F-F_Research_Data_5_Factors_2x3",
        "US 5-Factors daily": "F-F_Research_Data_5_Factors_2x3_daily",
        "US Momentum Factor": "F-F_Momentum_Factor",
        "US Momentum Factor daily": "F-F_Momentum_Factor_daily",

        "Developed 3-Factors": 'Developed_3_Factors',
        "Developed 3-Factors daily": 'Developed_3_Factors_Daily',
        "Developed 5-Factors": 'Developed_5_Factors',
        "Developed 5-Factors daily": 'Developed_5_Factors_Daily',
        "Developed Momentum Factor": 'Developed_Mom_Factor',
        "Developed Momentum Factor daily": 'Developed_Mom_Factor_Daily',

        "Developed ex-USA 3-Factors": 'Developed_ex_US_3_Factors',
        "Developed ex-USA 3-Factors daily": 'Developed_ex_US_3_Factors_Daily',
        "Developed ex-USA 5-Factors": 'Developed_ex_US_5_Factors',
        "Developed ex-USA 5-Factors daily": 'Developed_ex_US_5_Factors_Daily',
        "Developed ex-USA Momentum Factor": 'Developed_ex_US_Mom_Factor',
        "Developed ex-USA daily": 'Developed_ex_US_Mom_Factor_Daily',

        "Europe 3-Factors": 'Europe_3_Factors',
        "Europe 3-Factors daily": 'Europe_3_Factors_Daily',
        "Europe 5-Factors": 'Europe_5_Factors',
        "Europe 5-Factors daily": 'Europe_5_Factors_Daily',
        "Europe Momentum Factor": 'Europe_Mom_Factor',
        "Europe Momentum Factor daily": 'Europe_Mom_Factor_Daily',

        "Japan 3-Factors": 'Japan_3_Factors',
        "Japan 3-Factors daily": 'Japan_3_Factors_Daily',
        "Japan 5-Factors": 'Japan_5_Factors',
        "Japan 5-Factors daily": 'Japan_5_Factors_Daily',
        "Japan Momentum Factor": 'Japan_Mom_Factor',
        "Japan Momentum Factor daily": 'Japan_Mom_Factor_Daily',

        "Asia-Pacific ex-Japan 3-Factors": 'Asia_Pacific_ex_Japan_3_Factors',
        "Asia-Pacific ex-Japan 3-Factors daily": 'Asia_Pacific_ex_Japan_3_Factors_Daily',
        "Asia-Pacific ex-Japan 5-Factors": 'Asia_Pacific_ex_Japan_5_Factors',
        "Asia-Pacific ex-Japan 5-Factors daily": 'Asia_Pacific_ex_Japan_5_Factors_Daily',

        "North America 3-Factors": 'North_America_3_Factors',
        "North America 3-Factors daily": 'North_America_3_Factors_Daily',
        "North America 5-Factors": 'North_America_5_Factors',
        "North America 5-Factors daily": 'North_America_5_Factors_Daily',
        "North America Momentum Factor": 'North_America_Mom_Factor',
        "North America Momentum Factor daily": 'North_America_Mom_Factor_Daily',

        "Emerging Markets 5-Factors": "Emerging_5_Factors",
        "Emerging Markets Momentum Factor": "Emerging_MOM_Factor"
    }
    
    def __init__(self, dataset, timestamps=False):
        if dataset in self._factor_datasets:
            self._dataset = self._factor_datasets[dataset]
        else:
            self._dataset = dataset
        self.timestamps = timestamps

    def _read_zip(self, http_response) -> str:
        with TemporaryFile() as temp_file:
            temp_file.write(http_response)
            try:
                with ZipFile(temp_file, "r") as zip_file:
                    raw_data = zip_file.open(zip_file.namelist()[0]).read().decode(encoding="cp1252")
                    return raw_data
            except BadZipFile:
                raise DatasetError(f"Could not fetch data for {self._dataset}")
          
    def read(self) -> dict:
        time_series = {}
        response = requests.get(url=self._dataset_url.format(self.dataset), headers=HEADERS).content
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
                df.index = pd.to_datetime([str(date) for date in df.index], format="%Y%m")
            elif all([len(str(date)) == 8 for date in df.index]):
                df.index = pd.to_datetime([str(date) for date in df.index], format="%Y%m%d")
            elif not all([len(str(date)) == 4 for date in df.index]):
                continue # ignore dataframes that contain dataset description
            else:
                df.index = pd.to_datetime([str(date) for date in df.index], format="%Y") #yearly data
            if "For portfolios formed in June of year t" in name:
                name = re.findall("(Value Weight Average of [^\s]+)", name)[0]
            df.columns = [col.strip() for col in df.columns]

            if self.timestamps:
                df.index = [int(date.timestamp()) for date in df.index]
            
            time_series[name] = df
        return time_series

    @property
    def dataset(self):
        return self._dataset
    
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