import json
import pandas as pd
import re
import requests
from typing import Optional
from . import utils

NoneType = type(None)


class StratosphereReader:
    _base_url = "https://www.stratosphere.io/company/{}/{}"
    
    def __init__(self, ticker: str) -> None:
        self._ticker = ticker.upper()
        self._profile = None
    
    def __repr__(self) -> str:
        return f"StratosphereReader({self.ticker})"
    
    def _get_data(self, suffix) -> dict:
        html = requests.get(
            url=self._base_url.format(self.ticker, suffix),
            headers=utils.HEADERS
        ).text
        json_str = html.split('type="application/json">')[1].split("</script></body></html>")[0]
        data = json.loads(json_str)

        if self._profile is None and suffix == "":
            self._populate_profile(data)

        return data

    def _parse_fundamental_data(self, data, timestamps=False) -> dict:
        dct = {"annual": {}, "quarterly": {}}
        for freq in ("annual", "quarterly"):
            for item in data[freq]:
                date = item["date"]
                if date == "TTM":
                    continue
                if timestamps:
                    date = int(pd.to_datetime(date).timestamp())
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

    def _populate_profile(self, data) -> None:
        if "company" not in data["props"]["pageProps"]:
            return None
        self._profile = {"ticker": self.ticker}
        profile_data = data["props"]["pageProps"]["company"]
        self._profile["name"] = profile_data["name"]
        self._profile["cik"] = None if profile_data["cik"] in (None, "") else int(profile_data["cik"])
        self._profile["website"] = f'https://www.{profile_data["website"]}'
        self._profile["exchange"] = profile_data["exchange"]
        self._profile["country"] = profile_data["country"]
        self._profile["currency"] = {
            "name": profile_data["currency"],
            "exchange_rate": round(1/data["props"]["pageProps"]["exchangeRate"], 4)
        }
        self._profile["market_cap"] = int(data["props"]["pageProps"]["marketCap"])

    def _uncompress_variables(self, old: dict) -> dict:
        new = {"annual": {}, "quarterly": {}}
        for freq in ("annual", "quarterly"):
            for var in old[freq]:
                if re.findall("(\([bB]\))", var):
                    uncompressed_var = re.sub("( \([bB]\))", "", var)
                    multiplicator = 1_000_000_000
                elif re.findall("(\([mM]\))", var):
                    uncompressed_var = re.sub("( \([mM]\))", "", var)
                    multiplicator = 1_000_000
                elif re.findall("(\([tT]housands\))", var):
                    uncompressed_var = re.sub("( \([tT]housands\))", "", var)
                    multiplicator = 1_000
                else:
                    uncompressed_var = var
                    multiplicator = 1

                if uncompressed_var not in new[freq]:
                    new[freq][uncompressed_var] = {}

                for date in old[freq][var]:
                    new[freq][uncompressed_var][date] = round(old[freq][var][date]*multiplicator, 6) if not isinstance(old[freq][var][date], (str, NoneType)) else None
        return new

    def analyst_estimates(self, timestamps=False) -> Optional[dict]:
        if not hasattr(self, "_estimates_data"):
            self._estimates_data = self._get_data("analysts/estimates")

        if "data" not in self._estimates_data["props"]["pageProps"]:
            return None

        data = self._parse_fundamental_data(
            self._estimates_data["props"]["pageProps"]["data"]["estimates"],
            timestamps
        )
        return data

    def balance_sheet(self, timestamps=False) -> Optional[dict]:
        if not hasattr(self, "_balance_data"):
            self._balance_data = self._get_data("balance-sheet")

        if "financials" not in self._balance_data["props"]["pageProps"]:
            return None

        data = self._parse_fundamental_data(self._balance_data["props"]["pageProps"]["financials"], timestamps)
        return data

    def cashflow_statement(self, timestamps=False) -> Optional[dict]:
        if not hasattr(self, "_cashflow_data"):
            self._cashflow_data = self._get_data("cash-flow-statement")

        if "financials" not in self._cashflow_data["props"]["pageProps"]:
            return None

        data = self._parse_fundamental_data(self._cashflow_data["props"]["pageProps"]["financials"], timestamps)
        return data

    def financial_ratios(self, timestamps=False) -> Optional[dict]:
        if not hasattr(self, "_ratios_data"):
            self._ratios_data = self._get_data("ratios/valuation")

        if "financials" not in self._ratios_data["props"]["pageProps"]:
            return None

        data = self._parse_fundamental_data(self._ratios_data["props"]["pageProps"]["financials"], timestamps)
        return data

    def financial_statement(self, timestamps=False, merged=False) -> dict:
        income = self.income_statement(timestamps)
        balance = self.balance_sheet(timestamps)
        cashflow = self.cashflow_statement(timestamps)
        ratios = self.financial_ratios(timestamps)

        if merged:
            return {
                "annual": {**income["annual"], **balance["annual"], **cashflow["annual"], **ratios["annual"]},
                "quarterly": {**income["quarterly"], **balance["quarterly"], **cashflow["quarterly"], **ratios["quarterly"]}
            }
        else:
            return {
                "income_statement": income,
                "balance_sheet": balance,
                "cashflow_statement": cashflow,
                "financial_ratios": ratios
            }

    def income_statement(self, timestamps=False) -> Optional[dict]:
        if not hasattr(self, "_income_data"):
            self._income_data = self._get_data("")

        if "financials" not in self._income_data["props"]["pageProps"]:
            return None

        data = self._parse_fundamental_data(self._income_data["props"]["pageProps"]["financials"], timestamps)
        return data

    def kpi_information(self, timestamps=False) -> Optional[dict]:
        if not hasattr(self, "_segment_kpi_data"):
            self._segment_kpi_data = self._get_data("kpis")

        if "financials" not in self._segment_kpi_data["props"]["pageProps"]:
            return None

        dct = self._segment_kpi_data["props"]["pageProps"]["financials"]
        variables = {item["label"] for item in dct["labels"] if not item["isSegment"]}
        data = self._parse_fundamental_data(dct["financials"], timestamps)
        data = {
            "annual": {var: values for var, values in data["annual"].items() if var in variables},
            "quarterly": {var: values for var, values in data["quarterly"].items() if var in variables}
        }
        data = self._uncompress_variables(data)
        return data

    def prices(self, timestamps=False) -> Optional[dict]:
        if not hasattr(self, "_price_target_data"):
            self._price_target_data = self._get_data("analysts/price-targets")

        if "prices" not in self._price_target_data["props"]["pageProps"]:
            return None

        data = self._price_target_data["props"]["pageProps"]["prices"]
        data = {
            (int(pd.to_datetime(item["date"]).timestamp()) if timestamps else item["date"]): item["close"]
            for item in data
        }
        return data

    def price_targets(self, timestamps=False) -> Optional[list]:
        if not hasattr(self, "_price_target_data"):
            self._price_target_data = self._get_data("analysts/price-targets")

        if "priceTargets" not in self._price_target_data["props"]["pageProps"]:
            return None

        data = self._price_target_data["props"]["pageProps"]["priceTargets"]
        data = [
            {
                "price_target": round(item["priceTarget"], 2),
                "datetime": int(pd.to_datetime(item["publishedDate"]).timestamp()) if timestamps else item["publishedDate"][:-1],
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

        if "priceTargetConsensus" not in self._price_target_data["props"]["pageProps"]:
            return None

        data = self._price_target_data["props"]["pageProps"]["priceTargetConsensus"]
        data = {
            "average": round(data["targetConsensus"], 2),
            "median": round(data["targetMedian"], 2),
            "high": round(data["targetHigh"], 2),
            "low": round(data["targetLow"], 2)
        }
        return data

    def profile(self) -> Optional[dict]:
        if self._profile is None:
            self.income_statement()
        return self._profile

    def segment_information(self, timestamps=False) -> Optional[dict]:
        if not hasattr(self, "_segment_kpi_data"):
            self._segment_kpi_data = self._get_data("kpis")

        if "financials" not in self._segment_kpi_data["props"]["pageProps"]:
            return None

        dct = self._segment_kpi_data["props"]["pageProps"]["financials"]
        variables = {item["label"] for item in dct["labels"] if item["isSegment"]}
        data = self._parse_fundamental_data(dct["financials"], timestamps)
        data = {
            "annual": {var: values for var, values in data["annual"].items() if var in variables},
            "quarterly": {var: values for var, values in data["quarterly"].items() if var in variables}
        }
        data = self._uncompress_variables(data)
        return data

    @property
    def ticker(self) -> str:
        return self._ticker

    @staticmethod
    def fund_letters(timestamps=False) -> list:
        html = requests.get(
            url="https://www.stratosphere.io/fund-letters/",
            headers=utils.HEADERS
        ).text
        json_str = html.split('type="application/json">')[1].split("</script></body></html>")[0]
        data = json.loads(json_str)["props"]["pageProps"]["letters"]
        data = [
            {
                "company": item["title"],
                "date": (
                    int(pd.to_datetime(f'{item["date"]} {item["year"]}').timestamp()) if timestamps
                    else pd.to_datetime(f'{item["date"]} {item["year"]}').date().isoformat()
                ),
                "year": int(item["year"]),
                "quarter": int(item["quarter"].replace("Q", "")),
                "url": item["link"] 
            }
            for item in data
        ]
        return data

    @staticmethod
    def investors() -> list:
        html = requests.get(
            url="https://www.stratosphere.io/super-investors/",
            headers=utils.HEADERS
        ).text
        json_str = html.split('type="application/json">')[1].split("</script></body></html>")[0]
        investors = json.loads(json_str)["props"]["pageProps"]["superinvestors"]
        data = []
        for item in investors:
            portfolio = [
                {
                    "ticker": position["ticker"],
                    "cusip": position["cusip"],
                    "type": position["putCall"].title(),
                    "weight": round(position["weight"]/100, 6)
                }
                for position in item["positions"]
            ]
            statistics = {
                "market_value": item["stats"]["marketValue"] if "marketValue" in item["stats"] else None,
                "no_holdings": item["stats"]["portfolioSize"] if "portfolioSize" in item["stats"] else None,
                "purchased": item["stats"]["securitiesAdded"] if "securitiesAdded" in item["stats"] else None,
                "sold": item["stats"]["securitiesRemoved"] if "securitiesRemoved" in item["stats"] else None,
                "average_holding_period": item["stats"]["averageHoldingPeriod"] if "averageHoldingPeriod" in item["stats"] else None,
                "concentration": round(item["stats"]["concentration"]/100, 4) if "concentratione" in item["stats"] and item["stats"]["concentration"] is not None else None,
                "turnover": round(item["stats"]["turnover"], 4) if "turnover" in item["stats"] and item["stats"]["turnover"] is not None else None
            }
            data.append(
                {
                    "name": item["name"],
                    "manager": item["owner"],
                    "cik": int(item["cik"]),
                    "statistics": statistics,
                    "portfolio": portfolio,
                }
            )
        return data