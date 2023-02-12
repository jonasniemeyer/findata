import requests
import json
from bs4 import BeautifulSoup
from finance_data.utils import HEADERS
from typing import Union

NoneType = type(None)

class StratosphereReader:
    _base_url = "https://www.stratosphere.io/company/{}/{}"
    
    def __init__(self, ticker: str) -> None:
        self._ticker = ticker
        self._profile = None
    
    def __repr__(self) -> str:
        return f"StratosphereReader({self.ticker})"
    
    @property
    def ticker(self) -> str:
        return self._ticker

    def profile(self) -> Union[dict, None]:
        if self._profile is None:
            self.income_statement()
        return self._profile
    
    def _get_data(self, suffix) -> dict:
        html = requests.get(
            url=self._base_url.format(self.ticker, suffix),
            headers=HEADERS
        ).text
        json_str = html.split('type="application/json">')[1].split("</script></body></html>")[0]
        data = json.loads(json_str)

        if self._profile is None and suffix == "":
            self._populate_profile(data)

        return data
    
    def _populate_profile(self, data) -> None:
        self._profile = {"ticker": self.ticker}
        profile_data = data["props"]["pageProps"]["company"]
        self._profile["name"] = profile_data["name"]
        self._profile["cik"] = None if profile_data["cik"] is None else int(profile_data["cik"])
        self._profile["website"] = f'https://www.{profile_data["website"]}'
        self._profile["exchange"] = profile_data["exchange"]
        self._profile["country"] = profile_data["country"]
        self._profile["currency"] = {
            "name": profile_data["currency"],
            "exchange_rate": round(1/data["props"]["pageProps"]["exchangeRate"], 4)
        }
        self._profile["market_cap"] = int(data["props"]["pageProps"]["marketCap"])
    
    def _parse_fundamental_data(self, data, timestamps=False):
        dct = {
            "annual": {},
            "quarterly": {}
        }
        for freq in ("annual", "quarterly"):
            for item in data[freq]:
                date = item["date"]
                if date == "TTM":
                    continue
                for var in item.keys():
                    if var in (
                        "date",
                        "symbol",
                        "reportedCurrency",
                        "cik",
                        "fillingDate",
                        "acceptedDate",
                        "calendarYear",
                        "period",
                        "link",
                        "finalLink"
                    ):
                        continue
                    if var not in dct[freq]:
                        dct[freq][var] = {}
                    dct[freq][var][date] = round(item[var], 6) if not isinstance(item[var], (str, NoneType)) else None
        return dct
    
    def income_statement(self, timestamps=False) -> dict:
        if not hasattr(self, "_income_data"):
            self._income_data = self._get_data("")
        data = self._parse_fundamental_data(self._income_data["props"]["pageProps"]["financials"], timestamps)
        return data
    
    def balance_sheet(self, timestamps=False) -> dict:
        if not hasattr(self, "_balance_data"):
            self._balance_data = self._get_data("balance-sheet")
        data = self._parse_fundamental_data(self._balance_data["props"]["pageProps"]["financials"], timestamps)
        return data
    
    def cashflow_statement(self, timestamps=False) -> dict:
        if not hasattr(self, "_cashflow_data"):
            self._cashflow_data = self._get_data("cash-flow-statement")
        data = self._parse_fundamental_data(self._cashflow_data["props"]["pageProps"]["financials"], timestamps)
        return data
    
    def financial_ratios(self, timestamps=False) -> dict:
        if not hasattr(self, "_ratios_data"):
            self._ratios_data = self._get_data("ratios/valuation")
        data = self._parse_fundamental_data(self._ratios_data["props"]["pageProps"]["financials"], timestamps)
        return data

    def segment_information(self, timestamps=False) -> dict:
        if not hasattr(self, "_segment_kpi_data"):
            self._segment_kpi_data = self._get_data("kpis")
        dct = self._segment_kpi_data["props"]["pageProps"]["financials"]
        variables = {item["label"] for item in dct["labels"] if not item["isSegment"]}
        data = self._parse_fundamental_data(dct["financials"], timestamps)
        data = {
            "annual": {var: values for var, values in data["annual"].items() if var in variables},
            "quarterly": {var: values for var, values in data["quarterly"].items() if var in variables}
        }
        return data

    def kpi_information(self, timestamps=False) -> dict:
        if not hasattr(self, "_segment_kpi_data"):
            self._segment_kpi_data = self._get_data("kpis")
        dct = self._segment_kpi_data["props"]["pageProps"]["financials"]
        variables = {item["label"] for item in dct["labels"] if not item["isSegment"]}
        data = self._parse_fundamental_data(dct["financials"], timestamps)
        data = {
            "annual": {var: values for var, values in data["annual"].items() if var in variables},
            "quarterly": {var: values for var, values in data["quarterly"].items() if var in variables}
        }
        return data

    def analyst_estimates(self, timestamps=False) -> dict:
        if not hasattr(self, "_estimates_data"):
            self._estimates_data = self._get_data("analysts/estimates")        
            if "data" not in self._estimates_data["props"]["pageProps"].keys():
                return {}
        data = self._parse_fundamental_data(
            self._estimates_data["props"]["pageProps"]["data"]["estimates"],
            timestamps
        )
        return data

    def prices(self, timestamps=False) -> dict:
        if not hasattr(self, "_price_target_data"):
            self._price_target_data = self._get_data("analysts/price-targets")

        if "prices" not in self._price_target_data["props"]["pageProps"].keys():
            return {}

        data = self._price_target_data["props"]["pageProps"]["prices"]
        data = {
            (int(pd.to_datetime(item["date"]).timestamp()) if timestamps else item["date"]): item["close"]
            for item in data
        }
        return data
    
    def price_targets(self, timestamps=False) -> list:
        if not hasattr(self, "_price_target_data"):
            self._price_target_data = self._get_data("analysts/price-targets")
        
        if "priceTargets" not in self._price_target_data["props"]["pageProps"].keys():
            return {}

        data = self._price_target_data["props"]["pageProps"]["priceTargets"]
        data = [
             {
                 "price_target": item["priceTarget"],
                 "date": int(pd.to_datetime(item["publishedDate"]).timestamp()) if timestamps else item["publishedDate"],
                 "analyst_company": item["analystCompany"],
                 "analyst_name": item["analystName"],
                 "news_title": item["newsTitle"],
                 "news_source": item["newsPublisher"],
                 "news_url": item["newsURL"],
                 "price_when_rated": item["priceWhenPosted"]
             }
            for item in data
        ]
        return data

    def price_target_consensus(self) -> dict:
        if not hasattr(self, "_price_target_data"):
            self._price_target_data = self._get_data("analysts/price-targets")
        
        if "priceTargetConsensus" not in self._price_target_data["props"]["pageProps"].keys():
            return {}

        data = self._price_target_data["props"]["pageProps"]["priceTargetConsensus"]
        data = {
            "average": round(data["targetConsensus"], 2),
            "median": round(data["targetMedian"], 2),
            "high": round(data["targetHigh"], 2),
            "low": round(data["targetLow"], 2)
        }
        return data

    @staticmethod
    def fund_letters(timestamps=False) -> list:
        html = requests.get(
            url="https://www.stratosphere.io/fund-letters/",
            headers=HEADERS
        ).text
        json_str = html.split('type="application/json">')[1].split("</script></body></html>")[0]
        data = json.loads(json_str)["props"]["pageProps"]["letters"]
        data = [
            {
                "title": item["title"],
                "date": (
                    int(pd.to_datetime(f'{item["date"]} {item["year"]}').timestamp()) if timestamps
                    else pd.to_datetime(f'{item["date"]} {item["year"]}').date().isoformat()
                ),
                "year": item["year"],
                "quarter": item["quarter"],
                "url": item["link"] 
            }
            for item in data
        ]
        return data