import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
from .utils import HEADERS, DatasetError


class EconomistNews:
    _base_url = "https://www.economist.com"
    
    sections = {
        "Leaders": "leaders",
        "Letters": "letters",
        "Briefing": "briefing",
        "United States": "united-states",
        "Americas": "the-americas",
        "Asia": "asia",
        "China": "china",
        "Middle East & Africa": "middle-east-and-africa",
        "Europe": "europe",
        "Britain": "britain",
        "International": "international",
        "Business": "business",
        "Finance & Economics": "finance-and-economics",
        "Science & Technology": "science-and-technology",
        "Culture": "culture",
        "Graphic Detail": "graphic-detail",
        "Obituary": "obituary",
        "Essay": "essay",
        "By Invitation": "by-invitation",
        "Schools Brief": "schools-brief",
        "The Economist Explains": "the-economist-explains",
        "The Economist Reads": "the-economist-reads"
    }
    
    @classmethod
    def articles(
        cls,
        section,
        start=pd.to_datetime("today").date().isoformat(),
        timestamps=False
    ) -> list:
        if isinstance(start, str):
            start = pd.to_datetime(start).timestamp()
        elif not isinstance(start, (int, float)):
            raise ValueError("start parameter has to be of type str, float or int")
        
        articles = []
        start_reached = False
        page_counter = 0
        
        if section in cls.sections:
            section = cls.sections[section]
        
        while start_reached is False:
            page_counter+=1
            url = f"{cls._base_url}/{section}?page={page_counter}"
            response = requests.get(url=url, headers=HEADERS)
            
            if int(response.url.split("page=")[1]) != page_counter:
                break
            
            html = response.text
            soup = BeautifulSoup(html, "lxml")
            
            try:
                div = soup.find_all("div", {"class": "layout-section-collection ds-layout-grid"})[0]
                tags = div.find_all("div", {"class": "css-e6sfh4 e1mrg8dy0"}, recursive=False)
            except IndexError:
                raise DatasetError(f"No articles found for section '{section}'")
            assert len(tags) != 0
            
            for tag in tags:
                tag = tag.find_all("div", recursive=False)[0]
                url = tag.find("h3", recursive=False).find("a").get("href")
                url = f"{cls._base_url}{url}"
                
                date = re.findall("[0-9]{4}/[0-9]{2}/[0-9]{2}", url)
                if date == []:
                    date = None
                else:
                    date = pd.to_datetime(date[0])
                    if date.timestamp() < start:
                        start_reached = True
                        break

                    if timestamps:
                        date = int(date.timestamp())
                    else:
                        date = date.date().isoformat()
                
                title = tag.find("h3", recursive=False).find("a").text
                description = tag.find_all("p", recursive=False)
                if description == []:
                    description = None
                else:
                    description = description[0].text

                article = {
                    "title": title,
                    "description": description,
                    "date": date,
                    "url": url
                }

                articles.append(article)
        return articles


