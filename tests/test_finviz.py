from finance_data import FinvizReader

class TestMethods:
    @classmethod
    def setup_class(cls):
        cls.reader = FinvizReader("AAPL")

    def test_analyst_recommendations(self):
        recommendations = self.reader.analyst_recommendations()
        for item in recommendations:
            assert isinstance(item["date"], str)
            assert isinstance(item["company"], str)
            assert isinstance(item["change"], str)
            assert item["rating_old"] is None or isinstance(item["rating_old"], str)
            assert isinstance(item["rating_new"], str)
            assert item["price_old"] is None or round(item["price_old"], 2) == item["price_old"]
            assert round(item["price_new"], 2) == item["price_new"]
            if item["change"] == "Reiterated":
                assert item["rating_old"] == item["rating_new"]
        
        recommendations = self.reader.analyst_recommendations(timestamps=True)
        for item in recommendations:
            assert isinstance(item["date"], int)

    def test_insider_trades(self):
        trades = self.reader.insider_trades()
        for item in trades:
            assert isinstance(item["name"], str)
            assert isinstance(item["position"], str)
            assert isinstance(item["date"], str)
            assert isinstance(item["transaction"], str)
            assert isinstance(item["shares"], int)
            assert isinstance(item["value"], int)
            assert round(item["price"], 2) == item["price"]
            assert isinstance(item["url"], str)

    def test_news(self):
        news = self.reader.news()
        for item in news:
            assert isinstance(item["date"], str)
            assert isinstance(item["source"], str)
            assert isinstance(item["title"], str)
            assert isinstance(item["url"], str)
        
        news = self.reader.news(timestamps=True)
        for item in news:
            assert isinstance(item["date"], int)