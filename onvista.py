import json
import requests
import pandas as pd
import numpy as np
from typing import Union, Optional
from .utils import HEADERS, DatasetError

class _OnvistaAbstractReader:
    """
    _OnvistaAbstractReader is the base class for OnvistaStockReader and OnvistaBondReader.
    It implements shared attributes and methods across all readers and how the historical price data is parsed, while
    the derived classes implement their own security-specific methods (e.g. OnvistaBondReader.duration and OnvistaStockReader.income_statement).

    Each OnvistaReader class is called with an identifier that automatically redirects to the onvista page. The identifier can be an ISIN, the first part of an isin
    or the security's ticker. If the identifier is not related to a security and hence the redirect fails, a DatasetError is raised instead.
    """
    def __init__(self, identifier) -> None:
        self._data = self._get_data(identifier)
        self._name = self._data["instrument"]["name"]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(Name: {self.name}, ISIN: {self.isin})"

    def _get_data(self, identifier: str) -> dict:
        if self.__class__.__name__ == "OnvistaStockReader":
            self._section = "aktien"
        elif self.__class__.__name__ == "OnvistaBondReader":
            self._section = "anleihen"
        elif self.__class__.__name__ == "OnvistaFundReader":
            self._section = "fonds"
        else:
            raise NotImplementedError()

        html = requests.get(f"https://www.onvista.de/{self._section}/{identifier}", headers=HEADERS).text
        try:
            data = json.loads(html.split('type="application/json">')[-1].split("</script>")[0])["props"]["pageProps"]["data"]["snapshot"]
        except KeyError:
            raise DatasetError(f"No Data found for identifier '{identifier}'")
        self._isin = data["instrument"]["isin"]
        return data

    @property
    def isin(self) -> str:
        return self._isin

    @property
    def name(self) -> str:
        return self._name

    def exchanges(self) -> list:
        if not hasattr(self, "_exchange_data"):
            html = requests.get(f"https://www.onvista.de/{self._section}/handelsplaetze/{self.isin}", headers=HEADERS).text
            self._exchange_data = json.loads(html.split('type="application/json">')[-1].split("</script>")[0])["props"]["pageProps"]["data"]["snapshot"]["quoteList"]["list"]
        data = [
            {
                "name": item["market"]["name"],
                "abbr": item["market"]["codeExchange"],
                "code": item["market"]["codeMarket"],
                "dataset_id": item["market"]["idNotation"],
                "country": item["market"]["isoCountry"],
                "currency": item["isoCurrency"],
                "volume": item["volume"] if "volume" in item else 0,
                "4_week_volume": item["volume4Weeks"] if "4_week_volume" in item else 0,
                "unit": item["unitType"]
            }
            for item in self._exchange_data
        ]
        return data

    def historical_data(
        self,
        dataset_id: Optional[int] = None,
        start: Union[int, str] = "1900-01-01",
        end: Union[int, str] = pd.to_datetime("today").date().isoformat()
    ) -> dict:
        if dataset_id is None:
            dataset_id = max(self.exchanges(), key=lambda x: x["4_week_volume"])["dataset_id"]
        return _OnvistaAbstractReader.get_historical_data(dataset_id, start, end)

    @staticmethod
    def get_historical_data(
        dataset_id: int,
        start: Union[int, str] = "1900-01-01",
        end: Union[int, str] = pd.to_datetime("today").date().isoformat()
    ) -> dict:
        if isinstance(start, int):
            start = pd.to_datetime(start, unit="s")
        elif isinstance(start, str):
            start = pd.to_datetime(start)

        if isinstance(end, int):
            end = pd.to_datetime(end, unit="s")
        elif isinstance(end, str):
            end = pd.to_datetime(end)

        js = requests.get(f"https://api.onvista.de/api/v1/instruments/STOCK/{dataset_id}/eod_history?idNotation={dataset_id}&range=5Y&startDate=1900-01-01", headers=HEADERS).json()
        dataset_start = pd.to_datetime(pd.to_datetime(js["datetimeStartAvailableHistory"]).date())
        dataset_end = pd.to_datetime(pd.to_datetime(js["datetimeEndAvailableHistory"]).date())

        information = {
            "instrument_id": js["idInstrument"],
            "dataset_id": js["idNotation"],
            "start": dataset_start.date().isoformat(),
            "end": dataset_end.date().isoformat(),
            "exchange": {
                "name": js["market"]["name"],
                "code": js["market"]["codeMarket"],
                "country": js["market"]["isoCountry"]
            },
            "currency": js["isoCurrency"]
        }

        if start < dataset_start:
            start = dataset_start

        end_reached = False
        subsamples = []
        while not end_reached:
            js = requests.get(f"https://api.onvista.de/api/v1/instruments/STOCK/{dataset_id}/eod_history?idNotation={dataset_id}&range=5Y&startDate={start}", headers=HEADERS).json()
            start = start + pd.offsets.DateOffset(years=5)
            if start >= end or start >= dataset_end:
                end_reached = True

            df = pd.DataFrame(index=js["datetimeLast"])
            df.index = pd.to_datetime(df.index, unit="s")
            df["open"] = js["first"]
            df["high"] = js["high"]
            df["low"] = js["low"]
            df["close"] = js["last"]
            df["simple_returns"] = df["close"].pct_change()
            df["log_returns"] = np.log(df["close"]/df["close"].shift(1))
            subsamples.append(df)
        data = pd.concat(subsamples)

        return {
            "information": information,
            "data": data
        }


