from finance_data import margin_debt
import pandas as pd

def test_margin_debt():
    data = margin_debt()
    assert all(key in ("combined full", "combined new", "combined old", "finra old", "nyse old") for key in data.keys())
    for key in data:
        df = data[key]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert all(df[col].dtype == "int64" for col in df.columns)
    assert all(col in ('debit', 'credit') for col in data["combined full"])
    assert all(col in ('debit', 'credit cash accounts', 'credit margin accounts') for col in data["combined new"])
    assert all(col in ('debit', 'credit') for col in data["combined old"])
    assert all(col in ('debit', 'credit') for col in data["finra old"])
    assert all(col in ('debit', 'credit cash accounts', 'credit margin accounts') for col in data["nyse old"])

    assert all(pd.concat([data["combined old"], data["combined new"]])["debit"] == data["combined full"]["debit"])

    data = margin_debt(timestamps=True)
    assert all(
        all(
            isinstance(item, int) for item in data[dataset].index
        )
        for dataset in data.keys()
    )

