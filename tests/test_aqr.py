from finance_data import AQRReader
import pandas as pd

def test_esg_efficient_frontier_portfolios():
    data = AQRReader.esg_efficient_frontier_portfolios()
    assert len(data.keys()) == 2
    for key in ("Value-weighted excess returns", "Equal-weighted excess returns"):
        df = data[key]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert df.index.is_unique
        assert all(df[col].dtype == "float64" for col in df.columns)
        assert all(
            col in (
                "E1 \n(high CO2 emissions)", "E2", "E3", "E4",
                "E5 \n(low CO2 emissions)", "E5-E1", "S1\n(sin stocks)",
                "S2 \n(non-sin stocks)", "S2-S1", "G1 \n(high accruals)", "G2", "G3",
                "G4", "G5 \n(low accruals)", "G5-G1", "ESG1 \n(low ESG)", "ESG2",
                "ESG3", "ESG4", "ESG5\n(high ESG)", "ESG5-ESG1"
            )
            for col in df.columns
        )

def test_bab_factors_daily():
    data = AQRReader.bab_factors(frequency="daily")
    assert len(data.keys()) == 7
    for key in ("BAB Factors", "MKT", "SMB", "HML FF", "HML Devil", "UMD", "RF"):
        df = data[key]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert df.index.is_unique
        assert all(df[col].dtype == "float64" for col in df.columns)
        if key != "RF":
            assert all(
                col in (
                    "AUS", "AUT", "BEL", "CAN", "CHE", "DEU", "DNK", "ESP", "FIN", "FRA",
                    "GBR", "GRC", "HKG", "IRL", "ISR", "ITA", "JPN", "NLD", "NOR", "NZL",
                    "PRT", "SGP", "SWE", "USA", "Global", "Global Ex USA", "Europe",
                    "North America", "Pacific"
                )
                for col in df.columns if col != "RF"
            )
    assert "Risk Free Rate" in data["RF"].columns

def test_bab_factors_monthly():
    data = AQRReader.bab_factors(frequency="monthly")
    assert len(data.keys()) == 7
    for key in ("BAB Factors", "MKT", "SMB", "HML FF", "HML Devil", "UMD", "RF"):
        df = data[key]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert df.index.is_unique
        assert all(df[col].dtype == "float64" for col in df.columns)
        if key != "RF":
            assert all(
                col in (
                    "AUS", "AUT", "BEL", "CAN", "CHE", "DEU", "DNK", "ESP", "FIN", "FRA",
                    "GBR", "GRC", "HKG", "IRL", "ISR", "ITA", "JPN", "NLD", "NOR", "NZL",
                    "PRT", "SGP", "SWE", "USA", "Global", "Global Ex USA", "Europe",
                    "North America", "Pacific"
                )
                for col in df.columns if col != "RF"
            )
    assert "Risk Free Rate" in data["RF"].columns

def test_factor_premia_century():
    df = AQRReader.factor_premia_century()
    assert all(isinstance(date, pd.Timestamp) for date in df.index)
    assert df.index.is_unique
    assert all(df[col].dtype == "float64" for col in df.columns)
    assert all(
        col in (
            "US Stock Selection Value", "US Stock Selection Momentum",
            "US Stock Selection Defensive", "US Stock Selection Multi-style",
            "Intl Stock Selection Value", "Intl Stock Selection Momentum",
            "Intl Stock Selection Defensive", "Intl Stock Selection Multi-style",
            "Equity indices Value", "Equity indices Momentum",
            "Equity indices Carry", "Equity indices Defensive",
            "Equity indices Multi-style", "Fixed income Value",
            "Fixed income Momentum", "Fixed income Carry", "Fixed income Defensive",
            "Fixed income Multi-style", "Currencies Value", "Currencies Momentum",
            "Currencies Carry", "Currencies Multi-style", "Commodities Value",
            "Commodities Momentum", "Commodities Carry", "Commodities Multi-style",
            "All Stock Selection Value", "All Stock Selection Momentum",
            "All Stock Selection Defensive", "All Stock Selection Multi-style",
            "All Macro Value", "All Macro Momentum", "All Macro Carry",
            "All Macro Defensive", "All Macro Multi-style",
            "All asset classes Value", "All asset classes Momentum",
            "All asset classes Carry", "All asset classes Defensive",
            "All asset classes Multi-style", "Equity indices Market",
            "Fixed income Market", "Commodities Market", "All Macro Market"
        )
        for col in df.columns
    )