class OnvistaStockReader(_OnvistaAbstractReader):
    def __init__(self, *kwargs):
        super().__init__(*kwargs)
        self._country = {
            "name": self._data["company"]["nameCountry"],
            "abbr": self._data["company"]["isoCountry"]
        }
        self._long_name = self._data["stocksDetails"]["officialName"]
        self._market_cap = {
            "market_cap": self._data["stocksFigure"]["marketCapCompany"],
            "currency": self._data["stocksFigure"]["isoCurrency"]
        }
        self._sector = {
            "sector": self._data["company"]["branch"]["name"],
            "description": self._data["company"]["branch"]["sector"]["name"]
        }
        self._shares_outstanding = self._data["stocksFigure"]["numSharesCompany"]

    @property
    def country(self) -> dict:
        return self._country

    @property
    def long_name(self) -> str:
        return self._long_name

    @property
    def market_cap(self) -> dict:
        return self._market_cap

    @property
    def sector(self) -> dict:
        return self._sector

    @property
    def shares_outstanding(self) -> int:
        return self._shares_outstanding

    def accounting_data(self) -> dict:
        data = self._data["stocksBalanceSheetList"]["list"]
        data = {
            "actual": {
                dct["idYear"]: {k: v for k,v in dct.items() if k not in ("label", "idYear")}
                for dct in data if "e" not in dct["label"]
            },
            "estimates": {
                dct["idYear"]: {k: v for k,v in dct.items() if k not in ("label", "idYear")}
                for dct in data if "e" in dct["label"]
            }
        }
        return data

    def financial_ratios(self) -> dict:
        data = self._data["stocksCnFinancialList"]["list"]
        data = {
            "actual": {
                dct["idYear"]: {k: v for k,v in dct.items() if k not in ("label", "idYear")}
                for dct in data if "e" not in dct["label"]
            },
            "estimates": {
                dct["idYear"]: {k: v for k,v in dct.items() if k not in ("label", "idYear")}
                for dct in data if "e" in dct["label"]
            }
        }
        return data

    def price_ratios(self) -> dict:
        data = self._data["stocksCnFundamentalList"]["list"]
        data = {
            "actual": {
                dct["idYear"]: {k: v for k,v in dct.items() if k not in ("label", "idYear")}
                for dct in data if "e" not in dct["label"]
            },
            "estimates": {
                dct["idYear"]: {k: v for k,v in dct.items() if k not in ("label", "idYear")}
                for dct in data if "e" in dct["label"]
            }
        }
        return data

    def splits(self) -> dict:
        data = self._data["stocksSplitList"]["list"]
        data = {
            pd.to_datetime(item["dateSplit"]).date().isoformat(): item["factor"]
            for item in data
        }
        return data


