from findata import TipranksStockReader
import datetime as dt

NoneType = type(None)


def test_trending_stocks():
    data = TipranksStockReader.trending_stocks()
    assert isinstance(data, list)
    for item in data:
        assert isinstance(item["ticker"], str)
        assert isinstance(item["popularity"], int)
        assert isinstance(item["sentiment"], int)
        assert round(item["consensus_score"], 2) == item["consensus_score"]
        assert isinstance(item["sector"], str)
        assert isinstance(item["market_cap"], (int, NoneType))
        assert isinstance(item["buy"], int)
        assert isinstance(item["hold"], int)
        assert isinstance(item["sell"], int)
        assert isinstance(item["consensus_rating"], int)
        assert isinstance(item["price_target"], float)
        assert dt.date.fromisoformat(item["latest_rating"])

    data = TipranksStockReader.trending_stocks(timestamps=True)
    for item in data:
        assert isinstance(item["latest_rating"], int)


def test_news_sentiment():
    data = TipranksStockReader("AAPL").news_sentiment()
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
        assert isinstance(item["hold"], int)
        assert isinstance(item["sell"], int)
        assert isinstance(item["average"], float)
        assert isinstance(item["count"], int)
    
    data = TipranksStockReader("AAPL").news_sentiment(timestamps=True)
    for item in data["articles"]:
        assert isinstance(item["week"], int)