class FTNews:
    _base_url = "https://www.ft.com"

    world_sections = {
        "World": "world",
        "Global Economy": "global-economy",
        "UK": "world/uk",
        "UK Business & Ecomnomy": "uk-business-economy",
        "UK Politics & Policy": "world/uk/politics",
        "Brexit": "brexit",
        "UK Companies": "companies/uk",
        "Personal Finance": "personal-finance",
        "US": "world/us",
        "US Economy": "us-economy",
        "US Companies": "companies/us",
        "US Politics & Policy": "world/us/politics",
        "China": "world/asia-pacific/china",
        "Chinese Economy": "chinese-economy",
        "China Politics & policy": "chinese-politics-policy",
        "Africa": "world/africa",
        "Asia Pacific": "world/asia-pacific",
        "Emerging Markets": "emerging-markets",
        "Europe": "world/europe",
        "War In Ukraine": "war-in-ukraine",
        "Americas": "world/americas",
        "Middle East & North Africa": "world/mideast",
        "Australia & NZ": "australia-newzealand",
        "Climate": "climate-capital"
    }
    
    companies_sections = {
        "Companies": "companies",
        "Energy": "companies/energy",
        "Mining": "companies/mining",
        "Oil & Gas": "companies/oil-gas",
        "Utilities": "companies/utilities",
        "Energy Source": "energy-source",
        "Financials": "companies/financials",
        "Banks": "banks",
        "Insurance": "companies/insurance",
        "Property": "companies/property",
        "Financial Services": "companies/financial-services",
        "Health": "companies/health",
        "Health Care": "companies/health-care",
        "Pharmaceuticals": "companies/pharmaceuticals",
        "Industrials": "companies/industrials",
        "Aerospace & Defence": "companies/aerospace-defence",
        "Automobiles": "companies/automobiles",
        "Basic Resources": "companies/basic-resources",
        "Chemicals": "companies/chemicals",
        "Construction": "companies/construction",
        "Industrial Goods": "companies/industrial-goods",
        "Support Services": "support-services",
        "Media": "companies/media",
        "Professional Services": "companies/professional-services",
        "Accounting & Consulting Services": "accounting-consulting-services",
        "Legal Services": "companies/legal-services",
        "Recruitment Services": "companies/recruitment-services",
        "Retail & Consumer": "companies/retail-consumer",
        "Food & Beverage": "food-beverage",
        "Luxury Goods": "companies/luxury-goods",
        "Personal & Household Goods": "companies/personal-goods",
        "Retail": "retail",
        "Tobacco": "companies/tobacco",
        "Travel & Leisure": "companies/travel-leisure",
        "Tech Sector": "companies/technology",
        "Telecoms": "companies/telecoms",
        "Transport": "companies/transport",
        "Airlines": "companies/airlines",
        "Shipping": "shipping",
        "Rail": "companies/rail",
        
        "Tech": "technology"
    }
    
    markets_sections = {
        "Markets": "markets",
        "Alphaville": "alphaville",
        "Cryptofinance": "cryptofinance",
        "Capital Markets": "capital-markets",
        "Commodities": "commodities",
        "Oil": "oil",
        "Gold": "gold",
        "Copper": "copper",
        "Currencies": "currencies",
        "US Dollar": "us-dollar",
        "Euro": "euro",
        "Pound Sterling": "pound-sterling",
        "Renminbi": "renminbi",
        "Yen": "yen",
        "Equities": "equities",
        "US Equities": "us-equities",
        "UK Equities": "uk-equities",
        "European Equities": "european-equities",
        "Asia-Pacific Equities": "asia-pacific-equities",
        "Fund Management": "fund-management",
        "FTfm": "ftfm",
        "Funds Regulation": "fund-regulation",
        "Pensions Industry": "pensions-industry",
        "Trading": "ft-trading-room",
        "Clearing & Settlement": "ft-trading-room/clearing-settlement",
        "High Frequency Trading": "ft-trading-room/high-frequency-trading",
        "Markets Regulation": "financial-markets-regulation",
        "OTC Markets": "otc-markets",
        "Derivatives": "derivatives",
        "Moral Money": "moral-money",
    }
    
    career_sections = {
        "Work & Careers": "work-careers",
        "Business Education": "business-education",
        "Entrepreneurship": "entrepreneurship",
        "Recruitment": "recruitment",
        "Business Books": "business-books",
        "Business Travel": "business-travel",
    }
    
    life_sections = {
        "Arts": "arts",
        "Architecture": "architecture",
        "Collecting": "collecting",
        "Dance": "dance",
        "Design": "design",
        "Film": "film",
        "Music": "music",
        "Television": "television",
        "Theatre": "theatre",
        "Visual Arts": "visual-arts",
        "Books": "books",
        "Business Books": "business-books",
        "Fiction": "fiction",
        "Non-Fiction": "non-fiction",
        "Food & Drink": "food-drink",
        "Wine": "wine",
        "Recipes": "recipes",
        "Restaurants": "restaurants",
        "FT Magazine": "magazine",
        "House & Home": "house-home",
        "Style": "style",
        "Fashion shows": "fashion-shows",
        "Travel": "travel",
        "Adventure Holidays": "adventure-holidays",
        "Cycling Holidays": "cycling-holidays",
        "City Breaks": "city-breaks",
        "Winter Sports": "winter-sports"
    }

    opinions = {
        "Opinion": "opinion",
        "The FT View": "ft-view",
        "The Big Read": "the-big-read",
        "Lex": "lex",
        "Obituaries": "obituaries",
        "Letters": "letters",

        "HTSI": "htsi"
    }

    columnists = {
        "Martin Wolf": "martin-wolf",
        "GIllian Tett": "gillian-tett",
        "Rana Foroohar": "rana-foroohar",
        "Robert Shrimsley": "robert-shrimsley",
        "Gideon Rachman": "gideon-rachman",
        "Camilla Cavendish": "camilla-cavendish",
        "Brooke Masters": "brooke-masters",
        "Janan Ganesh": "janan-ganesh",
        "Martin Sandbu": "martin-sandbu",
        "Sarah O'Connor": "sarah-o-connor",
        "Philip Stephens": "philip-stephens",
        "Merryn Somerset Webb": "merryn-somerset-webb",
        "Anjana Ahuja": "anjana-ahuja",
        "Pilita Clark": "pilita-clark",
        "Gavyn Davies": "gavyn-davies",
        "John Gapper": "john-gapper",
        "David Gardner": "david-gardner",
        "Chris Giles": "chris-giles",
        "Miranda Green": "miranda-green",
        "Andrew Hill": "andrew-hill",
        "Izabella Kaminska": "izabella-kaminska",
        "Amy Kazmin": "amy-kazmin",
        "James Kynge": "james-kynge",
        "Jemina Kelly": "jemima-kelly",
        "Leo Lewis": "leo-lewis",
        "Edward Luce": "edward-luce",
        "Sebastian Payne": "sebastian-payne",
        "David Pilling": "david-pilling",
        "John Thornhill": "john-thornhill",
        "Courtney Weaver": "courtney-weaver",

        "Oren Cass": "oren-cass",
        "Mohamed El-Erian": "mohamed-el-erian",
        "Megan Greene": "megan-greene",
        "Raghuram Rajan": "raghuram-rajan",
        "Marietje Schaake": "stream/867c0293-af3e-42d2-834f-19fb5af684bb",
        "Ruchir Sharma": "ruchir-sharma",
        "Anne Marie Slaughter": "anne-marie-slaughter",
        "Constanze Stelzenmuller": "constanze-stelzenmüller",
        "Patti Waldmeir": "patti-waldmeir"
    }
    
    @classmethod
    def articles(
        cls,
        section,
        start=pd.to_datetime("today").date().isoformat(),
        timestamps=False
    ) -> list:
        if isinstance(start, str):
            start = pd.to_datetime(start).timestamp()
        elif not isinstance(start, (int, float)):
            raise ValueError("start parameter has to be of type str, float or int")
        
        articles = []
        start_reached = False
        page_counter = 0
        
        if section in cls.world_sections:
            section = cls.world_sections[section]
        elif section in cls.companies_sections:
            section = cls.companies_sections[section]
        elif section in cls.markets_sections:
            section = cls.markets_sections[section]
        elif section in cls.career_sections:
            section = cls.career_sections[section]
        elif section in cls.life_sections:
            section = cls.life_sections[section]
        elif section in cls.opinions:
            section = cls.opinions[section]
        elif section in cls.columnists:
            section = cls.columnists[section]
        
        while start_reached is False:
            page_counter+=1
            if page_counter == 201:
                break
            url = f"{cls._base_url}/{section}?page={page_counter}"
            html = requests.get(url=url, headers=HEADERS).text
            soup = BeautifulSoup(html, "lxml")
            try:
                tags = soup.find_all("ul", {"class": "o-teaser-collection__list js-stream-list"})[0].find_all("li")
            except IndexError:
                raise DatasetError(f"No articles found for section '{section}'")
            assert len(tags) != 0
            
            for tag in tags:
                datetime = tag.find_all("div", recursive=False)[0].find_all("div", recursive=False)
                if datetime == []:
                    continue
                else:
                    datetime = datetime[0].find("time").get("datetime")
                    if pd.to_datetime(datetime).timestamp() < start:
                        start_reached = True
                        break

                if timestamps:
                    datetime = int(pd.to_datetime(datetime).timestamp())

                content = tag.find_all("div", recursive=False)[1].find_all("div", recursive=False)[0].find_all("div", recursive=False)[0].find_all("div", recursive=False)[0]
                category = content.find("div", {"class": "o-teaser__meta"}).find("a")
                if category is not None:
                    category = category.text
                title = content.find("div", {"class": "o-teaser__heading"}).find("a").text
                path = content.find("div", {"class": "o-teaser__heading"}).find("a").get("href")
                description = content.find("p", {"class": "o-teaser__standfirst"})
                if description is not None:
                    description = description.find("a").text
                url = f"{cls._base_url}{path}"

                article = {
                    "title": title,
                    "category": category,
                    "description": description,
                    "datetime": datetime,
                    "url": url
                }

                articles.append(article)
        return articles


