# findata: A library to retrieve financial and economic data from the web

## Description
**findata** is a Python library that allows to retrieve finance-related datasets from the web including
historical stock prices, fundamental data, condensed sec filing data and more.
<br>
Since findata scrapes data from websites, the package is just for educational purposes.
If you use it, you should refer to the respective terms of service of each website first.
<br>
## Dependencies
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [numpy](https://www.numpy.org)
- [pandas](https://pandas.pydata.org/)
- [requests](https://docs.python-requests.org/en/master/)
- [selenium](https://selenium-python.readthedocs.io/)

# Documentation

*There will be a thorough documentation in the near future.*
<br>
The package provides the following classes to scrape financial and economic datasets:
- AQRReader
- CMEReader
- FinvizReader
- FREDReader
- FrenchReader
- MacrotrendsReader
- MarketscreenerReader
- MSCIReader
- OnvistaBondReader
- OnvistaFundReader
- OnvistaStockReader
- Filing3
- Filing4
- Filing5
- Filing13D
- Filing13G
- Filing13F
- FilingNPORT
- SECFundamentals
- StratosphereReader
- TipranksAnalystReader
- TipranksStockReader
- YahooReader

Additionally, there are functions to retrieve unrelated datasets:
- latest_sec_filings
- sec_companies
- sec_filings
- sec_mutualfunds
- finra_margin_debt
- shiller_data
- sp_index_data

The package also provides multiple classes to fetch news:
- EconomistNews
- FTNews
- NasdaqNews
- SANews
- WSJNews