class OnvistaBondReader(_OnvistaAbstractReader):
    def __init__(self, *kwargs):
        super().__init__(*kwargs)
        if "bondsFigures" in self._data:
            bond_data = self._data["bondsFigures"]
            self._ytm = round(bond_data["yieldToMaturity"] / 100, 6)
            self._accrued_interest = round(bond_data["accruedInterest"], 4) if "accruedInterest" in bond_data else None
            self._modified_duration = round(bond_data["modifyDuration"], 4)
            self._macaulay_duration = round(bond_data["macaulayDuration"], 4)
            self._convexity = round(bond_data["convexity"], 4)
            self._interest_elasticity = round(bond_data["interestElasticity"], 4)
        else:
            self._ytm = None
            self._accrued_interest = None
            self._modified_duration = None
            self._macaulay_duration = None
            self._convexity = None
            self._interest_elasticity = None

    @property
    def accrued_interest(self) -> Optional[float]:
        return self._accrued_interest

    @property
    def convexity(self) -> Optional[float]:
        return self._convexity

    @property
    def interest_elasticity(self) -> Optional[float]:
        return self._interest_elasticity

    @property
    def macaulay_duration(self) -> Optional[float]:
        return self._macaulay_duration

    @property
    def modified_duration(self) -> Optional[float]:
        return self._modified_duration

    @property
    def ytm(self) -> Optional[float]:
        return self._ytm

    def coupon_dates(self, timestamps=False) -> list:
        data = self._data["bondsCouponList"]["list"]
        assert all(item["coupon"] == data[0]["coupon"] for item in data)
        coupons = [
            int(pd.to_datetime(item["datetimeEndCoupon"]).timestamp()) if timestamps
            else pd.to_datetime(item["datetimeEndCoupon"]).date().isoformat()
            for item in data
        ]
        return coupons

    def issuer(self) -> dict:
        data = self._data["bondsIssuer"]
        return {
            "issuer_name": data["name"],
            "country": {
                "name": data["nameCountry"],
                "abbr": data["isoCountry"]
            },
            "issuer_type": data["nameTypeIssuer"],
            "issuer_sub_type": data["nameSubTypeIssuer"]
        }

    def profile(self) -> dict:
        details = self._data["bondsDetails"]
        base_data = self._data["bondsBaseData"]
        data = {
            "bond_type": details["nameTypeBond"],
            "coupon_type": details["nameTypeCoupon"],
            "coupon": round(details["coupon"], 4) if "coupon" in details else 0,
            "nominal_value": details["nominal"],
            "maturity": pd.to_datetime(base_data["datetimeMaturity"]).date().isoformat(),
            "currency": details["isoCurrency"],
            "next_coupon_payment": pd.to_datetime(base_data["datetimeNextCoupon"]).date().isoformat() if "datetimeNextCoupon" in base_data else None,
            "emission_price": base_data["priceEmission"],
            "emission_volume": base_data["volumeEmission"],
            "emission_date": pd.to_datetime(base_data["datetimeEmission"]).date().isoformat(),
            "in_default": base_data["inDefault"],
            "perpetual": base_data["perpetual"],
            "callable": base_data["callable"]
        }
        return data


class OnvistaFundReader(_OnvistaAbstractReader):
    def __init__(self, *kwargs):
        super().__init__(*kwargs)
        self._issuer = self._data["fundsIssuer"]["name"]
        if self._data["manager"].count(",") == 1:
            first, second = self._data["manager"].split(", ")
            if len(first.split()) == 1 and len(second.split()) == 1:
                self._managers = [self._data["manager"]]
        else:
            self._managers = self._data["manager"].split(", ")

    @property
    def issuer(self) -> str:
        return self._issuer

    @property
    def managers(self) -> list:
        return self._managers

    def benchmark_indices(self) -> list:
        data = self._data["fundsBenchmarkList"]["list"]
        data = [
            {
                "name": item["instrument"]["name"],
                "url": item["instrument"]["urls"]["WEBSITE"],
                "id": item["idNotationBenchmark"]
            }
            for item in data
        ]
        return data

    def morningstar_rating(self) -> dict:
        data = self._data["fundsEvaluation"]
        data = {
            "bond_style": int(data["morningstarStyleboxBond"]) if "morningstarStyleboxBond" in data else None,
            "equity_style": int(data["morningstarStyleboxEquity"]) if "morningstarStyleboxEquity" in data else None,
            "rating": {
                "1y": int(data["morningstarRating"]),
                "3y": int(data["morningstarRating3y"]),
                "5y": int(data["morningstarRating5y"]),
                "10y": int(data["morningstarRating10y"])
            },
            "sustainability": data["morningstarSustainabilityRating"]
        }
        return data

    def profile(self) -> dict:
        data = self._data["fundsBaseData"]
        data = {
            "aum": data["volumeFund"],
            "emission_date": pd.to_datetime(data["dateEmission"]).date().isoformat(),
            "currency": data["isoCurrencyFund"],
            "custodian_bank": data["nameCustodianBank"],
            "custodian_country": {
                "name": data["nameCountry"],
                "abbr": data["isoCountry"]
            },
            "intitial_charge": round(data["maxPctInitialFee"]/100, 6),
            "ter": round(data["ongoingCharges"]/100, 6),
            "management_fee": round(data["managementFeeExPostMifid"]/100, 6),
            "custodian_fee": round(data["custodianBankFeePct"]/100, 6) if "custodianBankFeePct" in data else None
        }
        return data

    def reports(self) -> dict:
        data = self._data["fundsIssuerReports"]
        data = {
            item["nameTypeFundsReport"]: item["url"]
            for item in data
        }
        return data

    def sector_breakdown(self) -> dict:
        data = self._data["branchFundsBreakdownList"]["list"]
        data = {
            item["nameBreakdown"]: round(item["investmentPct"]/100, 6)
            for item in data
        }
        return data

    def top_holdings(self) -> list:
        data = self._data["fundsHoldingList"]["list"]
        data = [
            {
                "name": item["instrument"]["name"],
                "percentage": round(item["investmentPct"]/100, 6)
            }
            for item in data
        ]
        return data