from findata import (
    finra_margin_debt,
    lei_to_cik,
    shiller_data,
    sp_index_data
)
from findata.utils import DatasetError
import pandas as pd
import numpy as np
from requests import HTTPError


def test_finra_margin_debt():
    df = finra_margin_debt()
    assert all(col in ("debit", "credit_cash_accounts", "credit_margin_accounts") for col in df)
    assert all(isinstance(date, pd.Timestamp) for date in df.index)
    assert all(df[col].dtype in ("int64", "float64") for col in df.columns)

    df = finra_margin_debt(timestamps=True)
    assert all(isinstance(item, int) for item in df.index)


def test_lei_to_cik():
    # Apple
    try:
        assert lei_to_cik("HWUPKR0MPOU8FGXBT394") == 320193
    except HTTPError:
        pass
    # BASF
    try:
        assert lei_to_cik("529900PM64WH8AF1E917") is None
    except HTTPError:
        pass
    # fake LEI
    try:
        assert lei_to_cik("THISISNOTALEI") is None
    except HTTPError:
        pass


def test_shiller_data():
    df = shiller_data()
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

    df = shiller_data(timestamps=True)
    assert all(isinstance(date, int) for date in df.index)


def test_sp_index_data():
    data = sp_index_data()
    dfs = (
        data["quarterly_data"],
        data["sector_data"]["prices"],
        data["sector_data"]["operating_data"]["quarterly_eps"],
        data["sector_data"]["operating_data"]["yearly_eps"],
        data["sector_data"]["operating_data"]["yearly_pe"],
        data["sector_data"]["reported_data"]["quarterly_eps"],
        data["sector_data"]["reported_data"]["yearly_eps"],
        data["sector_data"]["reported_data"]["yearly_pe"]
    )
    for df in dfs:
        assert all(isinstance(date, pd.Timestamp) for date in df.index)

    for col in data["quarterly_data"].columns:
        assert col in (
            "Operating Earnings Per Share",
            "Reported Earnings Per Share",
            "Dividends Per Share",
            "PER SHR.2",
            "Sales Per Share",
            "Book Value Per Share",
            "Capital Expenditures Per Share",
            "Price",
            "Divisor"
        )

    for df in dfs[1:]:
        for col in df.columns:
            assert col in (
                "S&P 500",
                "S&P 500 Consumer Discretionary",
                "S&P 500 Consumer Staples",
                "S&P 500 Energy",
                "S&P 500 Financials",
                "S&P 500 Health Care",
                "S&P 500 Industrials",
                "S&P 500 Information Technology",
                "S&P 500 Materials",
                "S&P 500 Communication Services",
                "S&P 500 Utilities",
                "S&P 500 Real Estate (proforma pre-9/19/16)",
                "S&P 400",
                "S&P 400 Consumer Discretionary",
                "S&P 400 Consumer Staples",
                "S&P 400 Energy",
                "S&P 400 Financials",
                "S&P 400 Health Care",
                "S&P 400 Industrials",
                "S&P 400 Information Technology",
                "S&P 400 Materials",
                "S&P 400 Communication Services",
                "S&P 400 Utilities",
                "S&P 400 Real Estate (proforma pre-9/19/16)",
                "S&P 600",
                "S&P 600 Consumer Discretionary",
                "S&P 600 Consumer Staples",
                "S&P 600 Energy",
                "S&P 600 Financials",
                "S&P 600 Health Care",
                "S&P 600 Industrials",
                "S&P 600 Information Technology",
                "S&P 600 Materials",
                "S&P 600 Communication Services",
                "S&P 600 Utilities",
                "S&P 600 Real Estate (proforma pre-9/19/16)",
                "S&P Composite 1500",
                "S&P Composite 1500 Consumer Discretionary",
                "S&P Composite 1500 Consumer Staples",
                "S&P Composite 1500 Energy",
                "S&P Composite 1500 Financials",
                "S&P Composite 1500 Health Care",
                "S&P Composite 1500 Industrials",
                "S&P Composite 1500 Information Technology",
                "S&P Composite 1500 Materials",
                "S&P Composite 1500 Communication Services",
                "S&P Composite 1500 Utilities",
                "S&P Composite 1500 Real Estate (proforma pre-9/19/16)"
            )