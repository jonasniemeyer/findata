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
        articles = EconomistNews.articles(section=section, start="2022-01-01")
        assert isinstance(articles, list)
        assert len(articles) != 0

        for article in articles:
            assert isinstance(article["title"], str)
            assert isinstance(article["description"], str)
            assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}", article["datetime"])) == 1
            assert isinstance(article["url"], str)
    
    articles = EconomistNews(section="Europe", start="2023-01-01", timestamps=True)
    assert len(articles) != 0
    for article in articles:
        assert isinstance(article["datetime"], int)

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
            articles = FTNews.articles(section=section, start="2022-01-01")
            assert isinstance(articles, list)
            assert len(articles) != 0

            for article in articles:
                assert isinstance(article["header"], str)
                assert isinstance(article["url"], str)
                assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}", article["datetime"])) == 1
                assert isinstance(article["author"], str)
                assert isinstance(article["type"], str)

    articles = FTNews.articles(section="Tech Sector", start="2023-01-01", timestamps=True)
    assert len(articles) != 0
    for article in articles:
        assert isinstance(article["datetime"], int)