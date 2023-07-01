from findata import CMEReader
import numpy as np
import pandas as pd


class TestCMEReader:
    @classmethod
    def setup_class(cls):
        cls.reader = CMEReader("WTI Crude Oil")

    def test_attributes(self):
        assert self.reader.commodity == "WTI Crude Oil"
        assert self.reader.sector == "energy"
        assert self.reader.group == "crude-oil"
        assert self.reader.name == "west-texas-intermediate-wti-crude-oil-calendar-swap-futures"
        assert self.reader.timestamps == False

    def test_data(self):
        dct = self.reader.read()
        assert len(dct) in (4,5)
        for date, df in dct.items():
            assert isinstance(date, str) and pd.to_datetime(date)
            assert isinstance(df, pd.DataFrame)
            assert all(isinstance(date, pd.Timestamp) for date in df.index)
            assert df.index.is_unique is True
            for col in df.columns:
                assert isinstance(df[col].dtype, (type(np.dtype("float64")), type(np.dtype("int64"))))

    def test_timestamps_parameter(self):
        dct = CMEReader("WTI Crude Oil", timestamps=True).read()
        assert len(dct) in (4,5)
        for date, df in dct.items():
            assert isinstance(date, int) and pd.to_datetime(date, unit="s")
            assert isinstance(df, pd.DataFrame)
            assert all(isinstance(date, int) for date in df.index)
            assert df.index.is_unique is True
            for col in df.columns:
                assert isinstance(df[col].dtype, (type(np.dtype("float64")), type(np.dtype("int64"))))