def test_commodities_long_run():
    df = AQRReader.commodites_long_run()
    assert all(isinstance(date, pd.Timestamp) for date in df.index)
    assert df.index.is_unique
    assert all(df[col].dtype == "float64" for col in df.columns if col not in("State of backwardation/contango", "State of inflation"))
    assert all(
        col in (
            "Excess return of equal-weight commodities portfolio",
            "Excess spot return of equal-weight commodities portfolio",
            "Interest rate adjusted carry of equal-weight commodities portfolio",
            "Spot return of equal-weight commodities portfolio",
            "Carry of equal-weight commodities portfolio",
            "Excess return of long/short commodities portfolio",
            "Excess spot return of long/short commodities portfolio",
            "Interest rate adjusted carry of long/short commodities portfolio",
            "Aggregate backwardation/contango", "State of backwardation/contango",
            "State of inflation"
        )
        for col in df.columns
    )

def test_momentum_indices():
    data = AQRReader.momentum_indices()
    assert len(data.keys()) == 2
    df = data["Monthly"]
    assert all(isinstance(date, pd.Timestamp) for date in df.index)
    assert df.index.is_unique
    assert all(df[col].dtype == "float64" for col in df.columns)
    assert all(
        col in ("U.S. Large Cap", "U.S. Small Cap", "International")
        for col in df.columns
    )
    df = data["Yearly"]
    assert all(isinstance(date, int) for date in df.index)
    assert df.index.is_unique
    assert all(df[col].dtype == "float64" for col in df.columns)
    assert all(
        col in ("U.S. Large Cap", "U.S. Small Cap", "International")
        for col in df.columns
    )

def test_quality_sorted_portfolios():
    data = AQRReader.quality_sorted_portfolios()
    assert len(data.keys()) == 2
    for key in ("US", "Global"):
        df = data[key]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert df.index.is_unique
        assert all(df[col].dtype == "float64" for col in df.columns)
        assert all(
            col in (
                "P1 (low quality)", "P2", "P3", "P4", "P5", 
                "P6", "P7", "P8", "P9", "P10 (high quality)"
            )
            for col in df.columns
        )

def test_qmj_factors_daily():
    data = AQRReader.qmj_factors(frequency="daily")
    assert len(data.keys()) == 7
    for key in ("QMJ Factors", "MKT", "SMB", "HML FF", "HML Devil", "UMD", "RF"):
        df = data[key]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert df.index.is_unique
        assert all(df[col].dtype == "float64" for col in df.columns)
        if key != "RF":
            assert all(
                col in (
                    "AUS", "AUT", "BEL", "CAN", "CHE", "DEU", "DNK", "ESP", "FIN", "FRA",
                    "GBR", "GRC", "HKG", "IRL", "ISR", "ITA", "JPN", "NLD", "NOR", "NZL",
                    "PRT", "SGP", "SWE", "USA", "Global", "Global Ex USA", "Europe",
                    "North America", "Pacific"
                )
                for col in df.columns
            )
    assert "Risk Free Rate" in data["RF"].columns

def test_qmj_factors_monthly():
    data = AQRReader.qmj_factors(frequency="daily")
    assert len(data.keys()) == 7
    for key in ("QMJ Factors", "MKT", "SMB", "HML FF", "HML Devil", "UMD", "RF"):
        df = data[key]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert df.index.is_unique
        assert all(df[col].dtype == "float64" for col in df.columns)
        if key != "RF":
            assert all(
                col in (
                    "AUS", "AUT", "BEL", "CAN", "CHE", "DEU", "DNK", "ESP", "FIN", "FRA",
                    "GBR", "GRC", "HKG", "IRL", "ISR", "ITA", "JPN", "NLD", "NOR", "NZL",
                    "PRT", "SGP", "SWE", "USA", "Global", "Global Ex USA", "Europe",
                    "North America", "Pacific"
                )
                for col in df.columns
            )
    assert "Risk Free Rate" in data["RF"].columns

def test_quality_size_sorted_portfolios():
    data = AQRReader.quality_size_sorted_portfolios()
    assert len(data.keys()) == 2
    for key in ("US", "Global"):
        df = data[key]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert df.index.is_unique
        assert all(df[col].dtype == "float64" for col in df.columns)
        assert all(
            col in (
                "Small Low", "Small Medium", "Small Large", "Big Low", 
                "Big Medium", "Big Large", "Factor"
            )
            for col in df.columns
        )

