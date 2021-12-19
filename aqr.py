import pandas as pd
from finance_data.utils import HEADERS

class AQRReader:

    @classmethod
    def esg_efficient_frontier(cls) -> dict:
        file = pd.ExcelFile("https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/ESG_efficient_frontier_portfolios_vF.xlsx")
        dfs = {}
        for name in ("Value-weighted excess returns", "Equal-weighted excess returns"):
            df = file.parse(
                sheet_name=name,
                skiprows=range(12),
                index_col=1
            )
            dfs[name] = df
        return dfs

    @classmethod
    def bab_factors(cls, frequency = "daily") -> dict:
        if frequency not in ("daily", "monthly"):
            raise ValueError("frequency must be daily or monthly")
        file = pd.ExcelFile(f"https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Betting-Against-Beta-Equity-Factors-{frequency}.xlsx")
        dfs = {}
        for name in ("BAB Factors", "MKT", "SMB", "HML FF", "HML Devil", "UMD", "RF"):
            df = file.parse(
                sheet_name=name,
                skiprows=range(18),
                index_col=0
            )
            dfs[name] = df
        return dfs
    
    @classmethod
    def factor_premia_century(cls) -> dict:
        file = pd.ExcelFile("https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Century-of-Factor-Premia-Monthly.xlsx")
        dfs = {}
        for name in ("Century of Factor Premia"):
            df = file.parse(
                sheet_name=name,
                skiprows=range(18),
                index_col=0
            )
            dfs[name] = df
        return dfs
    
    @classmethod
    def commodites_long_run(cls) -> dict:
        file = pd.ExcelFile("https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Commodities-for-the-Long-Run-Index-Level-Data-Monthly.xlsx")
        dfs = {}
        for name in ("Commodities for the Long Run"):
            df = file.parse(
                sheet_name=name,
                skiprows=range(10),
                index_col=0
            )
            dfs[name] = df
        return dfs

    @classmethod
    def momentum_indices(cls) -> dict:
        file = pd.ExcelFile("https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/AQR-Index-Returns.xls")
        dfs = {}
        for name in ("Returns"):
            df = file.parse(
                sheet_name=name,
                skiprows=range(18),
                index_col=0
            )
            dfs[name] = df
        return dfs

    @classmethod
    def quality_sorted_portfolios(cls) -> dict:
        file = pd.ExcelFile("https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Quality-Minus-Junk-10-QualitySorted-Portfolios-Monthly.xlsx")
        dfs = {}
        for name in ("10 Portfolios Formed on Quality"):
            df = file.parse(
                sheet_name=name,
                skiprows=range(18),
                index_col=0
            )
            dfs[name] = df
        return dfs

    @classmethod
    def qmj_factors(cls, frequency = "daily") -> dict:
        if frequency not in ("daily", "monthly"):
            raise ValueError("frequency must be daily or monthly")
        dfs = {}
        file = pd.ExcelFile(f"https://images.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Quality-Minus-Junk-Factors-{frequency}.xlsx")
        for name in ("QMJ Factors", "MKT", "SMB", "HML FF", "HML Devil", "UMD", "RF"):
            df = file.parse(
                sheet_name=name,
                skiprows=range(18),
                index_col=0
            )
            dfs[name] = df
        return dfs
    
    @classmethod
    def quality_size_sorted_portfolios(cls) -> dict:
        file = pd.ExcelFile("https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Quality-Minus-Junk-Six-Portfolios-Formed-on-Size-and-Quality-Monthly.xlsx")
        dfs = {}
        for name in ("Size x Quality (2 x3)"):
            df = file.parse(
                sheet_name=name,
                skiprows=range(18),
                index_col=0
            )
            dfs[name] = df
        return dfs

    @classmethod
    def hml_devil_factors(cls, frequency = "daily") -> dict:
        if frequency not in ("daily", "monthly"):
            raise ValueError("frequency must be daily or monthly")
        file = pd.ExcelFile(f"https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/The-Devil-in-HMLs-Details-Factors-{frequency}.xlsx")
        dfs = {}
        for name in ("HML Devil", "MKT", "SMB", "HML FF", "UMD", "RF"):
            df = file.parse(
                sheet_name=name,
                skiprows=range(18),
                index_col=0
            )
            dfs[name] = df
        return dfs

    @classmethod
    def time_series_momentum(cls) -> dict:
        file = pd.ExcelFile("https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Time-Series-Momentum-Factors-Monthly.xlsx")
        dfs = {}
        for name in ("TSMOM Factors"):
            df = file.parse(
                sheet_name=name,
                skiprows=range(18),
                index_col=0
            )
            dfs[name] = df
        return dfs

    @classmethod
    def value_momentum_everywhere_factors(cls) -> dict:
        file = pd.ExcelFile("https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Value-and-Momentum-Everywhere-Factors-Monthly.xlsx")
        dfs = {}
        for name in ("VME Factors"):
            df = file.parse(
                sheet_name=name,
                skiprows=range(21),
                index_col=0
            )
            dfs[name] = df
        return dfs

    @classmethod
    def value_momentum_everywhere_portfolios(cls) -> dict:
        file = pd.ExcelFile("https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Value-and-Momentum-Everywhere-Portfolios-Monthly.xlsx")
        dfs = {}
        for name in ("VME Portfolios"):
            df = file.parse(
                sheet_name=name,
                skiprows=range(20),
                index_col=0
            )
            dfs[name] = df
        return dfs
