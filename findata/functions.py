from bs4 import BeautifulSoup
import pandas as pd
import requests
import utils


def finra_margin_debt(timestamps=False) -> dict:
    dataset_url = "https://www.finra.org/investors/learn-to-invest/advanced-investing/margin-statistics"
    data = {
        "combined new": [],
        "finra old": [],
        "nyse old": [],
        "combined old": []
    }
    
    html = requests.get(url=dataset_url, headers=utils.HEADERS).text
    
    finra = html.index("FINRA Statistics (shown in $ millions)")
    nyse = html.index("NYSE Statistics (shown in $ millions)")
    combined = html.index("FINRA and NYSE Combined Statistics (shown in $ millions)")
    
    data_new = html[:finra]
    data_finra = html[finra:nyse]
    data_nyse = html[nyse:combined]
    data_combined = html[combined:]
    
    for data_slice, key in zip(
        (
            data_new,
            data_finra,
            data_nyse,
            data_combined
        ),
        data
    ):
        soup = BeautifulSoup(data_slice, "lxml")
        rows = soup.find_all("tr")
        rows = [row.find_all("td") for row in rows if len(row.find_all("td")) > 1]
        rows = [
            [item.text for item in sublist]
            for sublist in rows
        ]
        for row in rows:
            date, *values = row
            values = [int(item.replace(",", "")) for item in values]
            try:
                date = pd.to_datetime(date.replace("Sept", "Sep"), format="%b-%y")
            except:
                date = pd.to_datetime(date, format="%B-%y")
            datapoint = (date, *values)
            data[key].append(datapoint)
        data[key] = pd.DataFrame(
            data = data[key],
            columns = ["month", "debit", "credit cash accounts", "credit margin accounts"] if len(data[key][0]) == 4 \
            else ["month", "debit", "credit"]
        )
        data[key].set_index("month", inplace=True, drop=True)
        data[key].sort_index(inplace=True)
        if timestamps:
            data[key].index = [int(date.timestamp()) for date in data[key].index]
    new_aggregated = pd.DataFrame()
    new_aggregated["debit"] = data["combined new"]["debit"]
    new_aggregated["credit"] = data["combined new"]["credit cash accounts"] + data["combined new"]["credit margin accounts"]
    data["combined full"] = pd.concat([new_aggregated, data["combined old"]]).sort_index()
    data = {
        "combined full": data["combined full"] * 1_000_000,
        "combined new": data["combined new"] * 1_000_000,
        "combined old": data["combined old"] * 1_000_000,
        "finra old": data["finra old"] * 1_000_000,
        "nyse old": data["nyse old"] * 1_000_000
    }

    return data


def shiller_data(timestamps=False) -> pd.DataFrame:
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
            "Comp.": "S&P 500 Index",
            "Dividend": "S&P 500 Dividends",
            "Earnings": "S&P 500 Earnings",
            "Index": "CPI",
            "Interest": "10-Year Interest Rate",
            "Real": "S&P 500 Real Index",
            "Real.1": "S&P 500 Real Dividends",
            "Return": "Real Total Price Return",
            "Real.2": "Real Earnings",
            "Scaled": "Real TR Scaled Earnings",
            "P/E10 or": "CAPE",
            "TR P/E10 or": "Total Price Return CAPE",
            "CAPE": "Excess CAPE Yield",
            "Bond": "Total Bond Return",
            "Bond.1": "Real Total Bond Return",
            "Annualized Stock": "10-Year Annualized Real Stock Return",
            "Annualized Bonds ": "10-Year Annualized Real Bond Return",
            "Excess Annualized ": "10-Year Annualized Excess Stock Return"
        }
    )
    if timestamps:
        df.index = [int(date.timestamp()) for date in df.index]
    return df


