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
            assert (isinstance(item["image_url"], str) or item["image_url"] is None)
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
    
    def test_insider_trades(self):
        data = self.reader.insider_trades()
        assert isinstance(data, dict)
        assert isinstance(data["insiders"], list)
        for item in data["insiders"]:
            assert isinstance(item["name"], str)
            assert isinstance(item["company"], str)
            assert isinstance(item["officer"], bool)
            assert isinstance(item["director"], bool)
            assert isinstance(item["title"], str)
            assert isinstance(item["amount"], float)
            assert isinstance(item["shares"], int)
            assert isinstance(item["form_type"], int)
            assert isinstance(item["report_date"], str)
            assert isinstance(item["file_url"], str)
            assert (isinstance(item["image_url"], str) or item["image_url"] is None)
        assert isinstance(data["insider_trades_last_3_months"], float)

        data = self.reader.insider_trades(timestamps=True)
        for item in data["insiders"]:
            assert isinstance(item["report_date"], int)

    def test_institutional_ownership(self):
        data = self.reader.institutional_ownership()
        assert isinstance(data, list)
        for item in data:
            assert isinstance(item["name"], str)
            assert isinstance(item["firm"], str)
            assert isinstance(item["stars"], float)
            assert round(item["stars"], 4) == item["stars"]
            assert isinstance(item["rank"], int)
            assert isinstance(item["ranked_institutions"], int)
            assert isinstance(item["value"], int)
            assert isinstance(item["change"], float)
            assert isinstance(item["percentage_of_portfolio"], float)
            assert round(item["percentage_of_portfolio"], 4) == item["percentage_of_portfolio"]
            assert (isinstance(item["image_url"], str) or item["image_url"] is None) 
    
    def test_institutional_ownership_trend(self):
        data = self.reader.institutional_ownership_trend()
        assert isinstance(data, dict)
        for key in data:
            assert isinstance(key, str)
            assert isinstance(data[key], int)
        
        data = self.reader.institutional_ownership_trend(timestamps=True)
        for key in data:
            assert isinstance(key, int)
    
    def test_recommendation_trend(self):
        data = self.reader.recommendation_trend()
        assert isinstance(data, dict)
        for key in ("all", "best"):
            for date in data[key]:
                assert isinstance(date, str)
                assert isinstance(data[key][date]["consensus_rating"], int)
                assert isinstance(data[key][date]["buy"], int)
                assert isinstance(data[key][date]["hold"], int)
                assert isinstance(data[key][date]["sell"], int)
                assert isinstance(data[key][date]["average"], float)
                assert isinstance(data[key][date]["average_price_target"], float)
        



