from finance_data import FrenchReader
import pandas as pd

def test_datasets():
    datasets = FrenchReader.datasets()
    assert isinstance(datasets, list)
    assert len(datasets) == 297

def test_retrieval():
    data = FrenchReader("F-F_Research_Data_Factors").read()
    assert ("Main" in data.keys()) and ("Annual Factors" in data.keys())
    assert all(
        column in data["Main"].columns for column in (
            "Mkt-RF", "SMB", "HML", "RF"
        )
    )
    assert all(
        isinstance(date, pd.Timestamp) for date in data["Main"].index
    )
    assert all(
        isinstance(date, pd.Timestamp) for date in data["Annual Factors"].index
    )

def test_retrieval_sorted_portfolios():
    data = FrenchReader("Portfolios_Formed_on_BE-ME").read()
    assert all(
        key in data.keys() for key in (
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
    )
    assert all(
        all(
            isinstance(date, (pd.Timestamp, int)) for date in data[key].index
        )
        for key in data.keys()
    )

def test_timestamps():
    data = FrenchReader("Portfolios_Formed_on_BE-ME", timestamps=True).read()
    assert all(
        all(
            isinstance(item, int) for item in data[dataset].index
        )
        for dataset in data.keys()
    )