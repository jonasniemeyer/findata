import calendar
import datetime as dt
import pandas as pd
import numpy as np
import requests
import re
import time
from bs4 import BeautifulSoup
from html import unescape
from finance_data.utils import (
    TickerError,
    HEADERS,
    PLACEHOLDER_LOGO,
    SERVER_ERROR_MESSAGE
)
from typing import Optional

class YahooReader:
    _main_url = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{}"
    _price_url = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
    _estimates_url = "https://finance.yahoo.com/quote{}/analysis"
    _options_url = "https://query1.finance.yahoo.com/v7/finance/options/{}"
    _esg_ts_url = "https://query1.finance.yahoo.com/v1/finance/esgChart"
    _quote_url = "https://finance.yahoo.com/quote/"

    def __init__(
        self,
        ticker=None,
        other_identifier=None
    ) -> None:
        if ticker:
            self._ticker = ticker.upper()
        elif other_identifier:
            self._ticker = YahooReader.get_ticker(other_identifier)
        else:
            raise ValueError("YahooReader has to be called with ticker or other_identifier")

    def __repr__(self) -> str:
        return f"YahooReader({self.ticker}|{self.name}|{self.security_type})"

    @property
    def ticker(self) -> str:
        return self._ticker
    
    @property
    def name(self) -> str:
        if not hasattr(self, "_raw_data"):
            self._raw_data = self._request_data()
        name = self._raw_data["quoteType"]["longName"]
        if name is None:
            name =  self._raw_data["quoteType"]["shortName"]
        if name is not None:
            name = unescape(name)
        return name
    
    @property
    def security_type(self) -> str:
        if not hasattr(self, "_raw_data"):
            self._raw_data = self._request_data()
        return self._raw_data["quoteType"]["quoteType"]
    
    def profile(self) -> Optional[dict]:
        if not hasattr(self, "_raw_data"):
            self._raw_data = self._request_data()

        try:
            data = self._raw_data["assetProfile"].copy()
        except:
            return None
        
        if "phone" not in data.keys() or data["phone"] == "N/A":
            data["phone"] = None

        for key in (
            "address1",
            "address2",
            "address3",
            "longBusinessSummary"
        ):
            if key in data.keys():
                try:
                    data[key] = data[key].encode("latin-1").decode("cp1252").replace("\n ", "\n")
                except:
                    pass
            else:
                data[key] = None
        
        if "fullTimeEmployees" in data.keys():
            data["employees"] = data.pop("fullTimeEmployees")
        if "longBusinessSummary" in data.keys():
            data["description"] = data.pop("longBusinessSummary")
            if data["description"] is not None:
                data["description"] = unescape(data["description"])
        if "website" in data.keys():
            data["website"] = data["website"].replace("http:", "https:")
        data["executives"] = [
            {
                "name": entry["name"],
                "age": entry["age"] if "age" in entry else None,
                "position": entry["title"],
                "born": entry["yearBorn"] if "yearBorn" in entry else None,
                "salary": entry["totalPay"]["raw"] if "totalPay" in entry else None,
                "exercised_options": entry["exercisedValue"]["raw"],
                "unexercised_options": entry["unexercisedValue"]["raw"]
            }
            for entry in data["companyOfficers"]
        ]
        if data["executives"] == []:
            data.pop("executives")
        for key in (
            "companyOfficers",
            "auditRisk",
            "boardRisk",
            "compensationRisk",
            "shareHolderRightsRisk",
            "overallRisk",
            "governanceEpochDate",
            "compensationAsOfEpochDate",
            "maxAge",
            "startDate"
        ):
            if key in data.keys():
                data.pop(key)
        return data

    def logo(self) -> Optional[bytes]:
        response = requests.get(
            url=f"https://storage.googleapis.com/iexcloud-hl37opg/api/logos/{self.ticker.replace('-', '.')}.png",
            headers=HEADERS
        ).content
        if response != PLACEHOLDER_LOGO and response != SERVER_ERROR_MESSAGE:
            if response == b"\n":
                return None
            return response

        if self.profile() is not None and "website" in self.profile().keys():
            response = requests.get(
                url=f"https://logo.clearbit.com/{self.profile()['website']}",
                headers=HEADERS
            ).content
            if response == b"\n":
                return None
            return response

        return None
    
    def historical_data(
        self,
        frequency="1d",
        start=dt.date(1930, 1, 1),
        end=dt.date.today(),
        returns=True,
        timestamps=False
    ) -> Optional[dict]:
        """
        frequency : str
            1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
            default: 1d

        period : str
            1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max, ytd
            default: None
        
        start : str, integer, datetime.date or datetime.datetime object
            str input has to be in ISO-format: YYYY-mm-dd
            default: dt.date(1970, 1, 1)

        end : str, integer, datetime.date or datetime.datetime object
            str input has to be in ISO-format: YYYY-mm-dd
            default: datetime.date.today()
        
        returns : bool
            If True, computes simple and log returns of the adjusted closing price series
            default: True

        timestamps : bool
            If True, df.index has timestamps. If False, df.index has tz-aware datetime objects
            default: False    
        """
        
        if self.security_type == "OPTION":
            print("Warning: option price data is bugged and hence is not implemented!")
            return

        if frequency not in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"):
            raise ValueError('frequency has to be one of ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo")')

        if (start == dt.date(1930, 1, 1)) and (end == dt.date.today()):
            if frequency == "1m":
                start = dt.date.today() - dt.timedelta(days=6)
            elif frequency in ("2m", "5m", "15m", "30m", "90m"):
                start = dt.date.today() - dt.timedelta(days=59)
            elif frequency in ("60m", "1h"):
                start = dt.date.today() - dt.timedelta(days=729)

        if isinstance(start, str):
            start = int((dt.date.fromisoformat(start) - dt.date(1970, 1, 1)).total_seconds())
        elif isinstance(start, dt.datetime):
            start = int((start - dt.datetime(1970, 1, 1)).total_seconds())
        elif isinstance(start, dt.date):
            start = int((start - dt.date(1970, 1, 1)).total_seconds())
        
        if isinstance(end, str):
            end = int((dt.date.fromisoformat(end) - dt.date(1970, 1, 1)).total_seconds())
        elif isinstance(end, dt.datetime):
            end = int((end - dt.datetime(1970, 1, 1)).total_seconds())
        elif isinstance(end, dt.date):
            end = int((end - dt.date(1970, 1, 1)).total_seconds())
        
        if frequency == "1m":
            if ((dt.date.today() - dt.date(1970, 1, 1)).total_seconds() - start) > 60*60*24*30:
                raise ValueError("1-minute data is only available for the last 30 days")
            elif (end - start) > 60*60*24*7:
                raise ValueError("1-minute data can only be fetched for 7 days per request")
        elif frequency in ("2m", "5m", "15m", "30m", "90m"):
            if ((dt.date.today() - dt.date(1970, 1, 1)).total_seconds() - start) > 60*60*24*60:
                raise ValueError("2-, 5-, 15-, 30- and 90-minute data is only available for the last 60 days")
        elif frequency in ("60m", "1h"):
            if ((dt.date.today() - dt.date(1970, 1, 1)).total_seconds() - start) > 60*60*24*730:
                raise ValueError("60-minute data is only available for the last 730 days")
        elif (end - start) > 60*60*24*365*100:
            raise ValueError("daily and monthly data can only be fetched for 100 years per request")

        parameters = {
            "period1": start,
            "period2": end,
            "interval": frequency,
            "events": "dividends,splits",
            "includeAdjustedClose": True
        }

        reponse = requests.get(
            url=self._price_url.format(self.ticker),
            params=parameters,
            headers=HEADERS
        )

        url = reponse.url
        data = reponse.json()
        
        try:
            meta_data = data["chart"]["result"][0]["meta"]
            currency = meta_data["currency"]
            type_ = meta_data["instrumentType"]
            utc_offset = meta_data["gmtoffset"]
            timezone = meta_data["timezone"]
            exchange_timezone = meta_data["exchangeTimezoneName"]
            ts = data["chart"]["result"][0]["timestamp"]
            history = data["chart"]["result"][0]["indicators"]["quote"][0]
        except (KeyError, TypeError):
            return None
        
        # dividend and split data
        if "events" in data["chart"]["result"][0]:
            events = data["chart"]["result"][0]["events"]

            # dividends
            if "dividends" in events:
                dividends = events["dividends"]
                dividends = [(div["date"], div["amount"]) for div in dividends.values()]
                dividends = list(zip(*dividends))

                df_div = pd.DataFrame(
                    data = dividends[1],
                    columns = ["dividends"],
                    index = dividends[0]
                )
            else:
                df_div = pd.DataFrame(columns=["dividends"], dtype="float64")
            
            # splits
            if "splits" in events:
                splits = events["splits"]
                splits = [(split["date"], split["numerator"]/split["denominator"]) for split in splits.values()]
                splits = list(zip(*splits))

                df_splits = pd.DataFrame(
                    data = splits[1],
                    columns = ["splits"],
                    index = splits[0]
                )
            else:
                df_splits = pd.DataFrame(columns=["splits"], dtype="float64")
            
        else:
            df_div = pd.DataFrame(columns=["dividends"], dtype="float64")
            df_splits = pd.DataFrame(columns=["splits"], dtype="float64")

        # price and volume data
        open_ = history["open"]
        high = history["high"]
        low = history["low"]
        close = history["close"]
        volume = history["volume"]
        
        if "adjclose" in data["chart"]["result"][0]["indicators"]:
            adj_close = data["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"]
        else:
            adj_close = close

        prices = pd.DataFrame(
            data = {
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "adj_close": adj_close,
                "volume": volume
            },
            index = ts
        )
        
        if not timestamps:
            if frequency in ("5d", "1wk", "1mo", "3mo"):
                prices.index = pd.to_datetime([pd.to_datetime(ts+utc_offset, unit="s").date() for ts in prices.index])
                df_div.index = pd.to_datetime([pd.to_datetime(ts+utc_offset, unit="s").date() for ts in df_div.index])
                df_splits.index = pd.to_datetime([pd.to_datetime(ts+utc_offset, unit="s").date() for ts in df_splits.index])
            else:
                prices.index = pd.to_datetime(prices.index, unit="s")
                df_div.index = pd.to_datetime(df_div.index, unit="s")
                df_splits.index = pd.to_datetime(df_splits.index, unit="s")

        if len(prices.index) < 2:
            return None
        if prices.index[-1] == prices.index[-2]:
            prices = prices[:-1]
        
        # merge prices with dividends
        df = pd.concat([prices, df_div], axis=1)
        df = df.sort_index()
        
        if frequency in ("5d", "1wk", "1mo", "3mo"):
            dividends = df["dividends"].copy()
            for i in range(len(dividends)-1):
                if not np.isnan(dividends.iloc[i]) and np.isnan(dividends.iloc[i+1]) and np.isnan(df.loc[df.index[i], "close"]):
                    df.loc[df.index[i+1], "dividends"] = df.loc[df.index[i], "dividends"]
            df = df[df["close"].notna()]
        
        # merge prices and dividends with splits
        df = pd.concat([df, df_splits], axis=1)
        df = df.sort_index()
        
        if frequency in ("5d", "1wk", "1mo", "3mo"):
            splits = df["splits"].copy()
            for i in range(len(splits)-1):
                if not np.isnan(splits.iloc[i]) and np.isnan(splits.iloc[i+1]) and np.isnan(df.loc[df.index[i], "close"]):
                    df.loc[df.index[i+1], "splits"] = df.loc[df.index[i], "splits"]
            df = df[df["close"].notna()]

        # round weird decimal places
        df["open"] = df["open"].round(6)
        df["high"] = df["high"].round(6)
        df["low"] = df["low"].round(6)
        df["close"] = df["close"].round(6)
        df["adj_close"] = df["adj_close"].round(6)

        if returns:
            df['simple_returns'] = (df['close'] + df['dividends'].fillna(0)) / df['close'].shift(1) - 1
            df['log_returns'] = np.log((df['close'] + df['dividends'].fillna(0)) / df['close'].shift(1))

        if timestamps:
            df.index.name = "timestamps"
        elif frequency in ("1d", "5d", "1wk", "1mo", "3mo"):
            df.index.name = "date"
        else:
            df.index.name = "datetime"
        
        df = df[:-1]
       
        return {
            "data": df,
            "information": {
                "type": type_,
                "currency": currency,
                "utc_offset": utc_offset,
                "timezone": timezone,
                "exchange_timezone": exchange_timezone,
                "url": url,
            }
        }
    
    def analyst_recommendations(self, timestamps=False) -> Optional[list]:
        if not hasattr(self, "_raw_data"):
            self._raw_data = self._request_data()

        try:
            data = self._raw_data["upgradeDowngradeHistory"]["history"]
        except:
            return None

        for dct in data:
            assert dct["action"] in ("main", "reit", "init", "up", "down")
        data = [
            {
                "date": (dct["epochGradeDate"] if timestamps else (dt.date(1970, 1, 1) + dt.timedelta(seconds=dct["epochGradeDate"])).isoformat()),
                "company": dct["firm"],
                "old": dct["toGrade"] if dct["action"] in ("main", "reit") else None if dct["action"] == "init" else dct["fromGrade"],
                "new": dct["toGrade"],
                "change": dct["action"]
            }
            for dct in data
        ]
        
        return data
    
    def recommendation_trend(self) -> Optional[dict]:
        if not hasattr(self, "_raw_data"):
            self._raw_data = self._request_data()

        try:
            data = self._raw_data["recommendationTrend"]["trend"]
        except:
            return None

        data = {
            entry["period"]: {
                "count": int(entry["strongBuy"] + entry["buy"] + entry["hold"] + entry["sell"] + entry["strongSell"]),
                "average": (
                    round(
                        (entry["strongBuy"] * 5 + entry["buy"] * 4 + entry["hold"] * 3 + entry["sell"] * 2 + entry["strongSell"] * 1)
                        / (entry["strongBuy"] + entry["buy"] + entry["hold"] + entry["sell"] + entry["strongSell"]),
                        2
                    )
                    if (entry["strongBuy"] + entry["buy"] + entry["hold"] + entry["sell"] + entry["strongSell"]) != 0 else None
                ),
                "strong_buy": entry["strongBuy"],
                "buy": entry["buy"],
                "hold": entry["hold"],
                "sell": entry["sell"],
                "strong_sell": entry["strongSell"]
            }
            for entry in data
        }
        
        data["today"] = data.pop("0m")
        data["-1month"] = data.pop("-1m")
        data["-2months"] = data.pop("-2m")
        data["-3months"] = data.pop("-3m")

        return data
    
    def options(
        self,
        date=None,
        strike_min=None,
        strike_max=None,
        timestamps=False
    ) -> Optional[dict]:
        """
        date : int
            If date is set to an integer, only options with that specific maturity date are returned
            default : None
        
        strike_min: int or float
            Sets the minimum strike price so that only option data with strike prices above the minimum strike are returned
            default : None
        
        strike_max: int or float
            Sets the maximum strike price so that only option data with strike prices below the maximum strike are returned
            default : None
        
        timestamps : bool
            If True, dict keys are isoformatted date strings. If False, dict keys are unix timestamps
            default: False
        """

        parameters = {
            "getAllData": True,
            "date": date,
            "strikeMin": strike_min,
            "strikeMax": strike_max
        }

        options_list = requests.get(
            url=self._options_url.format(self.ticker),
            headers=HEADERS,
            params=parameters
        ).json()
        
        try:
            options_list = options_list["optionChain"]["result"][0]["options"]
        except:
            return None
        
        options = {"calls": [], "puts": []}
        for dct in options_list:
            if timestamps:
                date = dct["expirationDate"]
            else:
                date = (dt.date(1970, 1, 1) + dt.timedelta(seconds=dct["expirationDate"])).isoformat()###

            for call in dct["calls"]:
                data = {}
                data["maturity"] = date
                data["strike"] = call["strike"]
                data["symbol"] = call["contractSymbol"]
                data["last_price"] = call["lastPrice"]
                if "bid" in call.keys():
                    data["bid"] = call["bid"]
                else:
                    data["bid"] = None
                if "ask" in call.keys():
                    data["ask"] = call["ask"]
                else:
                    data["ask"] = None
                if "volume" in call.keys():
                    data["volume"] = call["volume"]
                else:
                    data["volume"] = None
                data["implied_volatility"] = round(call["impliedVolatility"], 4)
                data["itm"] = call["inTheMoney"]
            
                options["calls"].append(data)
            
            for put in dct["puts"]:
                data = {}
                data["maturity"] = date
                data["strike"] = put["strike"]
                data["symbol"] = put["contractSymbol"]
                data["last_price"] = put["lastPrice"]
                if "bid" in put.keys():
                    data["bid"] = put["bid"]
                else:
                    data["bid"] = None
                if "ask" in put.keys():
                    data["ask"] = put["ask"]
                else:
                    data["ask"] = None
                if "volume" in put.keys():
                    data["volume"] = put["volume"]
                else:
                    data["volume"] = None
                data["implied_volatility"] = round(put["impliedVolatility"], 4)
                data["itm"] = put["inTheMoney"]
            
                options["puts"].append(data)
        
        return options
    
    def institutional_ownership(self, timestamps=False) -> Optional[list]:
        if not hasattr(self, "_raw_data"):
            self._raw_data = self._request_data()

        try:
            data = self._raw_data["institutionOwnership"]["ownershipList"]
        except:
            return None
        
        data = [
            {
                "date": (entry["reportDate"]["raw"] if timestamps else dt.date.fromtimestamp(entry["reportDate"]["raw"]).isoformat()),
                "company": entry["organization"],
                "percentage": np.round(entry["pctHeld"]["raw"], 4),
                "shares": entry["position"]["raw"],
                "value": entry["value"]["raw"]
            }
            for entry in data
        ]

        return data
    
    def fund_ownership(self, timestamps=False) -> Optional[list]:
        if not hasattr(self, "_raw_data"):
            self._raw_data = self._request_data()

        try:
            data = self._raw_data["fundOwnership"]["ownershipList"]
        except:
            return None
        
        data = [
            {
                "date": (entry["reportDate"]["raw"] if timestamps else entry["reportDate"]["fmt"]),
                "fund": entry["organization"],
                "percentage": round(entry["pctHeld"]["raw"], 4),
                "shares": entry["position"]["raw"],
                "value": entry["value"]["raw"]
            }
            for entry in data
        ]

        return data
    
    def insider_ownership(self, timestamps=False) -> Optional[list]:
        if not hasattr(self, "_raw_data"):
            self._raw_data = self._request_data()

        try:
            data = self._raw_data["insiderHolders"]["holders"]
        except:
            return None
        
        data = [
            {
                "date": ((entry["positionDirectDate"]["raw"] if timestamps else entry["positionDirectDate"]["fmt"])
                        if "positionDirectDate" in entry else None),
                "name": entry["name"].lower().title(),
                "position": entry["relation"],
                "shares": entry["positionDirect"]["raw"] if "positionDirect" in entry else None,
                "file": entry["url"] if len(entry["url"]) != 0 else None,
                "latest_trade": (
                    (entry["latestTransDate"]["raw"] if timestamps else entry["latestTransDate"]["fmt"]),
                    entry["transactionDescription"]
                )
            }
            for entry in data
        ]

        return data
    
    def ownership_breakdown(self) -> Optional[dict]:
        if not hasattr(self, "_raw_data"):
            self._raw_data = self._request_data()

        try:
            data = self._raw_data["majorHoldersBreakdown"]
        except:
            return None
        
        data["insider_ownership"] = round(data.pop("insidersPercentHeld"), 4)
        data["institutions_ownership"] = round(data.pop("institutionsPercentHeld"), 4)
        data["institutions_ownership_float"] = round(data.pop("institutionsFloatPercentHeld"), 4)
        data["count_institutions"] = data.pop("institutionsCount")
        
        data.pop("maxAge")
        return data
    
    def insider_trades(self, timestamps=False) -> Optional[list]:
        if not hasattr(self, "_raw_data"):
            self._raw_data = self._request_data()

        try:
            data  = self._raw_data["insiderTransactions"]["transactions"]
        except:
            return None
            
        data = [
            {
                "date": (entry["startDate"]["raw"] if timestamps else entry["startDate"]["fmt"]),
                "name": entry["filerName"].lower().title(),
                "position": entry["filerRelation"],
                "file": entry["filerUrl"] if len(entry["filerUrl"]) != 0 else None,
                "shares": entry["shares"]["raw"],
                "value": entry["value"]["raw"] if ("value" in entry and entry["value"]["raw"] != 0) else None,
                "text": entry["transactionText"] if len(entry["transactionText"]) != 0 else None
            }
            for entry in data
        ]

        return data
    
    def esg_scores(self, timestamps=False) -> Optional[dict]:
        if not hasattr(self, "_raw_data"):
            self._raw_data = self._request_data()

        try:
            data = self._raw_data["esgScores"]
        except:
            return None
        
        scores = {
            "date": (
                int(pd.to_datetime(pd.to_datetime(f"{data['ratingYear']}-{data['ratingMonth']}-01").date()).timestamp()) if timestamps
                else pd.to_datetime(f"{data['ratingYear']}-{data['ratingMonth']}-01").date().isoformat()
            ),
            "scores" : {
                "environment": data["environmentScore"],
                "social": data["socialScore"],
                "governance": data["governanceScore"],
            },
            "involvements": {}
        }

        for new_key, old_key in {
            "adult": "adult",
            "alcoholic": "alcoholic",
            "animal_testing": "animalTesting",
            "catholic": "catholic",
            "controversial_weapons": "controversialWeapons",
            "small_arms": "smallArms",
            "fur_and_leather": "furLeather",
            "gambling": "gambling",
            "gmo": "gmo",
            "military_contract": "militaryContract",
            "nuclear": "nuclear",
            "pesticides": "pesticides",
            "palm_oil": "palmOil",
            "coal": "coal",
            "tobacco": "tobacco",
        }.items():
            if old_key in data.keys():
                scores["involvements"][new_key] = data[old_key]

        return scores
    
    def sec_filings(self, timestamps=False) -> Optional[list]:
        if not hasattr(self, "_raw_data"):
            self._raw_data = self._request_data()

        try:
            data = self._raw_data["secFilings"]["filings"]
        except:
            return None
            
        data = [
            {
                "date_filed": int((dt.date.fromisoformat(entry["date"]) - dt.date(1970, 1, 1)).total_seconds()) if timestamps else entry["date"],
                "datetime_filed": entry["epochDate"] if timestamps else (dt.datetime(1970, 1, 1) + dt.timedelta(seconds=entry["epochDate"])).isoformat(),
                "form_type": entry["type"],
                "description": entry["title"],
                "url": entry["edgarUrl"]
            }
            for entry in data
        ]

        return data
    
    def fund_statistics(self) -> Optional[dict]:
        if not hasattr(self, "_raw_data"):
            self._raw_data = self._request_data()

        try:
            data = self._raw_data["fundProfile"]
        except:
            return None
        
        scores = {
            "company": data["family"],
            "type": data["legalType"],
            "style": data["categoryName"],
            "style_url": data["styleBoxUrl"]
        }
        try:
            scores["expense_ratio"] = round(data["feesExpensesInvestment"]["annualReportExpenseRatio"], 4)
        except KeyError:
            pass
        try:
            scores["turnover"] = round(data["feesExpensesInvestment"]["annualHoldingsTurnover"], 4)
        except KeyError:
            pass
        try:
            scores["aum"] = round(data["feesExpensesInvestment"]["totalNetAssets"] * 10_000, 2)
        except KeyError:
            pass

        return scores
    
    def holdings(self) -> Optional[dict]:
        if not hasattr(self, "_raw_data"):
            self._raw_data = self._request_data()

        try:
            data = self._raw_data["topHoldings"]
        except:
            return None
            
        data = {
            "equity_share": round(data["stockPosition"], 4),
            "bond_share": round(data["bondPosition"], 4),
            "holdings": [
                {
                    "ticker": entry["symbol"],
                    "name": entry["holdingName"],
                    "percentage": round(entry["holdingPercent"], 4)
                }
                for entry in data["holdings"]
            ],
            "equity_data": {
                "average_price_to_earnings": (
                    round(1/data["equityHoldings"]["priceToEarnings"], 2) if data["equityHoldings"]["priceToEarnings"] != 0
                    else None
                ),
                "average_price_to_book": (
                    round(1/data["equityHoldings"]["priceToBook"], 2) if data["equityHoldings"]["priceToBook"] != 0
                    else None
                ),
                "average_price_to_sales": (
                    round(1/data["equityHoldings"]["priceToSales"], 2) if data["equityHoldings"]["priceToSales"] != 0
                    else None
                ),
                "average_price_to_cashflow": (
                    round(1/data["equityHoldings"]["priceToCashflow"], 2) if data["equityHoldings"]["priceToCashflow"] != 0
                    else None
                )
            },
            "bond_data": {
                "average_maturity": data["bondHoldings"]["maturity"] if "maturity" in data["bondHoldings"] else None,
                "average_duration": data["bondHoldings"]["duration"] if "duration" in data["bondHoldings"] else None
            },
            "bond_ratings": {
                key: round(entry[key], 2) for entry in data["bondRatings"] for key in entry
            },
            "sector_weights": {
                key: round(entry[key], 4) for entry in data["sectorWeightings"] for key in entry
            }
        }
        if "realestate" in data["sector_weights"]:
            data["sector_weights"]["real_estate"] = round(data["sector_weights"].pop("realestate"), 4)

        return data
    
    def earnings_history(self, timestamps=False) -> Optional[list]:
        last_page_reached = False
        offset = 0
        earnings = []
        
        while not last_page_reached:
            params = {
                "symbol": self.ticker,
                "offset": offset,
                "size": 100
            }
            html = requests.get(
                url=f"https://finance.yahoo.com/calendar/earnings",
                params=params,
                headers=HEADERS
            ).text
            soup = BeautifulSoup(html, "lxml")
            tables = soup.find_all("table")
            try:
                assert len(tables) == 1
            except AssertionError:
                return None
            table = tables[0]

            rows = table.find("tbody").find_all("tr")
            for row in rows:
                cells = row.find_all("td")

                date = cells[2].find_all("span")[0].text
                date = pd.to_datetime(date)

                if timestamps:
                    date = int(date.timestamp())
                else:
                    date = date.date().isoformat()

                estimate = cells[3].text
                if estimate == "-":
                    estimate = None
                else:
                    estimate = float(estimate)

                actual = cells[4].text
                if actual == "-":
                    actual = None
                else:
                    actual = float(actual)

                if estimate is not None and actual is not None:
                    absolute_diff = actual - estimate
                    relative_diff = round(absolute_diff/abs(estimate), 4)
                else:
                    absolute_diff = None
                    relative_diff = None

                earnings.append(
                    {
                        "date": date,
                        "estimate": estimate,
                        "actual": actual,
                        "absolute_difference": absolute_diff,
                        "relative_difference": relative_diff
                    }
                )
            
            next_page_button_disabled = row.find_all("td")[-1].find_next("div").find_all("button")[-1].get("disabled")
            if next_page_button_disabled == "":
                last_page_reached = True
            elif next_page_button_disabled is None:
                offset += 100

        return earnings
    
    def financial_statement(
        self,
        quarterly=False,
        timestamps=False,
        merged=False
    ) -> dict:
        """
        merged : bool
            If merged is True, income, balance-sheet and cashflow data for the same period is merged into the same dictionary. 
            Otherwise the statement types act as dictionary keys, each corresponding to another dictionary that contains
            the periods as keys
            default : False
        
        """
        income = self.income_statement(quarterly=quarterly, timestamps=timestamps)
        balance = self.balance_sheet(quarterly=quarterly, timestamps=timestamps)
        cashflow = self.cashflow_statement(quarterly=quarterly, timestamps=timestamps)

        if merged:
            for key in income:
                if key in balance:
                    income[key].update(balance[key])
                if key in cashflow:
                    income[key].update(cashflow[key])
            return income
        else:
            return {
                "income_statement": income,
                "balance_sheet": balance,
                "cashflow_statement": cashflow
            }
        
    def income_statement(
        self,
        quarterly=False,
        timestamps=False
    ) -> Optional[dict]:
        data = self._get_fundamental_data(
            statement_type="income_statement",
            quarterly=quarterly,
            timestamps=timestamps
        )
        return data
    
    def balance_sheet(
        self,
        quarterly=False,
        timestamps=False
    ) -> Optional[dict]:
        data = self._get_fundamental_data(
            statement_type="balance_sheet",
            quarterly=quarterly,
            timestamps=timestamps
        )
        return data
    
    def cashflow_statement(
        self,
        quarterly=False,
        timestamps=False
    ) -> Optional[dict]:
        data = self._get_fundamental_data(
            statement_type="cashflow_statement",
            quarterly=quarterly,
            timestamps=timestamps
        )
        return data
    
    def _get_fundamental_data(
        self,
        statement_type,
        quarterly=False,
        timestamps=False,
    ) -> Optional[dict]:
        if not hasattr(self, "_raw_data"):
            self._raw_data = self._request_data()

        # parse json data
        try:
            if statement_type == "income_statement":
                suffix = "financials"
                if quarterly:
                    raw_data = self._raw_data["incomeStatementHistoryQuarterly"]["incomeStatementHistory"]
                else:
                    raw_data = self._raw_data["incomeStatementHistory"]["incomeStatementHistory"]
            elif statement_type == "balance_sheet":
                suffix = "balance-sheet"
                if quarterly:
                    raw_data = self._raw_data["balanceSheetHistoryQuarterly"]["balanceSheetStatements"]
                else:
                    raw_data = self._raw_data["balanceSheetHistory"]["balanceSheetStatements"]
            elif statement_type == "cashflow_statement":
                suffix = "cash-flow"
                if quarterly:
                    raw_data = self._raw_data["cashflowStatementHistoryQuarterly"]["cashflowStatements"]
                else:
                    raw_data = self._raw_data["cashflowStatementHistory"]["cashflowStatements"]
        except:
            return None

        json_name_conversion = {
            "income_statement": {
                "totalRevenue": "Total Revenue",
                "costOfRevenue": "Cost of Goods Sold",
                "grossProfit": "Gross Profit",
                "researchDevelopment": "Research & Development Expenses",
                "sellingGeneralAdministrative": "Selling, General & Administrative Expenses",
                "nonRecurring": "Non-Recurring Expenses",
                "otherOperatingExpenses": "Other Operating Expenses",
                "totalOperatingExpenses": "Total Operating Expenses",
                "operatingIncome": "Operating Income",
                "totalOtherIncomeExpenseNet": "Other Income/Expense, Net",
                "ebit": "EBIT",
                "interestExpense": "Interest Expenses",
                "incomeBeforeTax": "Income Before Taxes",
                "incomeTaxExpense": "Income Tax Expenses",
                "minorityInterest": "Minority Interest",
                "netIncomeFromContinuingOps": "Net Income from Continouing Operations",
                "discontinuedOperations": "Discontinued Operations",
                "extraordinaryItems": "Extraordinary Items",
                "effectOfAccountingCharges": "Accounting Charges",
                "otherItems": "Other Items",
                "netIncome": "Net Income",
                "netIncomeApplicableToCommonShares": "Net Income Applicable to Common Shares"
            },
            "balance_sheet": {
                "cash": "Cash and Cash Equivalents",
                "shortTermInvestments": "Short-Term Marketable Securities",
                "netReceivables": "Receivables",
                "inventory": "Inventories",
                "otherCurrentAssets": "Other Current Assets",
                "totalCurrentAssets": "Total Current Assets",
                "longTermInvestments": "Long-Term Marketable Securities",
                "propertyPlantEquipment": "Property, Plant & Equipment",
                "goodWill": "Goodwill",
                "intangibleAssets": "Intangible Assets",
                "otherAssets": "Other Assets",
                "totalAssets": "Total Assets",

                "accountsPayable": "Accounts Payable",
                "shortLongTermDebt": "Current Debt",
                "otherCurrentLiab": "Other Current Liabilities",
                "totalCurrentLiabilities": "Total Current Liabilities",

                "longTermDebt": "Non-Current Debt",
                "deferredLongTermAssetCharges": "Deferred Long-Term Asset Charges",
                "deferredLongTermLiab": "Deferred Long-Term Liabilities",
                "minorityInterest": "Minority Interest",
                "otherLiab": "Other Liabilities",
                "totalLiab": "Total Liabilities",

                "commonStock": "Common Stock",
                "retainedEarnings": "Retained Earnings",
                "treasuryStock": "Treasury Stock",
                "capitalSurplus":"Capital Surplus",
                "otherStockholderEquity": "Other Shareholders Equity",
                "totalStockholderEquity": "Total Shareholders Equity",
                "netTangibleAssets": "Tangible Book-Value"
            },
            "cashflow_statement": {
                "netIncome": "Net Income",
                "depreciation": "Depreciation & Amortization",
                "changeToNetincome": "Other Non-Cash Items",
                "changeToAccountReceivables": "Change in Acounts Receivable",
                "changeToLiabilities": "Change in Liabilities",
                "changeToInventory": "Change in Inventories",
                "changeToOperatingActivities": "Other Operating Activities",
                "effectOfExchangeRate": "Gains/Losses on Currency Changes",
                "totalCashFromOperatingActivities": "Total Cashflow From Operating Activities",
                "capitalExpenditures": "Capital Expenditures",
                "investments": "Change in Total Investments",
                "otherCashflowsFromInvestingActivities": "Other Investing Activities",
                "totalCashflowsFromInvestingActivities": "Total Cashflow From Investing Activities",
                "dividendsPaid": "Total Dividends Paid",
                "netBorrowings": "Total Debt Issued",
                "otherCashflowsFromFinancingActivities": "Other Financing Activities",
                "totalCashFromFinancingActivities": "Total Cashflow From Financing Activities",
                "changeInCash": "Change in Cash and Cash Equivalents",
                "repurchaseOfStock": "Repurchases of Common Stock",
                "issuanceOfStock": "Issuance of Common Stock"  
            }
        }
        
        json_data = {}
        for entry in raw_data:
            date = pd.to_datetime(entry["endDate"]["fmt"])
            last_day = calendar.monthrange(date.year, date.month)[1]
            if timestamps:
                date = int(pd.to_datetime(f"{date.year}-{date.month}-{last_day}").timestamp()) # date matching questionable
            else:
                date = f"{date.year}-{date.month:02d}-{last_day:02d}"
            
            data_points = {}
            for key, value in entry.items():
                if key not in ("maxAge", "endDate"):
                    data_points[json_name_conversion[statement_type][key]] = value["raw"] if "raw" in value else None
            
            json_data[date] = data_points
        
        if quarterly:
            data = json_data
        else:
            # parse html data
            html = requests.get(f"https://finance.yahoo.com/quote/{self.ticker}/{suffix}", headers=HEADERS).text
            soup = BeautifulSoup(html, "lxml")

            html_data = {}
            dates = {}
            header = soup.find_all("div", {"class": "D(tbr) C($primaryColor)"})
            assert len(header) == 1
            
            header = header[0].find_all("div", recursive=False)
            for index, tag in enumerate(header[1:]):
                date = tag.find("span").text.upper()
                if date != "TTM":
                    date = pd.to_datetime(date).date()
                    last_day = calendar.monthrange(date.year, date.month)[1]
                    date = pd.to_datetime(f"{date.year}-{date.month}-{last_day}")
                    if timestamps:
                        date = int(date.timestamp())
                    else:
                        date = date.date().isoformat()
                html_data[date] = {}
                dates[index] = date

            rows = soup.find_all("div", {"data-test": "fin-row"})
            for row in rows:
                row = row.find("div")
                cells = row.find_all("div", recursive=False)
                name = cells[0].find("div").find("span").text
                for index, cell in enumerate(cells[1:]):
                    value = cell.find("span")
                    if value is None:
                        value = cell.text.replace(",", "")
                    else:
                        value = value.text.replace(",", "")
                    if value == "-":
                        value = None
                    elif "." in value:
                        if "k" in value:
                            value = float(value.replace("k", "")) * 1000
                        else:
                            value = float(value)
                    else:
                        value = int(value) * 1000
                    date = dates[index]
                    html_data[date][name] = value
            
            # merge json with html data
            html_name_conversion = {
                "income_statement": {
                    "Total Revenue": "Total Revenue",
                    "Cost of Revenue": "Cost of Goods Sold",
                    "Gross Profit": "Gross Profit",
                    "Reconciled Depreciation": "Reconciled Depreciation",
                    "EBITDA": "EBITDA",
                    "EBTI": "EBIT",
                    "Operating Expense": "Total Operating Expenses",
                    "Operating Income": "Operating Income",
                    "Interest Expense": "Interest Expenses",
                    "Interest Income": "Interest Income",
                    "Pretax Income": "Income Before Taxes",
                    "Tax Provision": "Income Tax Expenses",
                    "Net Income from Continuing Operations": "Net Income from Continuing Operations",
                    "Net Income Common Stockholders": "Net Income Applicable to Common Shares",
                    "Basic EPS": "Basic EPS",
                    "Diluted EPS": "Diluted EPS",
                    "Basic Average Shares": "Basic Shares Outstanding",
                    "Diluted Average Shares": "Diluted Shares Outstanding"
                },
                "balance_sheet" : {
                    "Total Assets": "Total Assets",
                    "Total Liabilities Net Minority Interest": "Total Liabilities",
                    "Total Equity Gross Minority Interest": "Total Shareholders Equity",
                },
                "cashflow_statement": {
                    "Operating Cash Flow": "Total Cashflow From Operating Activities",
                    "Investing Cash Flow": "Total Cashflow From Investing Activities",
                    "Financing Cash Flow": "Total Cashflow From Financing Activities",
                    "End Cash Position": "Cash and Cash Equivalents End of Period",
                    "Income Tax Paid Supplemental": "Income Tax Paid",
                    "Interest Paid Supplemental Data": "Interest Paid",
                    "Capital Expenditure": "Capital Expenditures",
                    "Issuance of Capital Stock": "Issuance of Common Stock",
                    "Issuance of Debt": "Issuance of Debt",
                    "Repayment of Debt": "Repayment of Debt",
                    "Repurchase of Capital Stock": "Repurchases of Common Stock",
                    "Free Cash Flow": "Free Cashflow"
                }
            }
            for date in html_data:
                converted = {}
                for key in html_name_conversion[statement_type]:
                    if key not in html_data[date].keys():
                        converted[key] = None
                    elif key in html_name_conversion[statement_type]:
                        converted[html_name_conversion[statement_type][key]] = html_data[date][key]
                    else:
                        converted[key] = html_data[date][key]

                html_data[date] = converted
            
            if statement_type == "income_statement":
                data = self._merge_income_statements(json_data, html_data)
            elif statement_type == "balance_sheet":
                data = self._merge_balance_sheets(json_data, html_data)
            elif statement_type == "cashflow_statement":
                data = self._merge_cashflow_statements(json_data, html_data)
        
        return data
    
    def _merge_income_statements(self, json_data, html_data) -> dict:
        variables = (
            "Total Revenue",
            "Cost of Goods Sold",
            "Gross Profit",
            "Research & Development Expenses",
            "Selling, General & Development Expenses",
            "EBITDA",
            "Reconciled Depreciation",

            "Non-Recurring Expenses",
            "Other Operating Expenses",
            "Total Operating Expenses",
            "Operating Income",

            "Total Other Income Expense, Net",
            "EBIT",

            "Interest Expenses",
            "Interest Income",
            "Net Non Operating Interest Income Expense",
            "Income Before Taxes",

            "Tax Provision",
            "Minority Interest",
            "Net Income from Continouing Operations",

            "Discontinued Operations",
            "Extraordinary Items",
            "Accounting Charges",
            "Other Items",
            "Net Income",
            "Net Income applicable to Common Shares",

            "Basic EPS",
            "Diluted EPS",

            "Basic Shares Outstanding",
            "Diluted Shares Outstanding"
        )
        ordered_data = {}
        for date in html_data:
            ordered_data[date] = {}
            for var in variables:
                if date != "TTM" and var in json_data[date].keys():
                    ordered_data[date][var] = json_data[date][var]
                elif var in html_data[date].keys():
                    ordered_data[date][var] = html_data[date][var]
                else:
                    ordered_data[date][var] = None
        return ordered_data
    
    def _merge_balance_sheets(self, json_data, html_data) -> dict:
        variables = (
            "Cash and Cash Equivalents",
            "Short-Term Marketable Securities",
            "Accounts Receivable",
            "Inventories",
            "Other Current Assets",
            "Total Current Assets",

            "Long-Term Marketable Securities",
            "Property, Plant & Equipment",
            "Goodwill",
            "Intangible Assets",
            "Other Assets",
            
            "Total Assets",

            "Accounts Payable",
            "Current Debt",
            "Other Current Liabilities",
            "Total Current Liabilities",

            "Non-Current Debt",
            "Deferred Long-Term Asset Charges",
            "Deferred Long-Term Liabilities",
            "Other Liabilities",
            "Total Non-Current liabilities",
            
            "Total Liabilities",

            "Common Stock",
            "Retained Earnings",
            "Treasury Stock",
            "Other Shareholders Equity",
            "Total Shareholders Equity"
        )
        ordered_data = {}
        for date in html_data:
            ordered_data[date] = {}
            for var in variables:
                if var in html_data[date].keys():
                    ordered_data[date][var] = html_data[date][var]
                elif date != "TTM" and var in json_data[date].keys():
                    ordered_data[date][var] = json_data[date][var]
                else:
                    ordered_data[date][var] = None
        return ordered_data
    
    def _merge_cashflow_statements(self, json_data, html_data) -> dict:
        variables = (
            "Net Income",
            "Depreciation & Amortization",
            "Change in Acounts Receivable",
            "Change in Inventories",
            "Change in Liabilities",
            "Other Operating Activities",
            "Gains/Losses on Currency Changes",
            "Total Cashflow From Operating Activities",

            "Capital Expenditures",
            "Change in Total Investments",
            "Other Investing Activities",
            "Total Cashflow From Investing Activities",

            "Free Cashflow",

            "Issuance of Debt",
            "Repayment of Debt",
            "Total Debt Issued", # wrong data => Net Debt Issued
            "Issuance of Common Stock",
            "Repurchases of Common Stock", # wrong data => repurchase of capital stock
            "Total Dividends Paid",
            "Other Financing Activities",
            "Total Cashflow From Financing Activities",

            "Change in Cash and Cash Equivalents"
        )
        ordered_data = {}
        for date in html_data:
            ordered_data[date] = {}
            for var in variables:
                if var in html_data[date].keys():
                    ordered_data[date][var] = html_data[date][var]
                elif date != "TTM" and var in json_data[date].keys():
                    ordered_data[date][var] = json_data[date][var]
                else:
                    ordered_data[date][var] = None
        return ordered_data
    
    def _request_data(self) -> dict:
        parameters = {
            "modules": ",".join(
                (
                    'assetProfile',
                    'balanceSheetHistory',
                    'balanceSheetHistoryQuarterly',
                    'calendarEvents',
                    'cashflowStatementHistory',
                    'cashflowStatementHistoryQuarterly',
                    'defaultKeyStatistics',
                    'earnings',
                    'earningsHistory',
                    'earningsTrend',
                    "esgScores",
                    'financialData',
                    'fundOwnership',
                    'incomeStatementHistory',
                    'incomeStatementHistoryQuarterly',
                    'indexTrend',
                    'industryTrend',
                    'insiderHolders',
                    'insiderTransactions',
                    'institutionOwnership',
                    'majorDirectHolders',
                    'majorHoldersBreakdown',
                    'netSharePurchaseActivity',
                    'price',
                    'quoteType',
                    'recommendationTrend',
                    'secFilings',
                    'sectorTrend',
                    'summaryDetail',
                    'summaryProfile', 
                    'symbol',
                    'upgradeDowngradeHistory',
                    'fundProfile',
                    'topHoldings',
                    'fundPerformance'
                )
            ),
            "formatted": False
        }
        
        data = requests.get(
            url=self._main_url.format(self.ticker),
            params=parameters,
            headers=HEADERS
        ).json()
        
        if data["quoteSummary"]["error"] is not None:
            raise TickerError(f"no data found for ticker '{self.ticker}'")
        data = data["quoteSummary"]["result"][0]
        return data

    @classmethod
    def get_ticker(cls, identifier: str, pause: int = 60) -> Optional[dict]:
        """
        This classmethod takes an isin or other identifier and returns the corresponding Yahoo ticker if it exists.
        If there is no corresponding ticker found, None is returned instead.
        """
        params = {"yfin-usr-qry": identifier}
        response = requests.get(cls._quote_url, params=params, headers=HEADERS)
        try:
            ticker = re.findall(f"{cls._quote_url}(?P<ticker>.+)\?p=(?P=ticker)&.tsrc=fin-srch", response.url)[0].strip()
            return ticker
        except IndexError:
            # check if the http requests are rate limited or if the ticker does not exist
            limited = True
            while limited:
                try:
                    params_appl = {"yfin-usr-qry": "US0378331005"}
                    response_appl = requests.get(cls._quote_url, params=params_appl, headers=HEADERS)
                    ticker = re.findall(f"{cls._quote_url}(?P<ticker>.+)\?p=(?P=ticker)&.tsrc=fin-srch", response_appl.url)[0].strip()
                    limited = False
                except IndexError:
                    print(f"Rate limited: Pause {pause} seconds")
                    time.sleep(pause)
            try:
                ticker = re.findall(f"{cls._quote_url}(?P<ticker>.+)\?p=(?P=ticker)&.tsrc=fin-srch", response.url)[0].strip()
            except IndexError:
                ticker = None
            return ticker

    @staticmethod
    def currencies() -> list:
        data = requests.get(
            url="https://query1.finance.yahoo.com/v1/finance/currencies",
            headers=HEADERS
        ).json()

        data = data["currencies"]["result"]
        data = [
            {
                "short_name": item["shortName"],
                "long_name": item["longName"],
                "symbol": item["symbol"]
            }
            for item in data
        ]
        return data