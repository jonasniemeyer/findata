from findata import (
    OnvistaBondReader,
    OnvistaFundReader,
    OnvistaStockReader
)
import numpy as np
import pandas as pd

class TestOnvistaBondReader:
    @classmethod
    def setup_class(cls):
        cls.reader = OnvistaBondReader("AT0000A1XML2")

    def test_attributes(self):
        assert isinstance(self.reader.accrued_interest, float)
        assert isinstance(self.reader.convexity, float)
        assert isinstance(self.reader.interest_elasticity, float)
        assert self.reader.isin == "AT0000A1XML2"
        assert isinstance(self.reader.macaulay_duration, float)
        assert isinstance(self.reader.modified_duration, float)
        assert self.reader.name == "OEsterreich, Republik EO-Med.-Term Notes 2017(2117)"
        assert isinstance(self.reader.ytm, float)

    def test_coupon_dates(self):
        dates = self.reader.coupon_dates()
        assert all(isinstance(date, str) and pd.to_datetime(date) for date in dates)

    def test_exchanges(self):
        exchanges = self.reader.exchanges()
        for item in exchanges:
            assert isinstance(item["name"], str)
            assert isinstance(item["abbr"], str)
            assert isinstance(item["code"], str)
            assert isinstance(item["dataset_id"], int)
            assert isinstance(item["country"], str)
            assert isinstance(item["currency"], str)
            assert isinstance(item["volume"], int)
            assert isinstance(item["4_week_volume"], int)
            assert isinstance(item["unit"], str)

    def test_historical_data(self):
        data = self.reader.historical_data()
        info = data["information"]
        assert info["instrument_id"] == 128035187
        assert info["dataset_id"] == 221783897
        assert info["start"] == "2018-06-25"
        assert isinstance(info["end"], str) and pd.to_datetime(info["end"])
        assert info["exchange"]["name"] == "Tradegate"
        assert info["exchange"]["code"] == "_GAT"
        assert info["exchange"]["country"] == "DE"
        assert info["currency"] == "EUR"

        df = data["data"]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert df.index.is_unique is True
        for col in df.columns:
            assert isinstance(df[col].dtype, (type(np.dtype("float64")), type(np.dtype("int64"))))

    def test_issuer(self):
        issuer = self.reader.issuer()
        assert issuer["name"] == "Österreich, Republik"
        assert issuer["country"]["name"] == "Österreich"
        assert issuer["country"]["abbr"] == "AT"
        assert issuer["type"] == "öffentlich"
        assert issuer["sub_type"] == "Bund"

    def test_profile(self):
        profile = self.reader.profile()
        assert profile["bond_type"] == "Anleihe"
        assert profile["coupon_type"] == "Fest"
        assert profile["coupon"] == 2.1
        assert profile["nominal_value"] == 1000
        assert profile["maturity"] == "2117-09-20"
        assert profile["currency"] == "EUR"
        assert isinstance(profile["next_coupon_payment"], str) and pd.to_datetime(profile["next_coupon_payment"])
        assert profile["emission_price"] == 99.502
        assert profile["emission_volume"] == 6_000_000_000
        assert profile["in_default"] is False
        assert profile["perpetual"] is False
        assert profile["callable"] is False