def test_hml_devil_factors_daily():
    data = AQRReader.hml_devil_factors(frequency="daily")
    assert len(data.keys()) == 6
    for key in ("HML Devil", "MKT", "SMB", "HML FF", "UMD", "RF"):
        df = data[key]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert df.index.is_unique
        assert all(df[col].dtype == "float64" for col in df.columns)
        if key != "RF":
            assert all(
                col in (
                    'AUS', 'AUT', 'BEL', 'CAN', 'CHE', 'DEU', 'DNK', 'ESP', 'FIN', 'FRA',
                    'GBR', 'GRC', 'HKG', 'IRL', 'ISR', 'ITA', 'JPN', 'NLD', 'NOR', 'NZL',
                    'PRT', 'SGP', 'SWE', 'USA', 'Global', 'Global Ex USA', 'Europe',
                    'North America', 'Pacific'
                )
                for col in df.columns
            )
    assert "Risk Free Rate" in data["RF"].columns

def test_hml_devil_factors_monthly():
    data = AQRReader.hml_devil_factors(frequency="daily")
    assert len(data.keys()) == 6
    for key in ("HML Devil", "MKT", "SMB", "HML FF", "UMD", "RF"):
        df = data[key]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert df.index.is_unique
        assert all(df[col].dtype == "float64" for col in df.columns)
        if key != "RF":
            assert all(
                col in (
                    "AUS", "AUT", "BEL", "CAN", "CHE", "DEU", "DNK", "ESP", "FIN", "FRA",
                    "GBR", "GRC", "HKG", "IRL", "ISR", "ITA", "JPN", "NLD", "NOR", "NZL",
                    "PRT", "SGP", "SWE", "USA", "Global", "Global Ex USA", "Europe",
                    "North America", "Pacific"
                )
                for col in df.columns
            )
    assert "Risk Free Rate" in data["RF"].columns

def test_time_series_momentum():
    df = AQRReader.time_series_momentum()
    assert all(isinstance(date, pd.Timestamp) for date in df.index)
    assert df.index.is_unique
    assert all(df[col].dtype == "float64" for col in df.columns)
    assert all(col in ("TSMOM", "TSMOM^CM", "TSMOM^EQ", "TSMOM^FI", "TSMOM^FX") for col in df.columns)

def test_value_momentum_everywhere_factors():
    df = AQRReader.value_momentum_everywhere_factors()
    assert all(isinstance(date, pd.Timestamp) for date in df.index)
    assert df.index.is_unique
    assert all(df[col].dtype == "float64" for col in df.columns)
    assert all(
        col in (
            "VAL", "MOM", "VAL^SS", "MOM^SS", "VAL^AA", "MOM^AA", "VALLS_VME_US90",
            "MOMLS_VME_US90", "VALLS_VME_UK90", "MOMLS_VME_UK90", "VALLS_VME_ROE90",
            "MOMLS_VME_ROE90", "VALLS_VME_JP90", "MOMLS_VME_JP90", "VALLS_VME_EQ",
            "MOMLS_VME_EQ", "VALLS_VME_FX", "MOMLS_VME_FX", "VALLS_VME_FI",
            "MOMLS_VME_FI", "VALLS_VME_COM", "MOMLS_VME_COM"
        )
        for col in df.columns
    )

def test_value_momentum_everywhere_portfolios():
    df = AQRReader.value_momentum_everywhere_portfolios()
    assert all(isinstance(date, pd.Timestamp) for date in df.index)
    assert df.index.is_unique
    assert all(df[col].dtype == "float64" for col in df.columns)
    assert all(
        col in (
            "VAL1US", "VAL2US", "VAL3US", "MOM1US", "MOM2US", "MOM3US", "VAL1UK",
            "VAL2UK", "VAL3UK", "MOM1UK", "MOM2UK", "MOM3UK", "VAL1EU", "VAL2EU",
            "VAL3EU", "MOM1EU", "MOM2EU", "MOM3EU", "VAL1JP", "VAL2JP", "VAL3JP",
            "MOM1JP", "MOM2JP", "MOM3JP", "VAL1_VME_EQ", "VAL2_VME_EQ",
            "VAL3_VME_EQ", "MOM1_VME_EQ", "MOM2_VME_EQ", "MOM3_VME_EQ",
            "VAL1_VME_FX", "VAL2_VME_FX", "VAL3_VME_FX", "MOM1_VME_FX",
            "MOM2_VME_FX", "MOM3_VME_FX", "VAL1_VME_FI", "VAL2_VME_FI",
            "VAL3_VME_FI", "MOM1_VME_FI", "MOM2_VME_FI", "MOM3_VME_FI",
            "VAL1_VME_COM", "VAL2_VME_COM", "VAL3_VME_COM", "MOM1_VME_COM",
            "MOM2_VME_COM", "MOM3_VME_COM"
        )
        for col in df.columns
    )