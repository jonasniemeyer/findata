import pandas as pd

class ShillerReader:

    @classmethod
    def cape(cls, timestamps=False) -> pd.DataFrame:
        df = pd.read_excel(
            io="http://www.econ.yale.edu/~shiller/data/ie_data.xls",
            sheet_name="Data",
            skiprows=(0,1,2,3,4,5,7),
            skipfooter=1,
            index_col=0
        )
        df.index = [
            pd.to_datetime(f"{str(item)[:4]}-{str(item)[-2:]}-01") if len(str(item)) == 7
            else pd.to_datetime(f"{str(item)[:4]}-10-01")
            for item in df.index
        ]
        df = df.drop(["Date  ", "Unnamed: 13", "Unnamed: 15"], axis=1)
        df = df.rename(
            columns = {
                "Comp.": "Index",
                "Dividend": "Dividends",
                "Index": "CPI",
                "Interest": "10-Year Interest Rate",
                "Real": "Real Index",
                "Real.1": "Real Dividends",
                "Return": "Real Total Price Return",
                "Real.2": "Real Earnings",
                "Scaled": "Real TR Scaled Earnings",
                "P/E10 or": "CAPE",
                "TR P/E10 or": "Total Price Return CAPE",
                "CAPE": "Excess CAPE Yield",
                "Bond": "Total Bond Return",
                "Bond.1": "Real Total Bond Return",
                "Annualized Stock": "10-Year Annualized Real Stock Return",
                "Annualized Bonds": "10-Year Annualized Real Bond Return",
                "Excess Annualized ": "10-Year Annualized Excess Stock Return"
            }
        )
        if timestamps:
            df.index = [int(date.timestamp()) for date in df.index]
        return df