# finance_data: A library to retrieve financial and economic data from the web

## Description
**finance_data** is a Python library that allows to retrieve finance-related datasets from the web including
historical stock prices, fundamental data, condensed sec filing data and more.
<br>
## Dependencies
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [numpy](https://www.numpy.org)
- [pandas](https://pandas.pydata.org/)
- [requests](https://docs.python-requests.org/en/master/)
- [selenium](https://selenium-python.readthedocs.io/)
<br>
<br>

# Documentation

## YahooReader
---
The YahooReader class is able to fetch datasets provided by [Yahoo Finance](https://finance.yahoo.com/). Because Yahoo Finance
has no company logo and isin data, the YahooReader class instead compiles its logo data from [Clearbit](https://clearbit.com/logo)
and its isin from [Businessinsider](https://markets.businessinsider.com/).
<br>

### Instance Methods
---
- analyst_recommendations(timestamps=False)
> returns a dictionary of historical analyst recommendations, consisting of the name of the rating firm, the date, the rating and whether it maintained, upgraded or downgraded the stock  
>> timestamps : bool  
>>> specifies whether the date is given as an ISO-formatted string or a UNIX-timestamp integer  
>>> Default : False

- balance_sheet(quarterly=False, timestamps=False)
> returns a dictionary of balance-sheet data either of the past 4 year or of the past 5 quarters  
>> quarterly : bool  
>>> specifies whether the balance-sheet data is quarterly or annual  
>>> Default : False  
>  
>> timestamps : bool  
>>> specifies whether the date is given as an ISO-formatted string or a UNIX-timestamp integer  
>>> Default : False
>  
> *Related: financial_statement(), cashflow_statement() and income_statement()*

- cashflow_statement(quarterly=False, timestamps=False)
> returns a dictionary of cashflow-statement data either of the past 4 year or of the past 5 quarters  
>> quarterly : bool  
>>> specifies whether the cashflow-statement data is quarterly or annual  
>>> Default : False  
>  
>> timestamps : bool  
>>> specifies whether the date is given as an ISO-formatted string or a UNIX-timestamp integer  
>>> Default : False
>  
> *Related: financial_statement(), balance_sheet() and income_statement()*

- esg_scores()
> returns a dictionary of esg scores, including esg classifications in which the company operates in

- financial_statement(quarterly=False, timestamps=False, merged=False)
> returns a dictionary of financial-statement data either of the past 4 year or of the past 5 quarters  
>> quarterly : bool  
>>> specifies whether the financiaö-statement data is quarterly or annual  
>>> Default : False  
>  
>> timestamps : bool  
>>> specifies whether the date is given as an ISO-formatted string or a UNIX-timestamp integer  
>>> Default : False
>  
>> merged : bool  
>>> specifies whether the data is returned as one dictionary containing the income-statement,
>>> balance-sheet and cashflow-statement data or as a dictionary containing three dictionaries, each
>>> containing the respective dataset
>>> Default : False
>  
> *Related: balance_sheet, cashflow_statement() and income_statement()*

- fund_ownership(timestamps=False)
> returns a dictionary of the top 10 funds that have the security in their portfolio, including the names, the date, the percentage of the market capitalization, the number of shares and the market value
>> timestamps : bool  
>>> specifies whether the date is given as an ISO-formatted string or a UNIX-timestamp integer  
>>> Default : False

- fund_statistics()
> returns fund statistics, including the associated company, the type of the fund and statistics such as expense ratio, assets under management and annual turnover (works only for funds)

- historical_data(frequency="1d", start=datetime.datetime(1900, 1, 1), end=datetime.datetime.today(), returns=True, "timestamps=False, rounded=False, tz_aware=False)
> returns a pandas.DataFrame consisting of OHLC prices, dividends, stock split ratios and simple- and log-returns
>> frequency : str 
>>> specifies the sampling frequency of the data and can be 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
>>> Default : "1d"  
>  
>> start : str, integer, datetime.date or datetime.datetime object   
>>> specifies the starting date of the sample
>>> Default : datetime.datetime(1900, 1, 1)
>  
>> end : str, integer, datetime.date or datetime.datetime object   
>>> specifies the ending date of the sample
>>> Default : datetime.datetime.today()
>  
>> returns : bool   
>>> specifies whether the pandas.DataFrame also contains simple and log returns
>>> Default : True
>  
>> timestamps : bool  
>>> specifies whether the date is given as an ISO-formatted string or a UNIX-timestamp integer  
>>> Default : False
>  
>> rounded : bool 
>>> specifies whether prices are rounded to two decimals
>>> Default : False
>  
>> tz_aware : bool 
>>> specifies whether dates (in case the timestamps parameter is False) are timezone-aware and hence will be converted to local time instead of UTC
>>> Default : False

- holdings()
> returns a dictionary of the major holdings of a fund, including the ticker, name of the security and the percentage it makes up in the fund. The method also returns a possible industry breakdown, aggregate valuation of the securities and distribution of bond ratings (works only for funds)

- income_statement(quarterly=False, timestamps=False)
> returns a dictionary of income-statement data either of the past 4 year or of the past 5 quarters  
>> quarterly : bool  
>>> specifies whether the income-statement data is quarterly or annual  
>>> Default : False  
>  
>> timestamps : bool  
>>> specifies whether the date is given as an ISO-formatted string or a UNIX-timestamp integer  
>>> Default : False
>  
> *Related: balance_sheet, cashflow_statement() and financual_statement()*

- insider_ownership(timestamps=False)
> returns a dictionary of executive stock positions, including the position and name of the executive, the date, the number of shares and the date and order of the latest trade
>> timestamps : bool  
>>> specifies whether the date is given as an ISO-formatted string or a UNIX-timestamp integer  
>>> Default : False

- insider_trades(timestamps=False)
> returns a list of historical insider trades, including the name and position of the executive, the date and order of the trade and the number of shares and market value
>> timestamps : bool  
>>> specifies whether the date is given as an ISO-formatted string or a UNIX-timestamp integer  
>>> Default : False

- institutional_ownership(timestamps=False)
> returns a list of the largest insitutions holding the stock, including the name of the institution, the percentage of the market cap, the number of shares and the market value

- options(date=None, strike_min=None, strike_max=None, straddle=False, timestamps=False)
> returns rar options data without any cleaning

- ownership_breakdown(timestamps=False)
> returns a dictionary containing the distribution of insiders and institutionals holding the security
>> timestamps : bool  
>>> specifies whether the date is given as an ISO-formatted string or a UNIX-timestamp integer  
>>> Default : False

- recommendation_trend(timestamps=False)
> returns a dictionary of consensus recommendations of today and the last three months, containing the number of analysts, the number of ratings in each category (strong buy to strong sell) and the mean of the ratings
>> timestamps : bool  
>>> specifies whether the date is given as an ISO-formatted string or a UNIX-timestamp integer  
>>> Default : False

- sec_filings(timestamps=False)
> returns a list of recent sec filings, including the date, the form type and the url
>> timestamps : bool  
>>> specifies whether the date is given as an ISO-formatted string or a UNIX-timestamp integer  
>>> Default : False

<br>

### Instance Attributes
---
- isin
> returns the isin that is associated with the security. If no isin is found, it returns None.

- logo
> returns the logo of the company in bytes (works only for companies)

- name
> returns the name of the security

- ticker
> returns the ticker of the security

<br>

### Class Methods
---
- currencies()
> returns a list of all major currencies, including the name and the abbreviation

<br>

### Code Examples
---