class TestRatingData:
    @classmethod
    def setup_class(cls):
        cls.reader = TipranksStockReader("AAPL")
    
    def test_isin(self):
        isin = self.reader.isin
        assert isinstance(isin, str)
    
    def test_blogger_sentiment(self):
        data = self.reader.blogger_sentiment()
        assert isinstance(data["positive"], int)
        assert isinstance(data["neutral"], int)
        assert isinstance(data["negative"], int)
        assert round(data["average"], 2) == data["average"]
    
    def test_covering_analysts(self):
        data = self.reader.covering_analysts()
        assert isinstance(data, list)
        for item in data:
            assert isinstance(item["name"], (str, NoneType))
            assert isinstance(item["company"], str)
            assert isinstance(item["image_url"], (str, NoneType))
            assert round(item["success_rate_stock"], 4) == item["success_rate_stock"]
            assert round(item["average_rating_return_stock"], 4) == item["average_rating_return_stock"]
            assert isinstance(item["total_recommendations_stock"], int)
            assert isinstance(item["successful_recommendations_stock"], int)
            assert isinstance(item["consensus_analyst"], bool)
            assert isinstance(item["ratings"], list)
            assert len(item["ratings"]) == 1
            assert dt.date.fromisoformat(item["ratings"][0]["date"])
            assert isinstance(item["ratings"][0]["news_url"], (str, NoneType))
            assert isinstance(item["ratings"][0]["news_title"], (str, NoneType))
            assert isinstance(item["analyst_ranking"], dict)
            assert isinstance(item["analyst_ranking"]["rank"], int)
            assert isinstance(item["analyst_ranking"]["successful_recommendations"], int)
            assert isinstance(item["analyst_ranking"]["total_recommendations"], int)
            assert round(item["analyst_ranking"]["success_rate"], 4) == item["analyst_ranking"]["success_rate"]
            assert round(item["analyst_ranking"]["average_rating_return"], 4) == item["analyst_ranking"]["average_rating_return"]
            assert round(item["analyst_ranking"]["stars"], 1) == item["analyst_ranking"]["stars"]
        
        for key in (
            "name",
            "company",
            "success_rate_stock",
            "average_rating_return_stock",
            "total_recommendations_stock",
            "successful_recommendations_stock",
            "price_target",
            "rank",
            "successful_recommendations",
            "total_recommendations",
            "average_rating_return",
            "stars",
        ):
            assert self.reader.covering_analysts(sorted_by=key)
    
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
            assert round(item["amount"], 2) == item["amount"]
            assert isinstance(item["shares"], int)
            assert dt.date.fromisoformat(item["report_date"])
            assert isinstance(item["file_url"], str)
            assert isinstance(item["image_url"], (str, NoneType))
        assert round(data["insider_trades_last_3_months"], 2) == data["insider_trades_last_3_months"]

        data = self.reader.insider_trades(timestamps=True)
        for item in data["insiders"]:
            assert isinstance(item["report_date"], int)
        
        for key in ("name", "amount", "shares", "report_date"):
            assert self.reader.insider_trades(sorted_by=key)
    
    def test_institutional_ownership(self):
        data = self.reader.institutional_ownership()
        assert isinstance(data, list)
        for item in data:
            assert isinstance(item["name"], str)
            assert isinstance(item["company"], str)
            assert round(item["stars"], 1) == item["stars"]
            assert isinstance(item["rank"], int)
            assert isinstance(item["ranked_institutions"], int)
            assert isinstance(item["value"], int)
            assert round(item["change"], 4) == item["change"]
            assert round(item["percentage_of_portfolio"], 4) == item["percentage_of_portfolio"]
            assert isinstance(item["image_url"], (str, NoneType))
        
        for key in ("name", "company", "stars", "rank", "value", "percentage_of_portfolio"):
            assert self.reader.institutional_ownership(sorted_by=key)
    
    def test_institutional_ownership_trend(self):
        data = self.reader.institutional_ownership_trend()
        assert isinstance(data, dict)
        for key in data:
            assert isinstance(key, str)
            assert isinstance(data[key], int)
        
        data = self.reader.institutional_ownership_trend(timestamps=True)
        for key in data:
            assert isinstance(key, int)
    
    def test_peers(self):
        data = self.reader.peers()
        for item in data:
            assert isinstance(item["ticker"], str)
            assert isinstance(item["name"], str)
            assert isinstance(item["buy"], int)
            assert isinstance(item["hold"], int)
            assert isinstance(item["sell"], int)
            assert item["average"] is None or round(item["average"], 2) == item["average"] 
            assert item["average_price_target"] is None or round(item["average_price_target"], 2) == item["average_price_target"]
    
    def test_profile(self):
        data = self.reader.profile()
        assert isinstance(data["isin"], str)
        assert isinstance(data["description"], str)
        assert isinstance(data["industry"], str)
        assert isinstance(data["sector"], str)
        assert isinstance(data["ceo"], str)
        assert isinstance(data["employees"], int)
        assert isinstance(data["website"], str)
        assert isinstance(data["address"], str)
    
    def test_recommendation_trend(self):
        data = self.reader.recommendation_trend()
        assert isinstance(data, dict)
        for key in ("all_analysts", "best_analysts"):
            for date in data[key]:
                assert dt.date.fromisoformat(date)
                assert isinstance(date, str)
                assert isinstance(data[key][date]["consensus_rating"], int)
                assert isinstance(data[key][date]["buy"], int)
                assert isinstance(data[key][date]["hold"], int)
                assert isinstance(data[key][date]["sell"], int)
                assert round(data[key][date]["average"], 2) == data[key][date]["average"]
                assert round(data[key][date]["average_price_target"], 2) == data[key][date]["average_price_target"]
        
        data = self.reader.recommendation_trend(timestamps=True)
        for key in ("all_analysts", "best_analysts"):
            for date in data[key]:
                assert isinstance(date, int)
    
    def test_recommendation_trend_breakup(self):
        data = self.reader.recommendation_trend_breakup()
        for star in data:
            if star != "all":
                assert 1 <= star <= 5 and isinstance(star, int)
            for date in data[star]:
                assert dt.date.fromisoformat(date)
                assert isinstance(data[star][date]["buy"], int)
                assert isinstance(data[star][date]["hold"], int)
                assert isinstance(data[star][date]["sell"], int)
                assert data[star][date]["average"] is None or round(data[star][date]["average"], 2) == data[star][date]["average"]
        
        data = self.reader.recommendation_trend_breakup(timestamps=True)
        for star in data:
            for date in data[star]:
                assert isinstance(date, int)
        
        data = self.reader.recommendation_trend_breakup(sorted_by="date")
        for date in data:
            assert dt.date.fromisoformat(date)
            for star in data[date]:
                if star != "all":
                    assert 1 <= star <= 5 and isinstance(star, int)
        
        data = self.reader.recommendation_trend_breakup(sorted_by="date", timestamps=True)
        for date in data:
            assert isinstance(date, int)