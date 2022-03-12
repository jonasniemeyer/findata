from finance_data import MacrotrendsReader, TickerError
from finance_data.utils import MACROTRENDS_CONVERSION
import pytest

def test_default():
    data = MacrotrendsReader("AAPL").read()
    assert (
        ("income_statement" in data.keys())
        and ("balance_sheet" in data.keys())
        and ("cashflow_statement" in data.keys())
    )
    assert all(
        key in (data["income_statement"] | data["balance_sheet"] | data["cashflow_statement"])
        for key in MACROTRENDS_CONVERSION.values()
    )

def test_single_statement():
    for statement in ("income-statement", "balance-sheet", "cash-flow-statement"):
        data = MacrotrendsReader(ticker="AAPL", statement=statement).read()
        assert isinstance(data, dict)

def test_quarterly():
    data = MacrotrendsReader("AAPL", frequency="quarterly").read()
    assert (
        ("income_statement" in data.keys())
        and ("balance_sheet" in data.keys())
        and ("cashflow_statement" in data.keys())
    )

def test_hyphen_to_dot():
    data = MacrotrendsReader("BRK-A", frequency="quarterly").read()
    assert (
        ("income_statement" in data.keys())
        and ("balance_sheet" in data.keys())
        and ("cashflow_statement" in data.keys())
    )

def test_missing_data():
    with pytest.raises(TickerError):
        MacrotrendsReader("PLACEHOLDER", frequency="quarterly").read()

def test_timestamps():
    data = MacrotrendsReader("BRK-A", timestamps=True).read()
    assert all(
        all(
            all(
                isinstance(key, int) for key in data[statement][variable].keys()
            )
            for variable in data[statement].keys()
        )
        for statement in data.keys()
    )