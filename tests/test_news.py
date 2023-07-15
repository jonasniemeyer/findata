from findata import (
    EconomistNews,
    FTNews,
    NasdaqNews,
    SANews,
    WSJNews
)
import pandas as pd
from pandas.tseries.offsets import DateOffset
import re

NoneType = type(None)
last_month = (pd.to_datetime("today") - DateOffset(months=1)).date()


def test_economist_news():
    for section in EconomistNews.sections:
        start = last_month
        articles = []
        while len(articles) == 0:
            articles = EconomistNews.articles(section=section, start=start.isoformat())
            start = start - DateOffset(months=1)
        assert isinstance(articles, list)
        assert len(articles) != 0

        for article in articles:
            assert isinstance(article["title"], str)
            assert isinstance(article["description"], (str, NoneType))
            assert article["date"] is None or len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", article["date"])) == 1
            assert isinstance(article["url"], str)
    
    articles = EconomistNews.articles(section="Europe", start=last_month.isoformat(), timestamps=True)
    assert len(articles) != 0
    for article in articles:
        assert isinstance(article["date"], (int, NoneType))


def test_ft_news():
    for sections in (
        FTNews.world_sections,
        FTNews.companies_sections,
        FTNews.markets_sections,
        FTNews.career_sections,
        FTNews.life_sections,
        FTNews.opinions,
        FTNews.columnists
    ):
        for section in sections:
            start = last_month
            articles = []
            while len(articles) == 0:
                articles = FTNews.articles(section=section, start=start.isoformat())
                start = start - DateOffset(months=1)
            assert isinstance(articles, list)
            assert len(articles) != 0

            for article in articles:
                assert isinstance(article["title"], str)
                assert isinstance(article["category"], (str, NoneType))
                assert isinstance(article["description"], (str, NoneType))
                assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}", article["datetime"])) == 1
                assert isinstance(article["url"], str)

    articles = FTNews.articles(section="Tech Sector", start=last_month.isoformat(), timestamps=True)
    assert len(articles) != 0
    for article in articles:
        assert isinstance(article["datetime"], int)


def test_nasdaq_news():
    articles = NasdaqNews.rss_feed("AAPL")
    assert isinstance(articles, list)
    assert len(articles) != 0

    for article in articles:
        assert isinstance(article["header"], str)
        assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}", article["datetime"])) == 1
        assert isinstance(article["source"], str)
        assert isinstance(article["categories"], list)
        for category in article["categories"]:
            assert isinstance(category, str)
        assert isinstance(article["related_tickers"], list)
        for ticker in article["related_tickers"]:
            assert isinstance(ticker, str)
        assert isinstance(article["url"], str)
    
    articles = NasdaqNews.rss_feed("AAPL", timestamps=True)
    assert len(articles) != 0
    for article in articles:
        assert isinstance(article["datetime"], int)


def test_sa_rss():
    articles = SANews.rss_feed("AAPL")
    assert isinstance(articles, list)
    assert len(articles) != 0

    for article in articles:
        assert isinstance(article["header"], str)
        assert isinstance(article["url"], str)
        assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}", article["datetime"])) == 1
        assert isinstance(article["author"], str)
        assert isinstance(article["type"], str)


def test_nasdaq_rss():
    articles = NasdaqNews.rss_feed("AAPL", timestamps=True)
    assert len(articles) != 0
    for article in articles:
        assert isinstance(article["datetime"], int)


def test_wsj_news():
    for sections in (
        WSJNews.world_sections,
        WSJNews.us_sections,
        WSJNews.business_sections,
        WSJNews.markets_sections,
        WSJNews.opinions,
        WSJNews.books_art_sections,
        WSJNews.life_work_sections,
        WSJNews.style_sections,
        WSJNews.sports_sections,
        WSJNews.columns,
        WSJNews.reviews
    ):
        for section in sections:
            start = last_month
            articles = []
            while len(articles) == 0:
                articles = WSJNews.articles(section=section, start=start.isoformat())
                start = start - DateOffset(months=1)
            assert isinstance(articles, list)
            assert len(articles) != 0

            for article in articles:
                assert isinstance(article["title"], str)
                assert isinstance(article["authors"], list)
                for author in article["authors"]:
                    assert isinstance(author, str)
                assert isinstance(article["category"], (str, NoneType))
                assert isinstance(article["summary"], str)
                assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", article["date"])) == 1
                assert isinstance(article["url"], str)

    articles = WSJNews.articles(section="Europe", start=last_month.isoformat(), timestamps=True)
    assert len(articles) != 0
    for article in articles:
        assert isinstance(article["date"], int)


def test_wsj_rss():
    for section in WSJNews.rss_sections:
        articles = WSJNews.rss_feed(section=section)
        assert isinstance(articles, list)
        assert len(articles) != 0
        
        for article in articles:
            assert isinstance(article["header"], str)
            assert isinstance(article["url"], str)
            assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}", article["datetime"])) == 1
        
    articles = WSJNews.rss_feed(section="World", timestamps=True)
    assert len(articles) != 0
    for article in articles:
        assert isinstance(article["datetime"], int)