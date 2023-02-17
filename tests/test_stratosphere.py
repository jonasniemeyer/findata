import datetime as dt
from finance_data import StratosphereReader

NoneType = type(None)

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

class TestUSEquity:
    @classmethod
    def setup_class(cls):
        cls.reader = StratosphereReader("AAPL")

    def test_profile(self):
        profile = self.reader.profile()
        assert profile["ticker"] == "AAPL"
        assert profile["name"] == "Apple Inc."
        assert profile["cik"] == 320193
        assert profile["website"] == "https://www.apple.com"
        assert profile["exchange"] == "NASDAQ"
        assert profile["country"] == "US"
        assert profile["currency"]["name"] == "USD"
        assert profile["currency"]["exchange_rate"] == 1
        assert isinstance(profile["market_cap"], int)

    def test_prices(self):
        prices = self.reader.prices()
        for date, price in prices.items():
            assert dt.date.fromisoformat(date)
            assert isinstance(price, (int, float))

        prices = self.reader.prices(timestamps=True)
        for date, price in prices.items():
            assert isinstance(date, int)

    def test_price_targets(self):
        price_targets = self.reader.price_targets()
        for item in price_targets:
            assert isinstance(item["price_target"], (int, float))
            assert dt.datetime.fromisoformat(item["datetime"])
            assert isinstance(item["analyst_company"], (str, NoneType))
            assert isinstance(item["analyst_name"], (str, NoneType))
            assert isinstance(item["news_title"], (str, NoneType))
            assert isinstance(item["news_source"], (str, NoneType))
            assert isinstance(item["news_url"], (str, NoneType))
            assert isinstance(item["price_when_rated"], (int, float))

        price_targets = self.reader.price_targets(timestamps=True)
        for item in price_targets:
            assert isinstance(item["datetime"], int)

    def test_price_target_consensus(self):
        consensus = self.reader.price_target_consensus()
        for key in ("average", "median", "high", "low"):
            assert isinstance(consensus[key], (int, float))