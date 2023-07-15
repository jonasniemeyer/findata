from bs4 import BeautifulSoup
import datetime as dt
import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay
import requests
from . import utils


class MSCIReader:
    _base_url = "https://app2.msci.com/products/service/index/indexmaster/getLevelDataForGraph"

    def __init__(
        self,
        index_code,
        index_variant="NETR",
        index_currency="USD",
        start=dt.date(1969, 1, 1),
        end=dt.date.today()-BDay(1),
        frequency="DAILY",
        normalize=False,
        returns=True,
        timestamps=False
    ) -> None:
        """
        index_code : int or str
            specifies the MSCI index code that should be fetched
            Examples: 139245, "139249"
        
        index_variant : str
            specifies the variant of the index
            possible values: "GRTR" (accumulated), "NETR" (accumulated with taxes incorporated), "STRD" (raw index, not considering dividends)
            default : "NETR"
        
        index_currency : str
            sets the currency of the time-series
            Examples: "USD", "EUR", "LOCAL"
            default : "USD"
            Note: possible currency values depend on the index since index data is not available for all currencies

        start : int, str, datetime.date
            If the start argument is passed as an integer, the format has to be YYYYmmdd. 
            For strings, the format has to be "YYYYmmdd" or "YYYY-mm-dd" (ISO format)
            Examples: "20121120", "2012-11-20", 20121120, dt.date(2012, 11, 20)
            default : dt.date(1969, 1, 1)
        
        end : int, str, datetime.date
            If the end argument is passed as an integer, the format has to be YYYYmmdd.
            For strings, the format has to be "YYYYmmdd" or "YYYY-mm-dd" (ISO format)
            Examples: "20121120", "2012-11-20", 20121120, dt.date(2012, 11, 20)
            default : dt.date.today()
        
        frequency : str
            determines the sampling frequency of the data
            possible values: "daily", "monthly", "DAILY", "END_OF_MONTH
            default : "DAILY"
        
        normalize : bool
            If True, index prices are normalized to a starting price of 100
            default: False

        returns : bool
            If True, the returned dataframe contains simple and log returns
            default: True
        """
        
        self.code = index_code
        self.variant = index_variant 
        self.currency = index_currency

        if isinstance(start, dt.date):
            self.start = start
        elif isinstance(start, str):
            if start.count("-") == 2:
                self.start = dt.date.fromisoformat(start)
            else:
                self.start = dt.date(int(start[:4]), int(start[4:6]), int(start[6:]))
        elif isinstance(start, int):
            start = str(start)
            self.start = dt.date(int(start[:4]), int(start[4:6]), int(start[6:]))
        
        if isinstance(end, dt.date):
            self.end = end
        elif isinstance(end, str):
            if end.count("-") == 2:
                self.end = dt.date.fromisoformat(end)
            else:
                self.end = dt.date(int(end[:4]), int(end[4:6]), int(end[6:]))
        elif isinstance(end, int):
            end = str(end)
            self.end = dt.date(int(end[:4]), int(end[4:6]), int(end[6:]))
        
        if frequency in ("monthly", "MONTHLY", "END_OF_MONTH"):
            self.frequency = "END_OF_MONTH"
        elif frequency in ("daily", "DAILY"):
            self.frequency = "DAILY"
        else:
            raise ValueError('frequency parameter has to be one of ("monthly", "MONTHLY", "END_OF_MONTH", "daily", "DAILY")')
        
        self.normalize = normalize
        self.returns = returns
        self.timestamps = timestamps

    def historical_data(self) -> dict:
        start = int(f"{self.start.year}{self.start.month:02}{self.start.day:02}")
        if start < 19690101:
            print("Warning: start value cannot be earlier than 1969-01-01, thus it is set to 1969-01-01")
            start = 19690101

        end = int(f"{self.end.year}{self.end.month:02}{self.end.day:02}")

        parameters = {
            "currency_symbol": self.currency,
            "index_variant": self.variant,
            "start_date": start,
            "end_date": end,
            "data_frequency": self.frequency,
            "index_codes": self.code,
            "normalize": self.normalize
        }

        response = requests.get(
            url=self._base_url,
            params=parameters,
            headers=utils.HEADERS
        )

        url = response.url
        dct = response.json()

        if "error_code" in dct.keys():
            raise ValueError(f"""Could not retrieve data, error message: "{dct["error_message"]}"!""")

        df = pd.DataFrame(dct["indexes"]["INDEX_LEVELS"])
        df.set_index("calc_date", drop=True, inplace=True)
        df.index = pd.to_datetime(df.index, format=("%Y%m%d"))
        if self.timestamps:
            df.index = [int(date.timestamp()) for date in df.index]
        df.index.name = "date"
        df.columns = ["prices"]

        if self.normalize:
            df = df / 10
        
        if self.returns:
            df["simple_returns"] = df["prices"].pct_change()
            df["log_returns"] = np.log(df["prices"] / df["prices"].shift(1))

        return {
            "data": df,
            "information": {
                "index_code": int(dct["msci_index_code"]),
                "index_variant": dct["index_variant_type"],
                "currency": dct["ISO_currency_symbol"],
                "url": url
            }
        }

    @classmethod
    def indices(cls) -> pd.DataFrame:
        html = requests.get(
            url="https://www.msci.com/ticker-codes",
            headers=utils.HEADERS
        ).content

        soup = BeautifulSoup(html, "lxml")

        paragraph = [paragraph for paragraph in soup.find_all("p") if "Tickers for MSCI Indexes as of " in paragraph][0]
        href = f"https://www.msci.com/{paragraph.find('a').get('href')}"

        data = pd.read_excel(href, engine="openpyxl")

        data = data[data["Index Code"].notna()]
        data = data[["Index Code", "Index Name", "Variant", "Currency", "Vendor", "Ticker Type", "Ticker Code"]]
        data.columns = ["code", "name", "variant", "currency", "vendor", "type", "ticker_code"]
        data["code"] = data["code"].astype("int64")

        return data