class NasdaqNews:
    @staticmethod
    def rss_feed(ticker, timestamps=False) -> list:
        url = f"https://www.nasdaq.com/feed/rssoutbound?symbol={ticker}"
        response = requests.get(url=url, headers=HEADERS).text
        soup = BeautifulSoup(response, "lxml")
        tags = soup.find_all("item")
        
        articles = []
        for tag in tags:
            header = tag.find("title").text.strip()
            description = tag.find("description").text.strip()
            datetime = pd.to_datetime(tag.find("pubdate").text)
            if timestamps:
                datetime = int(datetime.timestamp())
            else:
                datetime = datetime.isoformat()
            source = tag.find("dc:creator").text.strip()
            categories = tag.find("category").text
            categories = [category.strip() for category in categories.split(",")]
            related_tickers = tag.find("nasdaq:tickers")
            if related_tickers is None:
                related_tickers = []
            else:
                related_tickers = related_tickers.text.strip()
                related_tickers = [ticker.strip() for ticker in related_tickers.split(",")]
            url = tag.find("guid").text.strip()
            article = {
                "header": header,
                "datetime": datetime,
                "description": description,
                "source": source,
                "categories": categories,
                "related_tickers": related_tickers,
                "url": url
            }
            articles.append(article)
            
        return articles


