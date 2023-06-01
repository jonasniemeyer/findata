import json
import requests
import pandas as pd
import numpy as np
from typing import Union, Optional
from finance_data.utils import HEADERS

class _OnvistaAbstractReader:
    """
    _OnvistaAbstractReader is the base class for OnvistaStockReader and OnvistaBondReader.
    It implements shared attributes and methods across all readers and how the historical price data is parsed, while
    the derived classes implement their own security-specific methods (e.g. OnvistaBondReader.duration and OnvistaStockReader.income_statement).
    """
    def __init__(self, isin) -> None:
        self._isin = isin
        self._data = self._get_data()
        self._name = self._data["instrument"]["name"]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(Name: {self.name}, ISIN: {self.isin})"

    def _get_data(self) -> dict:
        if self.__class__.__name__ == "OnvistaStockReader":
            section = "aktien"
        elif self.__class__.__name__ == "OnvistaBondReader":
            section = "anleihen"
        elif self.__class__.__name__ == "OnvistaFundReader":
            section = "fonds"
        else:
            raise NotImplementedError()

        html = requests.get(f"https://www.onvista.de/{section}/handelsplaetze/{self.isin}", headers=HEADERS).text
        data = json.loads(html.split('type="application/json">')[-1].split("</script>")[0])["props"]["pageProps"]["data"]["snapshot"]
        return data

    @property
    def isin(self) -> str:
        return self._isin

    @property
    def name(self) -> str:
        return self._name

    def exchanges(self) -> list:
        data = self._data["quoteList"]["list"]
        data = [
            {
                "name": item["market"]["name"],
                "abbr": item["market"]["codeExchange"],
                "code": item["market"]["codeMarket"],
                "dataset_id": item["market"]["idNotation"],
                "country": item["market"]["isoCountry"],
                "currency": item["isoCurrency"],
                "volume": item["volume"] if "volume" in item else 0,
                "4_week_volume": item["volume4Weeks"],
                "unit": item["unitType"]
            }
            for item in data
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

    def coupon_dates(self, timestamps=True) -> list:
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
            "coupon": details["coupon"] if "coupon" in details else 0,
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

    def top_holdings(self) -> list:
        data = self._data["fundsHoldingList"]["list"]
        data = [
            {
                "name": item["instrument"]["name"],
                "percentage": round(item["investmentPct"] / 100, 6)
            }
            for item in data
        ]
        return data