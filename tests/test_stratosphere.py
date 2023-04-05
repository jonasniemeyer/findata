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

    def test_income_statement(self):
        income_data = self.reader.income_statement()
        for freq in ("annual", "quarterly"):
            for segment in income_data[freq]:
                assert isinstance(segment, str)
                for date, value in income_data[freq][segment].items():
                    assert dt.date.fromisoformat(date)
                    assert isinstance(value, (int, float, NoneType))

        income_data = self.reader.income_statement(timestamps=True)
        for freq in ("annual", "quarterly"):
            for segment in income_data[freq]:
                for date, value in income_data[freq][segment].items():
                    assert isinstance(date, int)

    def test_balance_sheet(self):
        balance_data = self.reader.balance_sheet()
        for freq in ("annual", "quarterly"):
            for segment in balance_data[freq]:
                assert isinstance(segment, str)
                for date, value in balance_data[freq][segment].items():
                    assert dt.date.fromisoformat(date)
                    assert isinstance(value, (int, float, NoneType))

        balance_data = self.reader.income_statement(timestamps=True)
        for freq in ("annual", "quarterly"):
            for segment in balance_data[freq]:
                for date, value in balance_data[freq][segment].items():
                    assert isinstance(date, int)

    def test_cashflow_statement(self):
        cashflow_data = self.reader.cashflow_statement()
        for freq in ("annual", "quarterly"):
            for segment in cashflow_data[freq]:
                assert isinstance(segment, str)
                for date, value in cashflow_data[freq][segment].items():
                    assert dt.date.fromisoformat(date)
                    assert isinstance(value, (int, float, NoneType))

        cashflow_data = self.reader.income_statement(timestamps=True)
        for freq in ("annual", "quarterly"):
            for segment in cashflow_data[freq]:
                for date, value in cashflow_data[freq][segment].items():
                    assert isinstance(date, int)

    def test_financial_ratios(self):
        ratios_data = self.reader.financial_ratios()
        for freq in ("annual", "quarterly"):
            for segment in ratios_data[freq]:
                assert isinstance(segment, str)
                for date, value in ratios_data[freq][segment].items():
                    assert dt.date.fromisoformat(date)
                    assert isinstance(value, (int, float, NoneType))

        ratios_data = self.reader.income_statement(timestamps=True)
        for freq in ("annual", "quarterly"):
            for segment in ratios_data[freq]:
                for date, value in ratios_data[freq][segment].items():
                    assert isinstance(date, int)

    def test_financial_statement(self):
        income_data = self.reader.income_statement()
        balance_data = self.reader.balance_sheet()
        cashflow_data = self.reader.cashflow_statement()
        ratios_data = self.reader.financial_ratios()

        financial_data = self.reader.financial_statement()
        for key, data in {
            "income_statement": income_data,
            "balance_sheet": balance_data,
            "cashflow_cashflow": cashflow_data,
            "financial_ratios": ratios_data
        }.items():
            assert financial_data[key] == data

        financial_data = self.reader.financial_statement(merged=True)
        for freq in financial_data:
            assert freq in ("annual", "quarterly")

        vars = set(
            var for item in (
                income_data["annual"],
                balance_data["annual"],
                cashflow_data["annual"],
                ratios_data["annual"]
            )
            for var in item
        )
        for freq in ("annual", "quarterly"):
            for var in financial_data[freq]:
                assert var in vars

    def test_segment_information(self):
        segment_data = self.reader.segment_information()
        for freq in ("annual", "quarterly"):
            for segment in segment_data[freq]:
                assert segment in (
                    "Mac Revenue",
                    "Services Gross Profit",
                    "Products Gross Profit",
                    "Wearables, Home and Accessories Revenue",
                    "Products Revenue",
                    "iPhone Revenue",
                    "Services Revenue",
                    "iPad Revenue"
                )
                for date, value in segment_data[freq][segment].items():
                    assert dt.date.fromisoformat(date)
                    assert isinstance(value, (int, float, NoneType))

        segment_data = self.reader.kpi_information(timestamps=True)
        for freq in ("annual", "quarterly"):
            for segment in segment_data[freq]:
                for date, value in segment_data[freq][segment].items():
                    assert isinstance(date, int)

    def test_kpi_information(self):
        kpi_data = self.reader.kpi_information()
        for freq in ("annual", "quarterly"):
            assert tuple(kpi_data[freq].keys()) == ("iPhone Installed User Base",)
            for date, value in kpi_data[freq]["iPhone Installed User Base"].items():
                assert dt.date.fromisoformat(date)
                assert isinstance(value, (int, float, NoneType))

        kpi_data = self.reader.kpi_information(timestamps=True)
        for freq in ("annual", "quarterly"):
            for date, value in kpi_data[freq]["iPhone Installed User Base"].items():
                assert isinstance(date, int)

    def test_analyst_estimates(self):
        estimates = self.reader.analyst_estimates()
        for freq in ("annual", "quarterly"):
            for var in estimates[freq]:
                assert isinstance(var, str)
                for date, value in estimates[freq][var].items():
                    assert dt.date.fromisoformat(date)
                    assert isinstance(value, (int, float))

        estimates = self.reader.analyst_estimates(timestamps=True)
        for freq in ("annual", "quarterly"):
            for var in estimates[freq]:
                for date, value in estimates[freq][var].items():
                    assert isinstance(date, int)

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