class SANews:
    @staticmethod
    def rss_feed(ticker, timestamps=False) -> list:
        url = f"https://seekingalpha.com/api/sa/combined/{ticker}.xml"
        response = requests.get(url=url, headers=HEADERS).text
        soup = BeautifulSoup(response, "lxml")
        tags = soup.find_all("item")
        
        articles = []
        for tag in tags:
            header = tag.find("title").text
            url = tag.find("guid").text.replace("Article:", "article/").replace("MarketCurrent:", "news/")
            datetime = pd.to_datetime(tag.find("pubdate").text)
            if timestamps:
                datetime = int(datetime.timestamp())
            else:
                datetime = datetime.isoformat()
            author = tag.find("sa:author_name").text
            if "https://seekingalpha.com/news/" in url:
                type_ = "News"
            elif "https://seekingalpha.com/article/" in url:
                type_ = "Article"
            else:
                type_ = "Unclassified"
            article = {
                "header": header,
                "url": url,
                "datetime": datetime,
                "author": author,
                "type": type_
            }
            articles.append(article)
            
        return articles


class WSJNews:
    _base_url = "https://www.wsj.com/news/"
    
    world_sections = {
        "Africa": "types/africa-news",
        "Asia": "types/asia-news",
        "Canada": "types/canada-news",
        "China": "types/china-news",
        "Europe": "types/europe-news",
        "Latin America": "types/latin-america-news",
        "Middle East": "types/middle-east-news"
    }
    
    us_sections = {
        "Capital Account": "types/capital-account"
    }
    
    business_sections = {
        "Aerospace & Defense": "business/defense-aerospace",
        "Autos & Transportation": "business/transportation",
        "Consumer Products": "business/consumer-products",
        "Energy": "business/energy-oil-gas",
        "Entrepreneurship": "business/small-business-marketing",
        "Financial Services": "business/financial-services",
        "Food & Services": "business/food-tobacco",
        "Health Care": "business/health-industry",
        "Hospitality": "business/hotels-casinos",
        "Law": "business/law-legal",
        "Manufacturing": "business/industrial-services",
        "Media & Marketing": "business/media-marketing",
        "Natural Resources": "business/natural-resources",
        "Retail": "business/retail-industry",
        "Obituaries": "types/obituaries"
    }
    
    markets_sections = {
        "Personal Tech": "types/personal-technology-joanna-stern",
        "Bonds": "markets/bonds",
        "Commercial Real Estate": "markets/real-estate-commercial",
        "Commodities & Futures": "markets/oil-gold-commodities-futures",
        "Stocks": "markets/stocks",
        "Streetwise": "types/streetwise",
        "Intelligent Investor": "types/the-intelligent-investor"
    }
    
    opinions = {
        "Editorials": "types/review-outlook-u-s",
        "Commentary": "types/commentary-u-s",
        "Future View": "types/future-view",
        "Letters to the Editor": "types/letters",
        "The Weekend Interview": "types/the-saturday-interview",
        "Notable & Quotable": "types/notable-quotable",
    }
    
    books_art_sections = {
        "Arts": "books-arts/arts",
        "Books": "books-arts/books"
    }
    
    life_work_sections = {
        "Cars": "life-work/automotive",
        "Careers": "types/management-careers",
        "Food & Drink": "life-work/food-cooking-drink",
        "Home & Design": "types/design",
        "Ideas": "life-work/ideas",
        "Personal Finance": "types/personal-finance",
        "Travel": "life-work/travel",
        "Wellness": "life-work/health-wellness"
    }
    
    style_sections = {
        "Fashion": "style-entertainment/fashion",
        "Film": "types/film",
        "Television": "types/television",
        "Music": "types/music",
        "Art & Auctions": "types/art-auctions"
    }
    
    sports_sections= {
        "Beijing 2022 Olympics": "types/olympics",
        "MLB": "types/mlb",
        "NBA": "types/nba",
        "NFL": "types/nfl",
        "Golf": "types/sports-golf",
        "Tennis": "types/tennis",
        "Soccer": "types/soccer"
    }
    
    columns = {
        "Washington Wire": "types/washington-wire",

        "Christopher Mims": "author/christopher-mims",
        "Joanna Stern": "author/joanna-stern",
        "Julie Jargon": "author/julie-jargon",
        "Nicole Nguyen": "author/nicole-nguyen",

        "Greg Ip": "author/greg-ip",
        "Jason Zweig": "author/jason-zweig",
        "Laura Saunders": "author/laura-saunders",
        "James Mackintosh": "author/james-mackintosh",

        "Gerard Baker": "author/gerard-baker",
        "Sadanand Dhume": "author/sadanand-dhume",
        "James Freeman": "author/james-freeman",
        "William A. Galston": "author/william-a-galston",
        "Daniel Henninger": "author/daniel-henninger",
        "Holman W. Jenkins": "author/holman-w-jenkinsjr",
        "Andy Kessler": "author/andy-kessler",
        "William McGurn": "author/william-mcgurn",
        "Walter Russell Mead": "author/walter-russell-mead",
        "Peggy Noonan": "author/peggy-noonan",
        "Mary Anastasia O'Grady": "author/mary-anastasia-ogrady",
        "Jason Riley": "author/jason-l-riley",
        "Joseph Sternberg": "author/joseph-c-sternberg",
        "Kimberly A. Strassel": "author/kimberley-a-strassel",
        "Allysia Finley": "author/allysia-finley",

        "Your Health": "author/sumathi-reddy",
        "Work & Life": "author/rachel-feintzeig",
        "Carry On": "types/carry-on",
        "Bonding": "author/elizabeth-anne-bernstein",
        "Turning Points": "author/clare-ansberry",
        "On Wine": "author/lettie-teague",
        "On The Clock": "types/on-the-clock",

        "My Monday Morning": "types/my-monday-morning",
        "Off Brand": "author/rory-satran",
        "On Trend": "author/jacob-gallagher",

        "Jason Gay": "author/jason-gay"
    }

    reviews = {
        "Film": "types/film-review",
        "Television": "types/television-review",
        "Theater": "types/theater-review",
        "Masterpiece Series": "types/masterpiece",
        "Music": "types/music-review",
        "Dance": "types/dance-review",
        "Opera": "types/opera-review",
        "Exhibition": "types/exhibition-review",
        "Cultural Commentary": "types/cultural-commentary"
    }

    rss_sections = ("Opinion", "World", "U.S. Business", "Markets", "Technology", "Lifestyle")
        
    @classmethod
    def articles(
        cls,
        section,
        start=pd.to_datetime("today").date().isoformat(),
        timestamps=False
    ) -> list:
        if isinstance(start, str):
            start = pd.to_datetime(start).timestamp()
        elif not isinstance(start, (int, float)):
            raise ValueError("start parameter has to be of type str, float or int")
            
        articles = []
        start_reached = False
        page_counter = 0

        if section in cls.world_sections:
            key = cls.world_sections[section]
        elif section in cls.us_sections:
            key = cls.us_sections[section]
        elif section in cls.business_sections:
            key = cls.business_sections[section]
        elif section in cls.markets_sections:
            key = cls.markets_sections[section]
        elif section in cls.opinions:
            key = cls.opinions[section]
        elif section in cls.books_art_sections:
            key = cls.books_art_sections[section]
        elif section in cls.life_work_sections:
            key = cls.life_work_sections[section]
        elif section in cls.style_sections:
            key = cls.style_sections[section]
        elif section in cls.sports_sections:
            key = cls.sports_sections[section]
        elif section in cls.columns:
            key = cls.columns[section]
        elif section in cls.reviews:
            key = cls.reviews[section]
        else:
            key = section
        
        while start_reached is False:
            page_counter += 1
            url = f"{cls._base_url}{key}?page={page_counter}"

            retry = True
            while retry:
                html = requests.get(url=url, headers=HEADERS).text
                soup = BeautifulSoup(html, "lxml")

                tag_section = soup.find("div", {"id": "latest-stories"})
                if tag_section is None:
                    tag_section = soup.find("div", {"id": "author-articles"})
                if tag_section is None:
                    raise DatasetError(f"No articles found for section '{section}'")
                tags = tag_section.find_all("article")

                if len(tags) != 0:
                    retry = False
            
            for tag in tags:
                if len(tag.find_all("div", recursive=False)) == 2:
                    content = tag.find_all("div", recursive=False)[1]
                else:
                    content = tag.find_all("div", recursive=False)[0]
                
                if len(content.find_all("div", recursive=False)) == 2:
                    length = 2
                    category = None
                else:
                    length = 3
                    category = content.find_all("div", recursive=False)[0]
                    if category.find("ul") is not None:
                        category = category.find("ul").find("li").text
                    else:
                        category = category.find("span").text

                date = content.find_all("div", recursive="False")[length-1].find("div").find("p").text
                date = pd.to_datetime(date)
                if date.timestamp() < start:
                    start_reached = True
                    break
                
                if timestamps:
                    date = int(date.timestamp())
                else:
                    date = date.date().isoformat()
                    

                title = content.find_all("div", recursive=False)[length-2].find("h2").find("a")
                url = title.get("href")
                title = title.find("span").text
                summary = content.find("p").find("span")
                if summary is not None:
                    summary = summary.text
                authors = content.find_all("div", recursive=False)[length-1].find("p").text.split("|")[0].strip()
                authors = [author.strip() for author in authors.split("and")]

                article = {
                    "title": title,
                    "authors": authors,
                    "category": category,
                    "summary": summary,
                    "date": date,
                    "url": url
                }

                articles.append(article)
        
        return articles
    
    @classmethod
    def rss_feed(cls, section, timestamps=False):
        url = "https://feeds.a.dj.com/rss/{}.xml"
        if section not in cls.rss_sections:
            raise ValueError(f"section has to be in {cls.rss_sections}")
        if section == "Opinion":
            url = url.format("RSSOpinion")
        elif section == "World":
            url = url.format("RSSWorldNews")
        elif section == "U.S. Business":
            url = url.format("WSJcomUSBusiness")
        elif section == "Markets":
            url = url.format("RSSMarketsMain")
        elif section == "Technology":
            url = url.format("RSSWSJD")
        elif section == "Lifestyle":
            url = url.format("RSSLifestyle")
        
        response = requests.get(url=url, headers=HEADERS).text
        soup = BeautifulSoup(response, "lxml")
        tags = soup.find_all("item")

        articles = []
        for tag in tags:
            article = {
                "header": tag.find("title").text,
                "url": f"https://www.wsj.com/articles/{tag.find('guid').text}",
                "datetime": int(pd.to_datetime(tag.find("pubdate").text).timestamp()) if timestamps else pd.to_datetime(tag.find("pubdate").text).isoformat()
            }
            articles.append(article)
            
        return articles