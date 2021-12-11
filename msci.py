import requests
import datetime as dt
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from finance_data.utils import HEADERS

class MSCIReader:

    _base_url = "https://app2.msci.com/products/service/index/indexmaster/getLevelDataForGraph"

    def __init__(
        self,
        index_code,
        index_variant,
        index_currency
    ):
        """
        index_code : int, str or an array-like object of strings or integers
            sets the index code of the msci index to request data of
            Example: (214156, "353567", "463743")
        
        index_variant : str
            sets the index variant
            Note: only STRD is working at the moment
        
        index_currency : str
            sets the currency of the time-series
            Note: only USD is working at the moment        
        """
        self.code = index_code
        self.variant = index_variant
        self.currency = index_currency

    def historical_data(
        self,
        start = None,
        end = None,
        frequency = None
    ) -> dict:
        """
        start : int, str, datetime.date or datetime.datetime
            If the start argument is passed as an integer or string, the format has to be YYYYmmdd.
            Example: "20121120" or 20121120 corresponds to the date 2012-11-20 in ISO-format
        
        end : int, str, datetime.date or datetime.datetime
            If the end argument is passed as an integer or string, the format has to be YYYYmmdd.
            Example: "20121120" or 20121120 corresponds to the date 2012-11-20 in ISO-format
        
        frequency : str
            determines the sampling frequency of the data, e.g. monthly
            Note: only daily is working at the moment
        """

        if isinstance(start, (dt.date, dt.datetime)):
            start = int(f"{start.year}{start.month:02}{start.day:02}")
    
        if start < 19690101:
            print("Warning: start value cannot be earlier than 1969-01-01, hence it is set to 1969-01-01")
            start = 19690101

        if isinstance(end, (dt.date, dt.datetime)):
            end = int(f"{end.year}{end.month:02}{end.day:02}")

        parameters = {
            "currency_symbol": self.currency,
            "index_variant": self.variant,
            "start_date": start,
            "end_date": end,
            "data_frequency": frequency,
            "index_codes": self.code
        }

        response = requests.get(
            url = self._base_url,
            params = parameters,
            headers = HEADERS
        )

        url = response.url
        dct = response.json()

        if "error_code" in dct.keys():
            raise ValueError(f"""No data found, error message: "{dct["error_message"]}" """)

        df = pd.DataFrame(dct["indexes"]["INDEX_LEVELS"])
        df.set_index("calc_date", drop=True, inplace=True)
        df.index = pd.to_datetime(df.index, format=("%Y%m%d")).date
        df.index.name = "date"
        df.columns = [self.code]

        return {
            "data": df,
            "information": {
                "index_code": dct["msci_index_code"],
                "index_variant": dct["index_variant_type"],
                "currency": dct["ISO_currency_symbol"],
                "url": url
            }
        }

    @classmethod
    def indices_list(cls) -> pd.DataFrame:
        html = requests.get(
            url = "https://www.msci.com/ticker-codes",
            headers = HEADERS
        ).content

        soup = BeautifulSoup(html, "lxml")

        paragraph = [paragraph for paragraph in soup.find_all("p") if "Tickers for MSCI Indexes as of " in paragraph][0]
        href = "https://www.msci.com/" + paragraph.find("a").get("href")

        data = pd.read_excel(href, engine = "openpyxl")

        data = data[data["Index Code"].notna()]
        data = data[["Index Code", "Index Name", "Variant", "Currency", "Vendor", "Ticker Type", "Ticker Code"]]
        data.columns = ["code", "name", "variant", "currency", "vendor", "type", "ticker_code"]
        data["code"] = data["code"].astype("int32")

        return data