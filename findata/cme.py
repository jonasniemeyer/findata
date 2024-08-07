import pandas as pd
from selenium import webdriver, common
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from . import utils


class CMEReader:
    commodities = {
        # Energy
        "Crude Oil": {"sector": "energy", "group": "crude-oil", "name": "light-sweet-crude", "sector_name": "Energy"},
        "WTI Crude Oil": {"sector": "energy", "group": "crude-oil", "name": "west-texas-intermediate-wti-crude-oil-calendar-swap-futures", "sector_name": "Energy"},
        "Brent Crude Oil": {"sector": "energy", "group": "crude-oil", "name": "brent-ice-calendar-swap-futures", "sector_name": "Energy"},
        "Coal": {"sector": "energy", "group": "coal", "name": "coal-api-2-cif-ara-argus-mccloskey", "sector_name": "Energy"},
        "Gasoline": {"sector": "energy", "group": "refined-products", "name": "rbob-gasoline", "sector_name": "Energy"},
        "Heating Oil": {"sector": "energy", "group": "refined-products", "name": "heating-oil", "sector_name": "Energy"},
        "Natural Gas": {"sector": "energy", "group": "natural-gas", "name": "natural-gas", "sector_name": "Energy"},
        "Global Emissions Offset": {"sector": "energy", "group": "emissions", "name": "cbl-global-emissions-offset", "sector_name": "Energy"},
        "Propane": {"sector": "energy", "group": "petrochemicals", "name": "mont-belvieu-propane-5-decimals-swap", "sector_name": "Energy"},
        "Butane": {"sector": "energy", "group": "petrochemicals", "name": "mont-belvieu-normal-butane-5-decimals-swap", "sector_name": "Energy"},
        "Ethane": {"sector": "energy", "group": "petrochemicals", "name": "mont-belvieu-ethane-opis-5-decimals-swap", "sector_name": "Energy"},
        "Ethanol": {"sector": "energy", "group": "biofuels", "name": "chicago-ethanol-platts-swap", "sector_name": "Energy"},
        # Agriculture
        "Cocoa": {"sector": "agriculture", "group": "lumber-and-softs", "name": "cocoa", "sector_name": "Agriculture"},
        "Coffee": {"sector": "agriculture", "group": "lumber-and-softs", "name": "coffee", "sector_name": "Agriculture"},
        "Corn": {"sector": "agriculture", "group": "grains", "name": "corn", "sector_name": "Agriculture"},
        "Cotton": {"sector": "agriculture", "group": "lumber-and-softs", "name": "cotton", "sector_name": "Agriculture"},
        "Milk": {"sector": "agriculture", "group": "dairy", "name": "class-iii-milk", "sector_name": "Agriculture"},
        "Oats": {"sector": "agriculture", "group": "grains", "name": "oats", "sector_name": "Agriculture"},
        "Soybean": {"sector": "agriculture", "group": "oilseeds", "name": "soybean", "sector_name": "Agriculture"},
        "Soybean Meal": {"sector": "agriculture", "group": "oilseeds", "name": "soybean-meal", "sector_name": "Agriculture"},
        "Soybean Oil": {"sector": "agriculture", "group": "oilseeds", "name": "soybean-oil", "sector_name": "Agriculture"},
        "Sugar": {"sector": "agriculture", "group": "lumber-and-softs", "name": "sugar-no11", "sector_name": "Agriculture"},
        "Wheat": {"sector": "agriculture", "group": "grains", "name": "wheat", "sector_name": "Agriculture"},
        "Feeder Cattle": {"sector": "agriculture", "group": "livestock", "name": "feeder-cattle", "sector_name": "Livestock"},
        "Lean Hogs": {"sector": "agriculture", "group": "livestock", "name": "lean-hogs", "sector_name": "Livestock"},
        "Live Cattle": {"sector": "agriculture", "group": "livestock", "name": "live-cattle", "sector_name": "Livestock"},
        "Lumber": {"sector": "agriculture", "group": "lumber-and-softs", "name": "lumber", "sector_name": "Agriculture"},
        "Rice": {"sector": "agriculture", "group": "grains", "name": "rough-rice", "sector_name": "Agriculture"},
        "Cheese": {"sector": "agriculture", "group": "dairy", "name": "cheese", "sector_name": "Agriculture"},
        "Palm Oil": {"sector": "agriculture", "group": "oilseeds", "name": "usd-malaysian-crude-palm-oil-calendar", "sector_name": "Agriculture"},
        # Metals
        "Aluminum": {"sector": "metals", "group": "base", "name": "aluminum", "sector_name": "Industrial Metals"},
        "Cobalt": {"sector": "metals", "group": "battery-metals", "name": "cobalt-metal-fastmarkets", "sector_name": "Industrial Metals"},
        "Copper": {"sector": "metals", "group": "base", "name": "copper", "sector_name": "Industrial Metals"},
        "Lead": {"sector": "metals", "group": "base", "name": "lead", "sector_name": "Industrial Metals"},
        "Zinc": {"sector": "metals", "group": "base", "name": "zinc", "sector_name": "Industrial Metals"},
        "Gold": {"sector": "metals", "group": "precious", "name": "gold", "sector_name": "Precious Metals"},
        "Palladium": {"sector": "metals", "group": "precious", "name": "palladium", "sector_name": "Precious Metals"},
        "Platinum": {"sector": "metals", "group": "precious", "name": "platinum", "sector_name": "Precious Metals"},
        "Silver": {"sector": "metals", "group": "precious", "name": "silver", "sector_name": "Precious Metals"},
        "Lithium": {"sector": "metals", "group": "battery-metals", "name": "lithium-hydroxide-cif-cjk-fastmarkets", "sector_name": "Industrial Metals"},
        "Steel": {"sector": "metals", "group": "ferrous", "name": "hrc-steel", "sector_name": "Industrial Metals"},
        "Uranium U308": {"sector": "metals", "group": "other", "name": "uranium", "sector_name": "Industrial Metals"}
    }

    def __init__(self, commodity, timestamps=False):
        self._commodity = commodity
        self._sector = self.commodities[commodity]["sector"]
        self._group = self.commodities[commodity]["group"]
        self._name = self.commodities[commodity]["name"]
        self._url = "https://www.cmegroup.com/markets/{}/{}/{}.settlements.html".format(
            self.sector,
            self.group,
            self.name
        )
        self._timestamps = timestamps
    
    def _open_website(self, browser="chrome", url=None):
        if not hasattr(self, "driver"):
            if browser == "chrome":
                options = webdriver.ChromeOptions()
                options.add_argument("--headless=new")
                options.add_argument(f"--user-agent={utils.HEADERS['User-Agent']}")
                options.add_experimental_option("excludeSwitches", ["enable-logging"])
                self.driver = webdriver.Chrome(service=Service(utils.CHROMEDRIVER_PATH), options=options)
            else:
                raise NotImplementedError("CMEReader is only implemented for the Google Chrome Browser")
        self.driver.get(self.url)
        i = 0
        clicked = False
        while not clicked:
            try:
                button_cookies = WebDriverWait(self.driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, f"/html/body/div[{i}]/div[2]/div/div[1]/div/div[2]/div/button[3]"))
                )
                button_cookies.click()
                clicked = True
            except common.exceptions.TimeoutException:
                pass
            i += 1

        if self.commodity == "Aluminum":
            button_survey = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, f"/html/body/div[8]/div/div[1]/div/div/div[1]/button"))
            )
            button_survey.click()

    def _parse(self) -> dict:
        data = {}

        time.sleep(1)
        try:
            button_expand = self.driver.find_element(by=By.XPATH, value="/html/body/main/div/div[3]/div[3]/div/div/div/div/div/div[2]/div/div/div/div/div/div[9]/div[2]/button")
        except common.exceptions.NoSuchElementException:
            y_distance = 0
        else:
            y_distance = button_expand.location["y"] - 200
            self.driver.execute_script(f"window.scrollBy(0, {y_distance})")
            time.sleep(1)
            button_expand.click()

        self.driver.execute_script(f"window.scrollBy(0, {-y_distance+300})")
        time.sleep(1)

        div = self.driver.find_element(by=By.XPATH, value="/html/body/main/div/div[3]/div[3]/div/div/div/div/div/div[2]/div/div/div/div/div/div[5]/div/div/div")
        button = div.find_element(by=By.XPATH, value=".//button")
        button.click()
        no_dates = len(div.find_elements(by=By.CSS_SELECTOR, value="div[role='presentation']"))
        assert no_dates != 0

        for index in range(1, no_dates+1):
            date_btn = self.driver.find_element(by=By.XPATH, value=f"/html/body/main/div/div[3]/div[3]/div/div/div/div/div/div[2]/div/div/div/div/div/div[5]/div/div/div/div/div/div[1]/div[2]/div/div/div/div/div[{index}]")
            date = pd.to_datetime(date_btn.get_attribute("data-value"))
            date_btn.click()
            time.sleep(2)
            if self.timestamps:
                data[int(date.timestamp())] = self._parse_table()
            else:
                data[date.date().isoformat()] = self._parse_table()
            button.click()

        return data
    
    def _parse_table(self) -> pd.DataFrame:
        html = self.driver.page_source
        df = pd.read_html(html)[0]
        df = df.set_index("Month")
        df.index = [item.replace("JLY", "JUL") for item in df.index]
        df.index = pd.to_datetime(df.index, format="%b %y")
        if self.timestamps:
            df.index = [int(date.timestamp()) for date in df.index]
        for col in df.columns:
            df[col] = df[col].apply(lambda x: x.replace("A", "") if isinstance(x, str) else x)
            df[col] = df[col].apply(lambda x: x.replace("B", "") if isinstance(x, str) else x)
            df[col] = df[col].apply(lambda x: x.replace("'", "") if isinstance(x, str) else x)
            df[col] = df[col].apply(lambda x: x.replace("-", "") if isinstance(x, str) else x)
            df[col] = df[col].apply(lambda x: x.replace("UNCH", "0") if isinstance(x, str) else x)
            df[col] = pd.to_numeric(df[col])
        df = df.rename(columns = {"Est. Volume": "Volume", "Prior day OI": "Open Interest"})
        return df

    @property
    def commodity(self) -> str:
        return self._commodity

    @property
    def group(self) -> str:
        return self._group

    @property
    def name(self) -> str:
        return self._name

    @property
    def sector(self) -> str:
        return self._sector

    @property
    def timestamps(self) -> bool:
        return self._timestamps

    @property
    def url(self) -> str:
        return self._url

    def read(self) -> dict:
        self._open_website()
        data = self._parse()
        self.driver.quit()
        return data