from findata import FrenchReader
import pandas as pd
import numpy as np


def test_datasets():
    datasets = FrenchReader.datasets()
    assert isinstance(datasets, list)
    assert len(datasets) == 297
    for item in datasets:
        assert isinstance(item, str)


def test_retrieval():
    data = FrenchReader("F-F_Research_Data_Factors").read()
    assert ("Main" in data) and ("Annual Factors" in data)
    assert all(col in ("Mkt-RF", "SMB", "HML", "RF") for col in data["Main"].columns)
    assert all(isinstance(date, pd.Timestamp) for date in data["Main"].index)
    assert all(isinstance(date, pd.Timestamp) for date in data["Annual Factors"].index)
    for col in ("Mkt-RF", "SMB", "HML", "RF"):
        assert data["Main"][col].dtype == np.float64


def test_sorted_portfolios():
    data = FrenchReader("Portfolios_Formed_on_BE-ME").read()
    assert all(
        key in (
            "Value Weight Returns Monthly",
            "Equal Weight Returns Monthly",
            "Value Weight Returns Annual",
            "Equal Weight Returns Annual",
            "Number of Firms in Portfolios",
            "Number of Firms in Portfolios",
            "Average Firm Size",
            "Sum of BE / Sum of ME",
            "Value Weight Average of BE / ME"
        )
        for key in data
    )
    for key in data:
        assert all(isinstance(date, pd.Timestamp) for date in data[key].index)
        for col in data[key]:
            assert data[key][col].dtype in (np.int64, np.float64)


def test_industry_portfolios():
    data = FrenchReader("49_Industry_Portfolios").read()
    assert all(
        key in (
            "Average Value Weighted Returns Monthly",
            "Average Equal Weighted Returns Monthly",
            "Average Value Weighted Returns Annual",
            "Average Equal Weighted Returns Annual",
            "Number of Firms in Portfolios",
            "Average Firm Size",
            "Sum of BE / Sum of ME",
            "Value-Weighted Average of BE/ME",
            "industries"
        )
        for key in data
    )
    for key in data:
        if key == "industries":
            continue
        assert all(isinstance(date, pd.Timestamp) for date in data[key].index)
        for col in data[key]:
            assert data[key][col].dtype in (np.int64, np.float64)

    for col in data["Average Value Weighted Returns Monthly"].columns:
        assert isinstance(data["industries"][col]["name"], str)
        assert len(data["industries"][col]["sic_codes"]) > 0
        for item in data["industries"][col]["sic_codes"]:
            assert isinstance(item["name"], str)
            assert isinstance(item["lower"], int)
            assert isinstance(item["upper"], int)

def test_timestamps():
    data = FrenchReader("Portfolios_Formed_on_BE-ME", timestamps=True).read()
    for key in data:
        assert all(isinstance(item, int) for item in data[key].index)