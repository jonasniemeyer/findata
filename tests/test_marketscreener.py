import re
from findata import MarketscreenerReader

NoneType = type(None)

class TestMarketscreenerReader:
    def setup_class(cls):
        cls.reader = MarketscreenerReader("AAPL")

    def test_general_methods(self):
        assert self.reader.currency() == "USD"
        assert self.reader.isin() == "US0378331005"
        assert isinstance(self.reader.latest_price(), float)
        assert self.reader.name() == "APPLE INC."
        assert self.reader.ticker() == "AAPL"

    def test_board_members(self):
        members = self.reader.board_members()
        for member in members:
            assert isinstance(member["name"], str)
            assert isinstance(member["title"], str)
            assert isinstance(member["age"], (int, NoneType))
            assert isinstance(member["joined"], (int, NoneType))

    def test_country_information(self):
        info = self.reader.country_information()
        for year, data in info.items():
            assert isinstance(year, int)
            for country, value in data.items():
                assert country in (
                    "United States",
                    "Europe",
                    "Greater China",
                    "Rest Of Asia Pacific",
                    "Japan",
                    "Americas"
                )
                assert isinstance(value, float)

    def test_financial_statement(self):
        statement = self.reader.financial_statement()
        for year, data in statement.items():
            assert isinstance(year, int)
            for variable, value in data.items():
                assert variable in (
                    "Net Sales",
                    "Net Sales Analysts",
                    "EBITDA",
                    "EBITDA Analysts",
                    "Operating Profit",
                    "Operating Profit Analysts",
                    "Operating Margin",
                    "Operating Margin Analysts",
                    "Pre-Tax Profit",
                    "Pre-Tax Profit Analysts",
                    "Net Income",
                    "Net Income Analysts",
                    "Net Margin",
                    "Net Margin Analysts",
                    "EPS",
                    "EPS Analysts",
                    "Free Cash Flow",
                    "Free Cash Flow Analysts",
                    "FCF Margin",
                    "FCF Margin Analysts",
                    "FCF Conversion",
                    "FCF Conversion Analysts",
                    "Dividend Per Share",
                    "Dividend Per Share Analysts",
                    "Shareholders' Equity",
                    "Shareholders' Equity Analysts",
                    "Assets",
                    "Assets Analysts",
                    "Book Value Per Share",
                    "Book Value Per Share Analysts",
                    "Cash Flow Per Share",
                    "Cash Flow Per Share Analysts",
                    "Capex",
                    "Capex Analysts",
                    "Shares Outstanding"
                )
                assert isinstance(value, (int, float, NoneType))

        statement = self.reader.financial_statement(quarterly=True)
        for quarter in statement:
            assert isinstance(quarter, str)

    def test_industry_information(self):
        info = self.reader.industry_information()
        assert info == [
            "Technology",
            "Technology Equipment",
            "Computers, Phones & Household Electronics",
            "Phones & Handheld Devices",
            "Phones & Smart Phones"
        ]

    def test_managers(self):
        managers = self.reader.managers()
        for manager in managers:
            assert isinstance(manager["name"], str)
            assert isinstance(manager["title"], str)
            assert isinstance(manager["age"], (int, NoneType))
            assert isinstance(manager["joined"], (int, NoneType))

    def test_news(self):
        news = self.reader.news()
        for article in news:
            assert isinstance(article["title"], str)
            assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", article["date"])) == 1
            assert isinstance(article["source"]["name"], str)
            assert isinstance(article["source"]["abbreviation"], str)
            assert isinstance(article["url"], str)

    def test_segment_information(self):
        info = self.reader.segment_information()
        for year, data in info.items():
            assert isinstance(year, int)
            for segment, value in data.items():
                assert segment in (
                    "iPhone",
                    "Services",
                    "Wearables, Home and Accessories",
                    "Mac",
                    "iPad",
                )
                assert isinstance(value, float)

    def test_shareholders(self):
        shareholders = self.reader.shareholders()
        for shareholder in shareholders:
            assert isinstance(shareholder["company"], str)
            assert isinstance(shareholder["shares"], int)
            assert isinstance(shareholder["percentage"], float)