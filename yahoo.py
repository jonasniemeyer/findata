import datetime as dt
import pandas as pd
import numpy as np
import requests

class TickerError(ValueError):
    pass

class YahooReader:
    
    _headers = {
        "Connection": "keep-alive",
        "Expires": "-1",
        "Upgrade-Insecure-Requests": "-1",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"
        ),
    }
    
    _crumb_url = "https://query1.finance.yahoo.com/v1/test/getcrumb"
    _currencies_url = "https://query1.finance.yahoo.com/v1/finance/currencies"
    
    _history_url = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
    _summary_url = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{}"
    _options_url = "https://query1.finance.yahoo.com/v7/finance/options/{}"
    _esg_ts_url = "https://query1.finance.yahoo.com/v1/finance/esgChart"

    def __init__(self, ticker):
        self._ticker = ticker.upper()
    
    @classmethod
    def crumb(cls) -> str:
        crumb = requests.get(
            url = __class__._crumb_url,
            _eaders = __class__._headers
        ).text
        return crumb
    
    @classmethod
    def currencies(cls) -> dict:
        dct = requests.get(
            url = cls._currencies_url,
            headers = cls._headers
        ).json()
        dct = dct["currencies"]["result"]
        return dct

    @classmethod
    def possible_datasets(cls) -> str:
        datasets = """
        Not every dataset offered by yahoo is implemented as some datasets contain very little information.
        Possible further datasets are
        https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules={}
            calendarEvents
            defaultKeyStatistics
            earnings
            earningsHistory
            earningsTrend
            financialData
            indexTrend
            industryTrend
            majorDirectHolders
            netSharePurchaseActivity
            price
            quoteType
            sectorTrend
            summaryDetail
            summaryProfile
            symbol
        """
        return datasets
    
    def profile(self) -> dict:
        parameters = {
            "modules": "assetProfile"
        }
        
        dct = requests.get(
            url = self._summary_url.format(self.ticker),
            params = parameters,
            headers = self._headers
        ).json()
        
        try:
            dct = dct["quoteSummary"]["result"][0]["assetProfile"]
        except:
            raise TickerError(f"no profile found for ticker {self.ticker}")
        
        for key in (
            "address1",
            "address2",
            "longBusinessSummary"
        ):
            if key in dct.keys():
                dct[key] = dct[key].encode("latin1").decode().replace("\n ", "\n")
        
        dct["description"] = dct.pop("longBusinessSummary")
        dct["executives"] = [
            {
                "name": entry["name"],
                "age": entry["age"] if "age" in entry else None,
                "position": entry["title"],
                "born": entry["yearBorn"] if "yearBorn" in entry else None,
                "salary": entry["totalPay"]["raw"] if "totalPay" in entry else None,
                "exersized_options": entry["exercisedValue"]["raw"],
                "unexcersized_options": entry["unexercisedValue"]["raw"]
            }
            for entry in dct["companyOfficers"]
        ]
        dct.pop("companyOfficers")
        
        return dct

    def historical_data(
        self,
        frequency = '1d',
        period = None,
        start = dt.datetime(1900, 1, 1),
        end = dt.datetime.today(),
        returns = True,
        timestamps = False,
        rounded = False,
        tz_aware = True
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
        
        rounded : bool
            If True, prices are rounded to two decimal points
            default : False
        
        tz_aware : bool
            If True and frequency is set to less than a day, datetimes are timezone-aware
            default : True        
        """

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
        

        parameters = {
            "period1": start,
            "period2": end,
            "interval": frequency,
            "events": "dividends,splits",
            "includeAdjustedClose": True
        }

        response = requests.get(
            url = self._history_url.format(self.ticker),
            params = parameters,
            headers = self._headers
        )
        url = response.url
        data = response.json()
        
        meta_data = data["chart"]["result"][0]["meta"]
        currency = meta_data["currency"]
        type_ = meta_data["instrumentType"]
        utc_offset = meta_data["gmtoffset"]
        timezone = meta_data["timezone"]
        exchange_timezone = meta_data["exchangeTimezoneName"]
        tz_offset = meta_data["gmtoffset"]
        
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
                df_div = pd.DataFrame(columns = ["dividends"])
            
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
                df_splits = pd.DataFrame(columns = ["Splits"])
        
        else:
            df_div = pd.DataFrame(columns = ["dividends"])
            df_splits = pd.DataFrame(columns = ["splits"])

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
                "adj close": adj_close,
                "volume": volume
            },
            index = ts
        )
        if rounded:
            prices[["open", "high", "low", "close", "adj close"]] = prices[["open", "high", "low", "close", "adj close"]].round(2)

        if prices.index[-1] == prices.index[-2]:
            prices = prices[:-1]
        
        df = pd.concat([prices, df_div, df_splits], axis=1)

        if timestamps:
            df.index.name = "timestamps"
        else:
            if frequency in ("1d", "1wk", "1mo", "3mo"):
                df.index = [dt.datetime(1970,1,1) + dt.timedelta(seconds=ts + tz_offset) for ts in df.index]
                df.index = df.index.date
                df.index.name = "date"
            else:
                df.index = [dt.datetime(1970,1,1) + dt.timedelta(seconds=ts) for ts in df.index]
                if tz_aware:
                    df.index = df.index.tz_localize(timezone)
                df.index.name = "datetime"
        
        if frequency in ("1wk", "1mo", "3mo"):
            dividends = df["dividends"].copy()
            for i in range(len(dividends)-1):
                if not np.isnan(dividends[i]) and np.isnan(dividends[i+1]) and np.isnan(df.loc[df.index[i], "close"]):
                    df.loc[df.index[i+1], "dividends"] = df.loc[df.index[i], "dividends"]
            df = df[df["close"].notna()]
        
        if returns:
            df['simple returns'] = (df['close'] + df['dividends'].fillna(0)) / df['close'].shift(1) - 1
            df['log returns'] = np.log((df['close'] + df['dividends'].fillna(0)) / df['close'].shift(1))

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
    
    def analyst_recommendations(
        self,
        timestamps = False
    ) -> list:
        parameters = {
            "modules": "upgradeDowngradeHistory"
        }
        
        dct = requests.get(
            url = self._summary_url.format(self.ticker),
            params = parameters,
            headers = self._headers
        ).json()
        try:
            recommendations = dct["quoteSummary"]["result"][0]["upgradeDowngradeHistory"]["history"]
        except:
            raise TickerError(f"no recommendations found for ticker {self.ticker}")
        
        recommendations = [
            {
                "date": (dct["epochGradeDate"] if timestamps
                         else (dt.date(1970, 1, 1) + dt.timedelta(seconds = dct["epochGradeDate"])).isoformat()),
                "firm": dct["firm"],
                "to": dct["toGrade"],
                "from": dct["fromGrade"],
                "change": dct["action"]
            }
            for dct in recommendations
        ]
        
        return recommendations
    
    def recommendation_trend(self) -> dict:
        parameters = {
            "modules": "recommendationTrend",
            "formatted": False
        }
        
        dct = requests.get(
            url = self._summary_url.format(self.ticker),
            params = parameters,
            headers = self._headers
        ).json()
        
        try:
            data = dct["quoteSummary"]["result"][0]["recommendationTrend"]["trend"]
        except:
            raise TickerError(f"no recommendation trend found for ticker {self.ticker}")
                
        data = {
            entry["period"]: {
                "recommendations": int(entry["strongBuy"] + entry["buy"] + entry["hold"] + entry["sell"] + entry["strongSell"]),
                "average": (
                    (entry["strongBuy"] * 5 + entry["buy"] * 4 + entry["hold"] * 3 + entry["sell"] * 2 + entry["strongSell"] * 1)
                    / (entry["strongBuy"] + entry["buy"] + entry["hold"] + entry["sell"] + entry["strongSell"])
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
        date = None,
        strike_min = None,
        strike_max = None,
        straddle = False,
        timestamps = False
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
        
        straddle: bool
            If True, call and put data with the same strike price and maturity date is merged together to form a straddle
            default : False
        
        timestamps : bool
            If True, dict keys are isoformatted date strings. If False, dict keys are unix timestamps
            default: False
        """
        parameters = {
            "getAllData": True,
            "date": date,
            "strikeMin": strike_min,
            "strikeMax": strike_max,
            "straddle": straddle
        }
        options_list = requests.get(
            url = self._options_url.format(self.ticker),
            headers = self._headers,
            params = parameters
        ).json()  
        
        try:
            options_list = options_list["optionChain"]["result"][0]["options"]
        except:
            raise TickerError(f"no options found for ticker {self.ticker}")
        
        dct = {}
        for item in options_list:
            if straddle:
                if timestamps:
                    date = (dt.date(1970, 1, 1) + dt.timedelta(seconds = item["expirationDate"])).isoformat()
                else:
                    date = item["expirationDate"]
                dct[date] = {"straddles": item["straddles"]}
            else:
                dct[date] = {
                    "calls": item["calls"],
                    "puts": item["puts"]
                }
        
        return dct
    
    def institutional_holders(
        self,
        timestamps = False
    ) -> list:
        parameters = {
            "modules": "institutionOwnership",
            "formatted": False,
        }
        
        dct = requests.get(
            url = self._summary_url.format(self.ticker),
            params = parameters,
            headers = self._headers
        ).json()
        
        try:
            owners = dct["quoteSummary"]["result"][0]["institutionOwnership"]["ownershipList"]
        except:
            raise TickerError(f"no institutional data found for ticker {self.ticker}")
        
        owners = [
            {
                "date": (entry["reportDate"]["raw"] if timestamps else entry["reportDate"]["fmt"]),
                "company": entry["organization"],
                "percentage": entry["pctHeld"]["raw"],
                "shares": entry["position"]["raw"],
                "value": entry["value"]["raw"]
            }
            for entry in owners
        ]
        
        return owners
    
    def fund_ownership(
        self,
        timestamps = False
    ) -> list:
        parameters = {
            "modules": "fundOwnership",
            "formatted": False,
        }
        
        dct = requests.get(
            url = self._summary_url.format(self.ticker),
            params = parameters,
            headers = self._headers
        ).json()
        
        try:
            funds = dct["quoteSummary"]["result"][0]["fundOwnership"]["ownershipList"]
        except:
            raise TickerError(f"no fund ownership data found for ticker {self.ticker}")
        
        funds = [
            {
                "date": (entry["reportDate"]["raw"] if timestamps else entry["reportDate"]["fmt"]),
                "fund": entry["organization"],
                "percentage": entry["pctHeld"]["raw"],
                "shares": entry["position"]["raw"],
                "value": entry["value"]["raw"]
            }
            for entry in funds
        ]
        
        return funds
    
    def insider_ownership(
        self,
        timestamps = False
    ):
        parameters = {
            "modules": "insiderHolders",
            "formatted": False
        }
        
        dct = requests.get(
            url = self._summary_url.format(self.ticker),
            params = parameters,
            headers = self._headers
        ).json()
        
        try:
            owners = dct["quoteSummary"]["result"][0]["insiderHolders"]["holders"]
        except:
            raise TickerError(f"no insider holders found for ticker {self.ticker}")
        #return owners
        owners = [
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
            for entry in owners
        ]
        
        return owners
    
    def ownership_breakdown(self) -> dict:
        parameters = {
            "modules": "majorHoldersBreakdown"
        }
        
        dct = requests.get(
            url = self._summary_url.format(self.ticker),
            params = parameters,
            headers = self._headers
        ).json()
        
        try:
            data = dct["quoteSummary"]["result"][0]["majorHoldersBreakdown"]
        except:
            raise TickerError(f"no ownership breakdown data found for ticker {self.ticker}")
        
        data.pop("maxAge")
        data = {
            k:v["raw"] for k,v in data.items()
        }
        return data
    
    def insider_trades(
        self,
        timestamps = False
    ):
        parameters = {
            "modules": "insiderTransactions",
            "formatted": False
        }
        
        dct = requests.get(
            url = self._summary_url.format(self.ticker),
            params = parameters,
            headers = self._headers
        ).json()
        
        try:
            trades = dct["quoteSummary"]["result"][0]["insiderTransactions"]["transactions"]
        except:
            raise TickerError(f"no insider trades found for ticker {self.ticker}")
            
        trades = [
            {
                "date": (entry["startDate"]["raw"] if timestamps else entry["startDate"]["fmt"]),
                "name": entry["filerName"].lower().title(),
                "position": entry["filerRelation"],
                "file": entry["filerUrl"] if len(entry["filerUrl"]) != 0 else None,
                "shares": entry["shares"]["raw"],
                "value": entry["value"]["raw"] if ("value" in entry and entry["value"]["raw"] != 0) else None,
                "text": entry["transactionText"] if len(entry["transactionText"]) != 0 else None
            }
            for entry in trades
        ]
        
        return trades
    
    def esg_scores(self) -> dict:
        parameters = {
            "modules": "esgScores",
            "formatted": False
        }
        
        dct = requests.get(
            url = self._summary_url.format(self.ticker),
            params = parameters,
            headers = self._headers
        ).json()
        
        try:
            dct = dct["quoteSummary"]["result"][0]["esgScores"]
        except:
            raise TickerError(f"no esg scores found for ticker {self.ticker}")
        
        return dct
    
    def sec_filings(
        self,
        timestamps = False
    ) -> dict:
        parameters = {
            "modules": "secFilings",
            "formatted": False
        }
        
        dct = requests.get(
            url = self._summary_url.format(self.ticker),
            params = parameters,
            headers = self._headers
        ).json()
        
        try:
            data = dct["quoteSummary"]["result"][0]["secFilings"]["filings"]
        except:
            raise TickerError(f"no sec filings found for ticker {self.ticker}")
            
        data = [
            {
                "date_filed": int((dt.date.fromisoformat(entry["date"]) - dt.date(1970,1,1)).total_seconds()) if timestamps else entry["date"],
                "datetime_files": entry["epochDate"] if timestamps else (dt.datetime(1970,1,1) + dt.timedelta(seconds=entry["epochDate"])).isoformat(),
                "type": entry["type"],
                "title": entry["title"],
                "url": entry["edgarUrl"]
            }
            for entry in data
        ]
            
        return data
    
    def fund_profile(self) -> dict:
        
        parameters = {
            "modules": "fundProfile",
            "formatted": False
        }
        
        dct = requests.get(
            url = self._summary_url.format(self.ticker),
            params = parameters,
            headers = self._headers
        ).json()
        
        try:
            data = dct["quoteSummary"]["result"][0]["fundProfile"]
        except:
            raise TickerError(f"no fund holdings found for ticker {self.ticker}")
        
        data = {
            "company": data["family"],
            "style": data["categoryName"],
            "type": data["legalType"],
            "charateristics": {
                "expense_ratio" : data["feesExpensesInvestment"]["annualReportExpenseRatio"],
                "turnover": data["feesExpensesInvestment"]["annualHoldingsTurnover"],
                "aum": data["feesExpensesInvestment"]["totalNetAssets"] * 10_000
            },
            "style_url": data["styleBoxUrl"],
            "brokerages": data["brokerages"]
        }
            
        return data
    
    def fund_holdings(self) -> dict:
        parameters = {
            "modules": "topHoldings",
            "formatted": False
        }
        
        dct = requests.get(
            url = self._summary_url.format(self.ticker),
            params = parameters,
            headers = self._headers
        ).json()
        #return dct
        try:
            data = dct["quoteSummary"]["result"][0]["topHoldings"]
        except:
            raise TickerError(f"no fund holdings found for ticker {self.ticker}")
            
        data = {
            "equity_share": data["stockPosition"],
            "bond_share": data["bondPosition"],
            "holdings": [
                {
                    "ticker": entry["symbol"],
                    "name": entry["holdingName"],
                    "percent": entry["holdingPercent"]
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
                key: entry[key] for entry in data["bondRatings"] for key in entry
            },
            "sector_weights": {
                key: entry[key] for entry in data["sectorWeightings"] for key in entry
            }
        }
            
        return data
    
    def financial_statement(
        self,
        quarterly = False,
        timestamps = False,
        merged = False
    ) -> dict:
        """
        merged : bool
            If merged is True, income, balance-sheet and cashflow data for the same period is merged into the same dictionary. 
            Otherwise the statement types act as dictionary keys, each corresponding to another dictionary that contains
            the periods as keys
            default : False
        
        """
        data = self.income_statement(quarterly=quarterly, timestamps = timestamps)        
        balance_sheet_data = self.balance_sheet(quarterly=quarterly, timestamps = timestamps)
        cashflow_data = self.cashflow_statement(quarterly=quarterly, timestamps = timestamps)
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
        quarterly = False,
        timestamps = False
    ) -> dict:
        data = self._get_fundamental_data(
            statement_type = "income_statement",
            quarterly = quarterly,
            timestamps = timestamps
        )
        return data
         
    def balance_sheet(
        self,
        quarterly = False,
        timestamps = False
    ) -> dict:
        data = self._get_fundamental_data(
            statement_type = "balance_sheet",
            quarterly = quarterly,
            timestamps = timestamps
        )
        return data
    
    def cashflow_statement(
        self,
        quarterly = False,
        timestamps = False
    ) -> dict:
        data = self._get_fundamental_data(
            statement_type = "cashflow_statement",
            quarterly = quarterly,
            timestamps = timestamps
        )
        return data
    
    def _get_fundamental_data(
        self,
        statement_type,
        quarterly = False,
        timestamps = False,
    ):
        if statement_type == "income_statement":
            parameters = {
                "modules": ("incomeStatementHistoryQuarterly" if quarterly else "incomeStatementHistory"),
            }
        elif statement_type == "balance_sheet":
            parameters = {
                "modules": ("balanceSheetHistoryQuarterly" if quarterly else "balanceSheetHistory"),
            }
        elif statement_type == "cashflow_statement":
            parameters = {
                "modules": ("cashflowStatementHistoryQuarterly" if quarterly else "cashflowStatementHistory"),
            }  
        parameters["formatted"] = False
        
        dct = requests.get(
            url = self._summary_url.format(self.ticker),
            params = parameters,
            headers = self._headers
        ).json()
        
        try:
            if statement_type == "income_statement":
                if quarterly:
                    raw_data = dct["quoteSummary"]["result"][0]["incomeStatementHistoryQuarterly"]["incomeStatementHistory"]
                else:
                    raw_data = dct["quoteSummary"]["result"][0]["incomeStatementHistory"]["incomeStatementHistory"]
            elif statement_type == "balance_sheet":
                if quarterly:
                    raw_data = dct["quoteSummary"]["result"][0]["balanceSheetHistoryQuarterly"]["balanceSheetStatements"]
                else:
                    raw_data = dct["quoteSummary"]["result"][0]["balanceSheetHistory"]["balanceSheetStatements"]
            elif statement_type == "cashflow_statement":
                if quarterly:
                    raw_data = dct["quoteSummary"]["result"][0]["cashflowStatementHistoryQuarterly"]["cashflowStatements"]
                else:
                    raw_data = dct["quoteSummary"]["result"][0]["cashflowStatementHistory"]["cashflowStatements"]
        except:
            raise TickerError(f"no {statement_type} data found for ticker {self.ticker}")
        
        data = {}
        for entry in raw_data:
            date = (entry["endDate"]["raw"] if timestamps else entry["endDate"]["fmt"])
            points = {key:(value["raw"] if "raw" in value else np.NaN) 
                      for key,value in entry.items() 
                      if key not in ("maxAge", "endDate")}
            data[date] = points
        
        return data
    
    @property
    def ticker(self):
        return self._ticker

if __name__ == "__main__":
    print(dir(YahooReader))