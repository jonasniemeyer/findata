from findata import (
    OnvistaBondReader,
    OnvistaFundReader,
    OnvistaStockReader
)
import numpy as np
import pandas as pd
from pytest import mark


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
        assert isinstance(info["instrument_id"], int)
        assert isinstance(info["dataset_id"], int)
        assert isinstance(info["start"], str) and pd.to_datetime(info["start"])
        assert isinstance(info["end"], str) and pd.to_datetime(info["end"])
        assert isinstance(info["exchange"]["name"], str)
        assert isinstance(info["exchange"]["code"], str)
        assert isinstance(info["exchange"]["country"], str)
        assert isinstance(info["currency"], str)

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


class TestOnvistaFundReader:
    @classmethod
    def setup_class(cls):
        cls.reader = OnvistaFundReader("LU0323578657")

    def test_attributes(self):
        assert self.reader.isin == "LU0323578657"
        assert self.reader.issuer == "Flossbach von Storch Invest S.A."
        assert self.reader.name == "Flossbach von Storch Multiple Opportunities R"

    def test_benchmark_indices(self):
        assert self.reader.benchmark_indices() == [{"name": "MSCI WORLD INDEX (GDTR, UHD)", "url": "https://www.onvista.de/index/MSCI-WORLD-INDEX-GDTR-UHD-Index-12221463", "id": 12221463}]

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
        assert isinstance(info["instrument_id"], int)
        assert isinstance(info["dataset_id"], int)
        assert isinstance(info["start"], str) and pd.to_datetime(info["start"])
        assert isinstance(info["end"], str) and pd.to_datetime(info["end"])
        assert isinstance(info["exchange"]["name"], str)
        assert isinstance(info["exchange"]["code"], str)
        assert isinstance(info["exchange"]["country"], str)
        assert isinstance(info["currency"], str)

        df = data["data"]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert df.index.is_unique is True
        for col in df.columns:
            assert isinstance(df[col].dtype, (type(np.dtype("float64")), type(np.dtype("int64"))))

    def test_managers(self):
        assert self.reader.managers == ["Dr. Bert Flossbach"]

    def test_morningstar_rating(self):
        rating = self.reader.morningstar_rating()
        for key in rating:
            assert key in ("bond_style", "equity_style", "rating", "sustainability")
        assert isinstance(rating["bond_style"], int)
        assert isinstance(rating["equity_style"], int)
        for key, data in rating["rating"].items():
            assert key in ("1y", "3y", "5y", "10y")
            assert isinstance(data, int)
        assert isinstance(rating["sustainability"], str)

    def test_profile(self):
        profile = self.reader.profile()
        assert isinstance(profile["aum"], int)
        assert profile["emission_date"] == "2007-10-23"
        assert profile["currency"] == "EUR"
        assert profile["custodian_bank"] == "DZ Privatbank S.A."
        assert profile["custodian_country"]["name"] == "Luxemburg"
        assert profile["custodian_country"]["abbr"] == "LU"
        assert profile["intitial_charge"] == 0.05
        assert profile["ter"] == 0.016269
        assert profile["management_fee"] == 0.0153
        assert profile["custodian_fee"] == 0.0009

    def test_reports(self):
        reports = self.reader.reports()
        for key, url in reports.items():
            assert isinstance(key, str)
            assert url.startswith("https://mediaproxy.mdgms.com/download.html?docId=")

    def test_sector_breakdown(self):
        breakdown = self.reader.sector_breakdown()
        for key, percent in breakdown.items():
            assert key in ("Konsumgüter zyklisch", "Finanzen", "Informationstechnologie", "Basiskonsumgüter", "Gesundheitswesen", "Industrie", "Telekomdienste", "Rohstoffe")
            assert round(percent, 4) == percent

    def test_top_holdings(self):
        holdings = self.reader.top_holdings()
        for item in holdings:
            assert isinstance(item["name"], str)
            assert round(item["percentage"], 4) == item["percentage"]


class TestOnvistaStockReader:
    @classmethod
    def setup_class(cls):
        cls.reader = OnvistaStockReader("DE0005190003")

    def test_attributes(self):
        self.reader.country == {"name": "Deutschland", "abbr": "DE"}
        assert self.reader.isin == "DE0005190003"
        assert self.reader.long_name == "Bayerische Motoren Werke AG Stammaktien EO 1"
        market_cap = self.reader.market_cap
        assert isinstance(market_cap["market_cap"], (int, float))
        assert market_cap["currency"] == "EUR"
        assert self.reader.name == "BMW"
        sector = self.reader.sector
        assert sector["sector"] == "Automobilproduktion"
        assert sector["description"] == "Kraftfahrzeugindustrie"
        assert isinstance(self.reader.shares_outstanding, int)
    
    @mark.skip(reason="test not implemented")
    def test_accounting_data(self):
        data = self.reader.accounting_data()

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
    
    @mark.skip(reason="test not implemented")
    def test_financial_ratios(self):
        ratios = self.reader.financial_ratios()

    def test_historical_data(self):
        data = self.reader.historical_data()
        info = data["information"]
        assert isinstance(info["instrument_id"], int)
        assert isinstance(info["dataset_id"], int)
        assert isinstance(info["start"], str) and pd.to_datetime(info["start"])
        assert isinstance(info["end"], str) and pd.to_datetime(info["end"])
        assert isinstance(info["exchange"]["name"], str)
        assert isinstance(info["exchange"]["code"], str)
        assert isinstance(info["exchange"]["country"], str)
        assert isinstance(info["currency"], str)

        df = data["data"]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert df.index.is_unique is True
        for col in df.columns:
            assert isinstance(df[col].dtype, (type(np.dtype("float64")), type(np.dtype("int64"))))
    
    @mark.skip(reason="test not implemented")
    def test_price_ratios(self):
        ratios = self.reader.price_ratios()

    def test_splits(self):
        assert self.reader.splits() == {"1999-08-23": 26, "1991-06-05": 1.125}