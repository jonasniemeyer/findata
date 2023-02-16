import datetime as dt
from finance_data import StratosphereReader

def test_fund_letters():
    letters = StratosphereReader.fund_letters()
    for letter in letters:
        assert isinstance(letter["company"], str)
        assert dt.date.fromisoformat(letter["date"])
        assert isinstance(letter["year"], int)
        assert letter["quarter"] in (1, 2, 3, 4)
        assert isinstance(letter["url"], str)
    
    letters = StratosphereReader.fund_letters(timestamps=True)
    for letter in letters:
        assert isinstance(letter["date"], int)

def test_investors():
    investors = StratosphereReader.investors()
    for investor in investors:
        assert isinstance(investor["name"], str)
        assert isinstance(investor["manager"], str)
        assert isinstance(investor["cik"], int)

        statistics = investor["statistics"]
        assert isinstance(statistics["market_value"], int)
        assert isinstance(statistics["no_holdings"], int)
        assert isinstance(statistics["purchased"], int)
        assert isinstance(statistics["sold"], int)
        assert isinstance(statistics["average_holding_period"], int)
        assert statistics["concentration"] == round(statistics["concentration"], 4)
        assert statistics["turnover"] == round(statistics["turnover"], 4)

        portfolio = investor["portfolio"]
        for security in portfolio:
            assert isinstance(security["ticker"], str)
            assert isinstance(security["cusip"], str)
            assert security["type"] in ("Share", "Call", "Put")
            assert security["weight"] == round(security["weight"], 6)