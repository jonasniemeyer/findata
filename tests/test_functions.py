from finance_data import finra_margin_debt, shiller_cape
import pandas as pd
import numpy as np

def test_finra_margin_debt():
    data = finra_margin_debt()
    assert all(key in ("combined full", "combined new", "combined old", "finra old", "nyse old") for key in data)
    for key in data:
        df = data[key]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert all(df[col].dtype == "int64" for col in df.columns)
    assert all(col in ("debit", "credit") for col in data["combined full"])
    assert all(col in ("debit", "credit cash accounts", "credit margin accounts") for col in data["combined new"])
    assert all(col in ("debit", "credit") for col in data["combined old"])
    assert all(col in ("debit", "credit") for col in data["finra old"])
    assert all(col in ("debit", "credit cash accounts", "credit margin accounts") for col in data["nyse old"])

    assert all(pd.concat([data["combined old"], data["combined new"]])["debit"] == data["combined full"]["debit"])

    data = finra_margin_debt(timestamps=True)
    for key in data:
        assert all(isinstance(item, int) for item in data[key].index)

def test_shiller_cape():
    df = shiller_cape()
    assert all(isinstance(date, pd.Timestamp) for date in df.index)
    for col in df.columns:
        assert col in (
        "S&P 500 Index",
        "S&P 500 Dividends",
        "S&P 500 Earnings",
        "CPI",
        "10-Year Interest Rate",
        "S&P 500 Real Index",
        "S&P 500 Real Dividends",
        "Real Total Price Return",
        "Real Earnings",
        "Real TR Scaled Earnings",
        "CAPE",
        "Total Price Return CAPE",
        "Excess CAPE Yield",
        "Total Bond Return",
        "Real Total Bond Return",
        "10-Year Annualized Real Stock Return",
        "10-Year Annualized Real Bond Return",
        "10-Year Annualized Excess Stock Return"
        )
    for col in df.columns:
        assert df[col].dtype in (np.int32, np.float64)

    df = shiller_cape(timestamps=True)
    assert all(isinstance(date, int) for date in df.index)