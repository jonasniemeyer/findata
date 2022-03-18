from finance_data import MacrotrendsReader, TickerError
from finance_data.utils import MACROTRENDS_CONVERSION
import pytest

def test_default():
    data = MacrotrendsReader("AAPL").read()
    assert (("income statement" in data) and ("balance sheet" in data) and ("cashflow statement" in data))
    assert all(key in (data["income statement"] | data["balance sheet"] | data["cashflow statement"]) for key in MACROTRENDS_CONVERSION.values())
    for statement in data:
        for variable in data[statement]:
            for date in data[statement][variable]:
                assert data[statement][variable][date] is None or isinstance(data[statement][variable][date], (float, int))

def test_single_statement():
    for statement in ("income-statement", "balance-sheet", "cash-flow-statement"):
        data = MacrotrendsReader(ticker="AAPL", statement=statement).read()
        assert isinstance(data, dict)

def test_quarterly():
    data = MacrotrendsReader("AAPL", frequency="quarterly").read()
    assert (("income statement" in data) and ("balance sheet" in data)and ("cashflow statement" in data))

def test_hyphen_to_dot():
    data = MacrotrendsReader("BRK-A", frequency="quarterly").read()
    assert (("income statement" in data) and ("balance sheet" in data) and ("cashflow statement" in data))

def test_missing_data():
    with pytest.raises(TickerError):
        MacrotrendsReader("PLACEHOLDER", frequency="quarterly").read()

def test_timestamps():
    data = MacrotrendsReader("BRK-A", timestamps=True).read()
    for statement in data:
        for variable in data[statement]:
            assert all(isinstance(key, int) for key in data[statement][variable])