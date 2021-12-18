from finance_data import MSCIReader
import pandas as pd

def test_indices_list():
    data = MSCIReader.indices()
    assert all(
        key in data.columns
        for key in (
            "code",
            "name",
            "variant",
            "currency",
            "vendor",
            "type",
            "ticker_code"
        )
    )
    assert data["code"].dtype == "int64"

def test_historical_data_default():
    data = MSCIReader(139245).historical_data()
    df = data["data"]
    info = data["information"]
    assert info["index_code"] == 139245
    assert info["index_variant"] == "STRD"
    assert info["currency"] == "USD"
    assert info["url"] == "https://app2.msci.com/products/service/index/indexmaster/getLevelDataForGraph?currency_symbol=USD&index_variant=STRD&start_date=19690101&end_date=20211218&data_frequency=DAILY&index_codes=139245&normalize=False"
    assert all(
        isinstance(date, pd.Timestamp)
        for date in df.index
    )
    assert all(
        df[col].dtype == "float64"
        for col in df.columns
    )

def test_historical_data_monthly():
    data = MSCIReader(139245, frequency="monthly").historical_data()["data"]
    assert all(
        isinstance(date, pd.Timestamp)
        for date in data.index
    )
    assert all(
        data[col].dtype == "float64"
        for col in data.columns
    )

def test_historical_data_netr():
    data = MSCIReader(139245, index_variant="NETR").historical_data()["data"]
    assert all(
        isinstance(date, pd.Timestamp)
        for date in data.index
    )
    assert all(
        data[col].dtype == "float64"
        for col in data.columns
    )

def test_historical_data_strd():
    data = MSCIReader(139245, index_variant="STRD").historical_data()["data"]
    assert all(
        isinstance(date, pd.Timestamp)
        for date in data.index
    )
    assert all(
        data[col].dtype == "float64"
        for col in data.columns
    )

def test_currency_eur():
    data = MSCIReader(139245, index_currency="EUR").historical_data()["data"]
    assert all(
        isinstance(date, pd.Timestamp)
        for date in data.index
    )
    assert all(
        data[col].dtype == "float64"
        for col in data.columns
    )

def test_returns_off():
    data = MSCIReader(139245, returns=False).historical_data()["data"]
    assert all(
        isinstance(date, pd.Timestamp)
        for date in data.index
    )
    assert all(
        data[col].dtype == "float64"
        for col in data.columns
    )
    assert ("simple_returns" not in data.columns) and ("log_returns" not in data.columns)

def test_normalize():
    data = MSCIReader(139245, normalize=True).historical_data()["data"]
    assert all(
        isinstance(date, pd.Timestamp)
        for date in data.index
    )
    assert all(
        data[col].dtype == "float64"
        for col in data.columns
    )
    assert data.iloc[0, 0] == 100