def sp_index_data(timestamps=False) -> dict:
    response = requests.get(
        url="https://www.spglobal.com/spdji/en/documents/additional-material/sp-500-eps-est.xlsx",
        headers=utils.HEADERS
    ).content

    data = {}

    #parse quarterly per-share data 
    quarterly_data = pd.read_excel(response, sheet_name="QUARTERLY DATA", skiprows=5, index_col=0)
    quarterly_data.index.name = "date"
    quarterly_data.rename(
        columns={
            "PER SHR": "Operating Earnings Per Share",
            "PER SHR.1": "Reported Earnings Per Share",
            "PER SHR.2": "Dividends Per Share",
            "SHARE": "Sales Per Share",
            "SHARE.1": "Book Value Per Share",
            "PER SHARE": "Capital Expenditures Per Share",
            "PRICE": "Price",
            "DIVISOR": "Divisor"
        },
        inplace=True
    )
    quarterly_data = quarterly_data[::-1]
    if timestamps:
        quarterly_data.index = [int(date.timestamp()) for date in quarterly_data.index]

    #parse sector-eps and -price data
    sector_data = pd.read_excel(response, sheet_name="SECTOR EPS", skiprows=5, index_col=0).iloc[:, 1:-1]
    sector_data.index.name = "date"
    sector_data = sector_data.T
    sector_data.columns = [item.strip() if isinstance(item, str) else item for item in sector_data.columns]

    blank1, blank2 = [sector_data.index.get_loc(col) for col in sector_data.index if "Unnamed:" in col]
    op_eps_index = sector_data.columns.get_loc("Operating Earnings Per Share by Economic Sector")
    reported_eps_index = sector_data.columns.get_loc("As Reported Earnings Per Share by Economic Sector")
    end_index = sector_data.columns.get_loc("Notes:")

    op_eps = sector_data.iloc[:, op_eps_index+1: reported_eps_index-2]
    op_eps = op_eps.loc[:, op_eps.columns.dropna()]

    reported_eps = sector_data.iloc[:, reported_eps_index+2: end_index-1]
    reported_eps = reported_eps.loc[:, reported_eps.columns.dropna()]

    quarterly_op_eps = op_eps.iloc[:blank1, :]
    index = []
    for item in quarterly_op_eps.index:
        item = item.replace("E", "").replace("Q", "")
        year, quarter = item.split()
        index.append(pd.to_datetime(f"{year}-{int(quarter)*3:02}-01"))
    quarterly_op_eps.index = index
    quarterly_op_eps = quarterly_op_eps.resample("Q").last()
    if timestamps:
        quarterly_op_eps.index = [int(date.timestamp()) for date in quarterly_op_eps.index]

    yearly_op_eps = op_eps.iloc[blank1+1:blank2, :]
    eps = yearly_op_eps[yearly_op_eps.index.str.contains("EPS")]
    eps.index = [pd.to_datetime(f"{item.split()[0].replace('E', '')}-12-31") for item in eps.index]
    if timestamps:
        eps.index = [int(date.timestamp()) for date in eps.index]
    pe = yearly_op_eps[yearly_op_eps.index.str.contains("P/E")]
    pe.index = [pd.to_datetime(f"{item.split()[0].replace('E', '')}-12-31") for item in pe.index]
    if timestamps:
        pe.index = [int(date.timestamp()) for date in pe.index]
    operating_data = {
        "quarterly_eps": quarterly_op_eps,
        "yearly_eps": eps,
        "yearly_pe": pe
    }

    quarterly_reported_eps = reported_eps.iloc[:blank1, :]
    index = []
    for item in quarterly_reported_eps.index:
        item = item.replace("E", "").replace("Q", "")
        year, quarter = item.split()
        index.append(pd.to_datetime(f"{year}-{int(quarter)*3:02}-01"))
    quarterly_reported_eps.index = index
    quarterly_reported_eps = quarterly_reported_eps.resample("Q").last()
    if timestamps:
        quarterly_reported_eps.index = [int(date.timestamp()) for date in quarterly_reported_eps.index]

    yearly_reported_eps = reported_eps.iloc[blank1+1:blank2, :]
    eps = yearly_reported_eps[yearly_reported_eps.index.str.contains("EPS")]
    eps.index = [pd.to_datetime(f"{item.split()[0].replace('E', '')}-12-31") for item in eps.index]
    if timestamps:
        eps.index = [int(date.timestamp()) for date in eps.index]
    pe = yearly_op_eps[yearly_op_eps.index.str.contains("P/E")]
    pe.index = [pd.to_datetime(f"{item.split()[0].replace('E', '')}-12-31") for item in pe.index]
    if timestamps:
        pe.index = [int(date.timestamp()) for date in pe.index]
    reported_data = {
        "quarterly_eps": quarterly_reported_eps,
        "yearly_eps": eps,
        "yearly_pe": pe
    }

    prices = op_eps.iloc[blank2+1:, :].applymap(lambda x: round(x, 2))
    prices.index = [pd.to_datetime(f"20{item[-2:]}-12-31") for item in prices.index]
    if timestamps:
        prices.index = [int(date.timestamp()) for date in prices.index]

    data["quarterly_data"] = quarterly_data
    data["sector_data"] = {
        "prices": prices,
        "operating_data": operating_data,
        "reported_data": reported_data
    }

    return data