class TestNonUSEquity:
    @classmethod
    def setup_class(cls):
        cls.reader = StratosphereReader("7309.T")

    def test_profile(self):
        profile = self.reader.profile()
        assert profile["ticker"] == "7309.T"
        assert profile["name"] == "Shimano Inc."
        assert profile["cik"] is None
        assert profile["website"] == "https://www.shimano.com"
        assert profile["exchange"] == "JPX"
        assert profile["country"] == "JP"
        assert profile["currency"]["name"] == "JPY"
        assert isinstance(profile["currency"]["exchange_rate"], float)
        assert isinstance(profile["market_cap"], int)

    def test_income_statement(self):
        income_data = self.reader.income_statement()
        for freq in ("annual", "quarterly"):
            for segment in income_data[freq]:
                assert isinstance(segment, str)
                for date, value in income_data[freq][segment].items():
                    assert dt.date.fromisoformat(date)
                    assert isinstance(value, (int, float, NoneType))

        income_data = self.reader.income_statement(timestamps=True)
        for freq in ("annual", "quarterly"):
            for segment in income_data[freq]:
                for date, value in income_data[freq][segment].items():
                    assert isinstance(date, int)

    def test_balance_sheet(self):
        balance_data = self.reader.balance_sheet()
        for freq in ("annual", "quarterly"):
            for segment in balance_data[freq]:
                assert isinstance(segment, str)
                for date, value in balance_data[freq][segment].items():
                    assert dt.date.fromisoformat(date)
                    assert isinstance(value, (int, float, NoneType))

        balance_data = self.reader.income_statement(timestamps=True)
        for freq in ("annual", "quarterly"):
            for segment in balance_data[freq]:
                for date, value in balance_data[freq][segment].items():
                    assert isinstance(date, int)

    def test_cashflow_statement(self):
        cashflow_data = self.reader.cashflow_statement()
        for freq in ("annual", "quarterly"):
            for segment in cashflow_data[freq]:
                assert isinstance(segment, str)
                for date, value in cashflow_data[freq][segment].items():
                    assert dt.date.fromisoformat(date)
                    assert isinstance(value, (int, float, NoneType))

        cashflow_data = self.reader.income_statement(timestamps=True)
        for freq in ("annual", "quarterly"):
            for segment in cashflow_data[freq]:
                for date, value in cashflow_data[freq][segment].items():
                    assert isinstance(date, int)

    def test_financial_ratios(self):
        ratios_data = self.reader.financial_ratios()
        for freq in ("annual", "quarterly"):
            for segment in ratios_data[freq]:
                assert isinstance(segment, str)
                for date, value in ratios_data[freq][segment].items():
                    assert dt.date.fromisoformat(date)
                    assert isinstance(value, (int, float, NoneType))

        ratios_data = self.reader.income_statement(timestamps=True)
        for freq in ("annual", "quarterly"):
            for segment in ratios_data[freq]:
                for date, value in ratios_data[freq][segment].items():
                    assert isinstance(date, int)

    def test_financial_statement(self):
        income_data = self.reader.income_statement()
        balance_data = self.reader.balance_sheet()
        cashflow_data = self.reader.cashflow_statement()
        ratios_data = self.reader.financial_ratios()

        financial_data = self.reader.financial_statement()
        for key, data in {
            "income_statement": income_data,
            "balance_sheet": balance_data,
            "cashflow_cashflow": cashflow_data,
            "financial_ratios": ratios_data
        }.items():
            assert financial_data[key] == data

        financial_data = self.reader.financial_statement(merged=True)
        for freq in financial_data:
            assert freq in ("annual", "quarterly")

        vars = set(
            var for item in (
                income_data["annual"],
                balance_data["annual"],
                cashflow_data["annual"],
                ratios_data["annual"]
            )
            for var in item
        )
        for freq in ("annual", "quarterly"):
            for var in financial_data[freq]:
                assert var in vars

    def test_segment_information(self):
        segment_data = self.reader.segment_information()
        assert segment_data == {}

    def test_kpi_information(self):
        kpi_data = self.reader.kpi_information()
        assert kpi_data == {}

    def test_analyst_estimates(self):
        estimates = self.reader.analyst_estimates()
        assert estimates == {}

        estimates = self.reader.analyst_estimates(timestamps=True)
        assert estimates == {}

    def test_prices(self):
        prices = self.reader.prices()
        assert prices == {}

    def test_price_targets(self):
        price_targets = self.reader.price_targets()
        assert price_targets == {}

    def test_price_target_consensus(self):
        consensus = self.reader.price_target_consensus()
        assert consensus == {}