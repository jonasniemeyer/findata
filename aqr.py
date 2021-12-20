import pandas as pd
from datetime import datetime, timedelta
from finance_data.utils import HEADERS

class AQRReader:

    @classmethod
    def _from_excel_ordinal(cls, ordinal, epoch=datetime(1899, 12, 31)):
        if ordinal >= 60:
            ordinal -= 1
        return epoch + timedelta(days=ordinal)
    
    @classmethod
    def esg_efficient_frontier_portfolios(cls) -> dict:
        file = pd.ExcelFile("https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/ESG_efficient_frontier_portfolios_vF.xlsx")
        dfs = {}
        for name, skip_rows in ("Value-weighted excess returns", 12), ("Equal-weighted excess returns", 9):
            df = file.parse(
                sheet_name=name,
                skiprows=range(skip_rows)
            )
            df1 = pd.DataFrame(data=df[["Date", "E1 \n(high CO2 emissions)", "E2", "E3", "E4", "E5 \n(low CO2 emissions)", "E5-E1"]]).dropna()
            df1.set_index("Date", inplace=True)
            df2 = pd.DataFrame(data=df[["Date.1", "S1\n(sin stocks)", "S2 \n(non-sin stocks)", "S2-S1"]]).dropna()
            df2.set_index("Date.1", inplace=True)
            df3 = pd.DataFrame(data=df[["Date.2", "G1 \n(high accruals)", "G2", "G3", "G4", "G5 \n(low accruals)", "G5-G1"]]).dropna()
            df3.set_index("Date.2", inplace=True)
            df4 = pd.DataFrame(data=df[["Date.3", "ESG1 \n(low ESG)", "ESG2", "ESG3", "ESG4", "ESG5\n(high ESG)", "ESG5-ESG1"]]).dropna()
            df4.set_index("Date.3", inplace=True)
            df = pd.concat([df1, df2, df3, df4], axis=1)
            dfs[name] = df
        return dfs
    
    @classmethod
    def bab_factors(cls, frequency="daily") -> dict:
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
            df.index = [cls._from_excel_ordinal(item) if bool_ else item for (item, bool_) in zip(df.index, df.index.astype(str).str.isdigit())]
            dfs[name] = df
        return dfs
    
    @classmethod
    def factor_premia_century(cls) -> pd.DataFrame:
        df = pd.read_excel(
            io="https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Century-of-Factor-Premia-Monthly.xlsx",
            sheet_name="Century of Factor Premia",
            skiprows=range(18),
            index_col=0
        )
        df.index = [cls._from_excel_ordinal(item) if bool_ else item for (item, bool_) in zip(df.index, df.index.astype(str).str.isdigit())]
        df.index = pd.to_datetime(df.index)
        return df
    
    @classmethod
    def commodites_long_run(cls) -> pd.DataFrame:
        df = pd.read_excel(
            io="https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Commodities-for-the-Long-Run-Index-Level-Data-Monthly.xlsx",
            sheet_name="Commodities for the Long Run",
            skiprows=range(10),
            index_col=0
        )
        return df
    
    @classmethod
    def momentum_indices(cls) -> pd.DataFrame:
        dfs = {}
        df = pd.read_excel(
            io="https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/AQR-Index-Returns.xls",
            sheet_name="Returns",
            skiprows=range(1),
            index_col=0
        )
        df1 = df[["U.S. Large Cap", "U.S. Small Cap", "International"]]
        df1.index.name = "Date"
        df2 = df[['Year', 'U.S. Large Cap.1', 'U.S. Small Cap.1', 'International.1']].dropna(how="all")
        df2["Year"] = df2["Year"].astype("int64")
        df2.set_index("Year", inplace=True)
        df2.columns = ["U.S. Large Cap", "U.S. Small Cap", "International"]
        dfs["Monthly"] = df1
        dfs["Yearly"] = df2
        return dfs
    
    @classmethod
    def quality_sorted_portfolios(cls) -> dict:
        file = pd.ExcelFile("https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Quality-Minus-Junk-10-QualitySorted-Portfolios-Monthly.xlsx")
        dfs = {}
        for name in ("10 Portfolios Formed on Quality",):
            df = file.parse(
                sheet_name=name,
                skiprows=range(18),
                index_col=0
            )
            df1 = pd.DataFrame(data=df[["P1 (low quality)", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10 (high quality)"]])
            df2 = pd.DataFrame(data=df[["P1 (low quality).1", "P2.1", "P3.1", "P4.1", "P5.1", "P6.1", "P7.1", "P8.1", "P9.1", "P10 (high quality).1"]])
            df2.columns = ["P1 (low quality)", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10 (high quality)"]
            dfs["US"] = df1
            dfs["Global"] = df2
        return dfs
    
    @classmethod
    def qmj_factors(cls, frequency="daily") -> dict:
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
            df.index = [cls._from_excel_ordinal(item) if bool_ else item for (item, bool_) in zip(df.index, df.index.astype(str).str.isdigit())]
            dfs[name] = df
        return dfs
    
    @classmethod
    def quality_size_sorted_portfolios(cls) -> dict:
        file = pd.ExcelFile("https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Quality-Minus-Junk-Six-Portfolios-Formed-on-Size-and-Quality-Monthly.xlsx")
        dfs = {}
        for name in ("Size x Quality (2 x3)",):
            df = file.parse(
                sheet_name=name,
                skiprows=range(18),
                index_col=0
            )
            df1 = pd.DataFrame(data=df[["Low", "Medium", "Large", "Low.1", "Medium.1", "Large.1", "Factor"]])
            df1.columns = ["Small Low", "Small Medium", "Small Large", "Big Low", "Big Medium", "Big Large", "Factor"]
            df2 = pd.DataFrame(data=df[["Low.2", "Medium.2", "Large.2", "Low.3", "Medium.3", "Large.3", "Factor.1"]])
            df2.columns = ["Small Low", "Small Medium", "Small Large", "Big Low", "Big Medium", "Big Large", "Factor"]
            dfs["US"] = df1
            dfs["Global"] = df2
        return dfs
    
    @classmethod
    def hml_devil_factors(cls, frequency="daily") -> dict:
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
            df.index = [cls._from_excel_ordinal(item) if bool_ else item for (item, bool_) in zip(df.index, df.index.astype(str).str.isdigit())]
            dfs[name] = df
        return dfs
    
    @classmethod
    def time_series_momentum(cls) -> pd.DataFrame:
        df = pd.read_excel(
            io="https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Time-Series-Momentum-Factors-Monthly.xlsx",
            sheet_name="TSMOM Factors",
            skiprows=range(17),
            index_col=0
        )
        return df
    
    @classmethod
    def value_momentum_everywhere_factors(cls) -> pd.DataFrame:
        df = pd.read_excel(
            io="https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Value-and-Momentum-Everywhere-Factors-Monthly.xlsx",
            sheet_name="VME Factors",
            skiprows=range(21),
            index_col=0
        )
        return df
    
    @classmethod
    def value_momentum_everywhere_portfolios(cls) -> pd.DataFrame:
        df = pd.read_excel(
            io="https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Value-and-Momentum-Everywhere-Portfolios-Monthly.xlsx",
            sheet_name="VME Portfolios",
            skiprows=range(20),
            index_col=0
        )
        return df