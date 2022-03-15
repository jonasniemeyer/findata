from finance_data import TipranksReader
import datetime as dt

def test_trending_stocks():
    data = TipranksReader.trending_stocks()
    assert isinstance(data, list)
    for item in data:
        assert isinstance(item["ticker"], str)
        assert isinstance(item["popularity"], int)
        assert isinstance(item["sentiment"], int)
        assert isinstance(item["consensus_score"], float)
        assert isinstance(item["sector"], str)
        assert isinstance(item["market_cap"], int)
        assert isinstance(item["buy"], int)
        assert isinstance(item["hold"], int)
        assert isinstance(item["sell"], int)
        assert isinstance(item["consensus_rating"], int)
        assert isinstance(item["price_target"], float)
        assert dt.date.fromisoformat(item["latest_rating"])

    data = TipranksReader.trending_stocks(timestamps=True)
    for item in data:
        assert isinstance(item["latest_rating"], int)

def test_news_sentiment():
    data = TipranksReader("AAPL").news_sentiment()
    assert isinstance(data, dict)
    assert isinstance(data["articles_last_week"], int)
    assert isinstance(data["average_weekly_articles"], float)
    assert isinstance(data["positive_percent"], float)
    assert isinstance(data["negative_percent"], float)
    assert isinstance(data["sector_sentiment"], list)
    for item in data["sector_sentiment"]:
        assert isinstance(item["ticker"], str)
        assert isinstance(item["name"], str)
        assert isinstance(item["positive_percent"], float)
        assert isinstance(item["negative_percent"], float)
    assert isinstance(data["sector_average_sentiment"], float)
    assert isinstance(data["news_score"], float)
    assert isinstance(data["articles"], list)
    for item in data["articles"]:
        assert isinstance(item["week"], str)
        assert isinstance(item["buy"], int)
        assert isinstance(item["neutral"], int)
        assert isinstance(item["sell"], int)
        assert isinstance(item["total"], int)
    
    data = TipranksReader("AAPL").news_sentiment(timestamps=True)
    for item in data["articles"]:
        assert isinstance(item["week"], int)

class TestRatingData:
    @classmethod
    def setup_class(cls):
        cls.reader = TipranksReader("AAPL")
    
    def test_isin(self):
        isin = self.reader.isin
        assert isinstance(isin, str)
    
    def test_blogger_sentiment(self):
        data = self.reader.blogger_sentiment()
        assert isinstance(data["positive"], int)
        assert isinstance(data["neutral"], int)
        assert isinstance(data["negative"], int)
        assert isinstance(data["average"], float)
    
    def test_covering_analysts(self):
        data = self.reader.covering_analysts()
        assert isinstance(data, list)
        for item in data:
            assert isinstance(item["name"], str)
            assert isinstance(item["firm"], str)
            assert isinstance(item["image_url"], str)
            assert isinstance(item["stock_success_rate"], float)
            assert isinstance(item["average_rating_return"], float)
            assert isinstance(item["total_recommendations"], int)
            assert isinstance(item["positive_recommendations"], int)
            assert isinstance(item["consensus_analyst"], bool)
            assert isinstance(item["ratings"], list)
            assert len(item["ratings"]) == 1
            assert isinstance(item["ratings"][0]["date"], str)
            assert isinstance(item["ratings"][0]["news_url"], str)
            assert isinstance(item["ratings"][0]["news_title"], str)
            assert isinstance(item["analyst_ranking"], dict)
            assert isinstance(item["analyst_ranking"]["rank"], int)
            assert isinstance(item["analyst_ranking"]["successful_recommendations"], int)
            assert isinstance(item["analyst_ranking"]["total_recommendations"], int)
            assert isinstance(item["analyst_ranking"]["average_rating_return"], float)
            assert isinstance(item["analyst_ranking"]["stars"], float)

