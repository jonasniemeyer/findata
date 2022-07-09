import datetime as dt
import pandas as pd
import numpy as np
import requests
import re
from finance_data.utils import (
    TickerError,
    DatasetError,
    HEADERS,
    CAMEL_TO_SPACE,
    PLACEHOLDER_LOGO,
    SERVER_ERROR_MESSAGE
)

class YahooReader:
    _main_url = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{}"
    _price_url = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
    _estimates_url = "https://finance.yahoo.com/quote{}/analysis"
    _options_url = "https://query1.finance.yahoo.com/v7/finance/options/{}"
    _esg_ts_url = "https://query1.finance.yahoo.com/v1/finance/esgChart"
    
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

    def __init__(self, ticker: str = None, isin: str = None) -> None:
        if ticker:
            self._ticker = ticker.upper()
        elif isin:
            response = requests.get(
                url=f"https://markets.businessinsider.com/ajax/SearchController_Suggest?max_results=1&query={isin}",
                headers=HEADERS
            ).text
            try:
                self._ticker = re.findall(f"\|{isin}\|([A-Z0-9]+)\|", response)[0]
            except IndexError as e:
                raise ValueError("Cannot find a ticker that belongs to the given isin")
        else:
            raise ValueError("Either ticker or isin has to be specified")
        self._stored_data = self._get_stored_data()
        
        self._security_type = self._stored_data["quoteType"]["quoteType"]
        self._name = self._stored_data["quoteType"]["longName"]

    @property
    def ticker(self):
        return self._ticker
    
    @property
    def name(self):
        return self._name
    
    @property
    def security_type(self):
        return self._security_type

    @property
    def isin(self):
        if not hasattr(self, "_isin"):
            ticker_dot = self.ticker.replace('-', '.')
            response = requests.get(
                url=f"https://markets.businessinsider.com/ajax/SearchController_Suggest?max_results=1&query={ticker_dot}",
                headers=HEADERS
            ).text
            try:
                self._isin = re.findall(f"{ticker_dot}\|([A-Z0-9]+)\|{ticker_dot}", response)[0]
            except IndexError:
                self._isin = None
        return self._isin
        
    def profile(self) -> dict:        
        try:
            data = self._stored_data["assetProfile"].copy()
        except:
            data = {}
            return data
        
        for key in (
            "address1",
            "address2",
            "address3",
            "longBusinessSummary"
        ):
            if key in data.keys():
                data[key] = data[key].encode("utf-8").decode().replace("\n ", "\n")
        
        if "fullTimeEmployees" in data.keys():
            data["employees"] = data.pop("fullTimeEmployees")
        if "longBusinessSummary" in data.keys(): 
            data["description"] = data.pop("longBusinessSummary")
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

    def logo(self) -> bytes:
        response = requests.get(
            url=f"https://storage.googleapis.com/iexcloud-hl37opg/api/logos/{self.ticker.replace('-', '.')}.png",
            headers=HEADERS
        ).content
        if response == PLACEHOLDER_LOGO or response == SERVER_ERROR_MESSAGE:
            if "website" in self.profile().keys():
                response = requests.get(
                    url=f"https://logo.clearbit.com/{self.profile()['website']}",
                    headers=HEADERS
                ).content
            else:
                response = b"\n"
        return response
    
    def historical_data(
        self,
        frequency="1d",
        start=dt.date(1930, 1, 1),
        end=dt.date.today(),
        returns=True,
        timestamps=False
    ) -> dict:

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

        data = requests.get(
            url=self._price_url.format(self.ticker),
            params=parameters,
            headers=HEADERS
        )

        url = data.url
        data = data.json()
        
        meta_data = data["chart"]["result"][0]["meta"]
        currency = meta_data["currency"]
        type_ = meta_data["instrumentType"]
        utc_offset = meta_data["gmtoffset"]
        timezone = meta_data["timezone"]
        exchange_timezone = meta_data["exchangeTimezoneName"]
        
        ts = data["chart"]["result"][0]["timestamp"]
        history = data["chart"]["result"][0]["indicators"]["quote"][0]
        
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
    
    def analyst_recommendations(self, timestamps = False) -> list:
        try:
            data = self._stored_data["upgradeDowngradeHistory"]["history"]
        except:
            raise DatasetError(f"no analyst ratings found for ticker {self.ticker}")
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
    
    def recommendation_trend(self) -> dict:
        try:
            data = self._stored_data["recommendationTrend"]["trend"]
        except:
            raise DatasetError(f"no recommendation trend found for ticker {self.ticker}")
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
    ) -> dict:
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
            raise DatasetError(f"no options found for ticker {self.ticker}")
        
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
    
    def institutional_ownership(self, timestamps=False) -> list:        
        try:
            data = self._stored_data["institutionOwnership"]["ownershipList"]
        except:
            raise DatasetError(f"no institutional data found for ticker {self.ticker}")
        
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
    
    def fund_ownership(self, timestamps=False) -> list:        
        try:
            data = self._stored_data["fundOwnership"]["ownershipList"]
        except:
            raise DatasetError(f"no fund ownership data found for ticker {self.ticker}")
        
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
    
    def insider_ownership(self, timestamps=False) -> list:
        try:
            data = self._stored_data["insiderHolders"]["holders"]
        except:
            raise DatasetError(f"no insider holders found for ticker {self.ticker}")
        
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
    
    def ownership_breakdown(self) -> dict:        
        try:
            data = self._stored_data["majorHoldersBreakdown"]
        except:
            raise DatasetError(f"no ownership breakdown data found for ticker {self.ticker}")
        
        data["insider_ownership"] = round(data.pop("insidersPercentHeld"), 4)
        data["institutions_ownership"] = round(data.pop("institutionsPercentHeld"), 4)
        data["institutions_ownership_float"] = round(data.pop("institutionsFloatPercentHeld"), 4)
        data["count_institutions"] = data.pop("institutionsCount")
        
        data.pop("maxAge")
        return data
    
    def insider_trades(self, timestamps=False) -> list:        
        try:
            data  = self._stored_data["insiderTransactions"]["transactions"]
        except:
            raise DatasetError(f"no insider trades found for ticker {self.ticker}")
            
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
    
    def esg_scores(self, timestamps=False) -> dict:        
        try:
            data = self._stored_data["esgScores"]
        except:
            raise DatasetError(f"no esg scores found for ticker {self.ticker}")
        
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
    
    def sec_filings(self, timestamps=False) -> dict:        
        try:
            data = self._stored_data["secFilings"]["filings"]
        except:
            raise DatasetError(f"no sec filings found for ticker {self.ticker}")
            
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
    
    def fund_statistics(self) -> dict:        
        try:
            data = self._stored_data["fundProfile"]
        except:
            raise DatasetError(f"no fund holdings found for ticker {self.ticker}")
        
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
    
    def holdings(self) -> dict:
        try:
            data = self._stored_data["topHoldings"]
        except:
            raise DatasetError(f"no fund holdings found for ticker {self.ticker}")
            
        data = {
            "equity_share": data["stockPosition"],
            "bond_share": data["bondPosition"],
            "holdings": [
                {
                    "ticker": entry["symbol"],
                    "name": entry["holdingName"],
                    "percentage": round(entry["holdingPercent"], 4)
                }
                for entry in data["holdings"]
            ],
            "equity_data": {
                "average_price/earnings": data["equityHoldings"]["priceToEarnings"],
                "average_price/book": data["equityHoldings"]["priceToBook"],
                "average_price/sales": data["equityHoldings"]["priceToSales"],
                "average_price/cashflow": data["equityHoldings"]["priceToCashflow"]
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
        data["sector_weights"]["real_estate"] = round(data["sector_weights"].pop("realestate"), 4)

        return data
     
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
        data = self.income_statement(quarterly=quarterly, timestamps=timestamps)        
        balance_sheet_data = self.balance_sheet(quarterly=quarterly, timestamps=timestamps)
        cashflow_data = self.cashflow_statement(quarterly=quarterly, timestamps=timestamps)
        if merged:
            for key in data:
                data[key].update(balance_sheet_data[key])
                data[key].update(cashflow_data[key])
            return data
        else:
            return {
                "income_statement": data,
                "balance_sheet": balance_sheet_data,
                "cashflow_statement": cashflow_data
            }
        
    def income_statement(
        self,
        quarterly=False,
        timestamps=False
    ) -> dict:
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
    ) -> dict:
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
    ) -> dict:
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
    ) -> dict:       
        try:
            if statement_type == "income_statement":
                if quarterly:
                    raw_data = self._stored_data["incomeStatementHistoryQuarterly"]["incomeStatementHistory"]
                else:
                    raw_data = self._stored_data["incomeStatementHistory"]["incomeStatementHistory"]
            elif statement_type == "balance_sheet":
                if quarterly:
                    raw_data = self._stored_data["balanceSheetHistoryQuarterly"]["balanceSheetStatements"]
                else:
                    raw_data = self._stored_data["balanceSheetHistory"]["balanceSheetStatements"]
            elif statement_type == "cashflow_statement":
                if quarterly:
                    raw_data = self._stored_data["cashflowStatementHistoryQuarterly"]["cashflowStatements"]
                else:
                    raw_data = self._stored_data["cashflowStatementHistory"]["cashflowStatements"]
        except:
            raise DatasetError(f"no {statement_type} data found for ticker {self.ticker}")
        
        data = {}
        for entry in raw_data:
            date = (entry["endDate"]["raw"] if timestamps else entry["endDate"]["fmt"])
            points = {CAMEL_TO_SPACE.sub(" ", key).lower():(value["raw"] if "raw" in value else np.NaN) 
                      for key,value in entry.items() 
                      if key not in ("maxAge", "endDate")}
            data[date] = points
        
        return data
    
    def _get_stored_data(self) -> dict:
        
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
            raise TickerError(f"no data found for ticker {self.ticker}")
        data = data["quoteSummary"]["result"][0]

        return data