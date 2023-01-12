import re
from finance_data import (
    EconomistNews,
    FTNews,
    NasdaqNews,
    SANews,
    WSJNews
)

NoneType = type(None)

def test_economist_news():
    for section in EconomistNews.sections:
        articles = EconomistNews.articles(section=section, start="2023-01-01")
        if len(articles) == 0:
            articles = EconomistNews.articles(section=section, start="2022-01-01")
            if len(articles) == 0:
                articles = EconomistNews.articles(section=section, start="2021-01-01")
        assert isinstance(articles, list)
        assert len(articles) != 0

        for article in articles:
            assert isinstance(article["title"], str)
            assert isinstance(article["description"], (str, NoneType))
            assert article["date"] is None or len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", article["date"])) == 1
            assert isinstance(article["url"], str)
    
    articles = EconomistNews.articles(section="Europe", start="2023-01-01", timestamps=True)
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
            articles = FTNews.articles(section=section, start="2023-01-01")
            if len(articles) == 0:
                articles = FTNews.articles(section=section, start="2022-01-01")
                if len(articles) == 0:
                    articles = FTNews.articles(section=section, start="2021-01-01")
            assert isinstance(articles, list)
            assert len(articles) != 0

            for article in articles:
                assert isinstance(article["title"], str)
                assert isinstance(article["category"], (str, NoneType))
                assert isinstance(article["description"], (str, NoneType))
                assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}", article["datetime"])) == 1
                assert isinstance(article["url"], str)

    articles = FTNews.articles(section="Tech Sector", start="2023-01-01", timestamps=True)
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

def test_sa_news():
    articles = SANews.rss_feed("AAPL")
    assert isinstance(articles, list)
    assert len(articles) != 0

    for article in articles:
        assert isinstance(article["header"], str)
        assert isinstance(article["url"], str)
        assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}", article["datetime"])) == 1
        assert isinstance(article["author"], str)
        assert isinstance(article["type"], str)

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
            articles = WSJNews.articles(section=section, start="2023-01-01")
            if len(articles) == 0:
                articles = WSJNews.articles(section=section, start="2022-01-01")
                if len(articles) == 0:
                    articles = WSJNews.articles(section=section, start="2021-01-01")
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

    articles = WSJNews.articles(section="Europe", start="2023-01-01", timestamps=True)
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