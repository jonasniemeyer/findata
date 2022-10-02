import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CMEReader:
    commodities = {
       "WTI Crude Oil": {"sector": "energy", "group": "crude-oil", "name": "light-sweet-crude"}, 
       "Heating Oil": {"sector": "energy", "group": "refined-products", "name": "heating-oil"},
       "Natural Gas": {"sector": "energy", "group": "natural-gas", "name": "natural-gas"},
       "Cocoa": {"sector": "agriculture", "group": "lumber-and-softs", "name": "cocoa"},
       "Coffee": {"sector": "agriculture", "group": "lumber-and-softs", "name": "coffee"},
       "Corn": {"sector": "agriculture", "group": "grains", "name": "corn"},
       "Cotton": {"sector": "agriculture", "group": "lumber-and-softs", "name": "cotton"},
       "Milk": {"sector": "agriculture", "group": "dairy", "name": "class-iii-milk"},
       "Oats": {"sector": "agriculture", "group": "grains", "name": "oats"},
       "Soybean": {"sector": "agriculture", "group": "oilseeds", "name": "soybean"},
       "Soybean Meal": {"sector": "agriculture", "group": "oilseeds", "name": "soybean-meal"},
       "Soybean Oil": {"sector": "agriculture", "group": "oilseeds", "name": "soybean-oil"},
       "Sugar": {"sector": "agriculture", "group": "lumber-and-softs", "name": "sugar-no11"},
       "Wheat": {"sector": "agriculture", "group": "grains", "name": "wheat"},
       "Feeder Cattle": {"sector": "agriculture", "group": "livestock", "name": "feeder-cattle"},
       "Lean Hogs": {"sector": "agriculture", "group": "livestock", "name": "lean-hogs"},
       "Live Cattle": {"sector": "agriculture", "group": "livestock", "name": "live-cattle"},
       "Aluminum": {"sector": "metals", "group": "base", "name": "aluminum"},
       "Copper": {"sector": "metals", "group": "base", "name": "copper"},
       "Lead": {"sector": "metals", "group": "base", "name": "lead"},
       "Zinc": {"sector": "metals", "group": "base", "name": "zinc"},
       "Gold": {"sector": "metals", "group": "precious", "name": "gold"},
       "Palladium": {"sector": "metals", "group": "precious", "name": "palladium"},
       "Platinum": {"sector": "metals", "group": "precious", "name": "platinum"},
       "Silver": {"sector": "metals", "group": "precious", "name": "silver"}
    }

    def __init__(self, commodity, timestamps=False):
        self.commodity = commodity
        self.sector = self.commodities[commodity]["sector"]
        self.group = self.commodities[commodity]["group"]
        self.name = self.commodities[commodity]["name"]
        self.url = "https://www.cmegroup.com/markets/{}/{}/{}.settlements.html".format(
            self.sector,
            self.group,
            self.name
        )
        self.timestamps = timestamps
    
    def read(self) -> dict:
        self._open_website()
        data = self._parse()
        self.driver.quit()
        return data
    
    def _open_website(self, browser="chrome", url=None):
        if not hasattr(self, "driver"):
            if browser == "chrome":
                self.driver = webdriver.Chrome()
            else:
                raise NotImplementedError
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
            except:
                pass
            i += 1
    
    def _parse(self) -> dict:
        data = {}
        
        html = self.driver.page_source
        soup = BeautifulSoup(html, "lxml")
        button = soup.find("select", {"class": "dropdown-toggle"})
        options = button.find_all("option")
        
        date = pd.to_datetime(options[0].get("value"))
        if self.timestamps:
            data[int(date.timestamp())] = self._parse_table()
        else:
            data[date.date().isoformat()] = self._parse_table()
        
        for index, option in enumerate(options):
            if index == 0:
                continue
            date = pd.to_datetime(option.get("value"))
            button_dates = self.driver.find_element_by_xpath("/html/body/main/div/div[3]/div[2]/div/div/div/div/div/div[2]/div/div/div/div/div/div[4]/div/div/div/div/select")
            actions = ActionChains(self.driver)
            actions.move_to_element(button_dates).perform()
            button_dates.click()
            button_refresh = self.driver.find_element_by_xpath(f"/html/body/main/div/div[3]/div[2]/div/div/div/div/div/div[2]/div/div/div/div/div/div[4]/div/div/div/div/select/option[{index+1}]")
            button_refresh.click()
            if self.timestamps:
                data[int(date.timestamp())] = self._parse_table()
            else:
                data[date.date().isoformat()] = self._parse_table()
        
        return data
    
    def _parse_table(self) -> pd.DataFrame:
        time.sleep(1)
        try:
            button_expand = self.driver.find_element_by_xpath("/html/body/main/div/div[3]/div[2]/div/div/div/div/div/div[2]/div/div/div/div/div/div[8]/div[2]/button")
            actions = ActionChains(self.driver)
            actions.move_to_element(button_expand).perform()
            self.driver.execute_script("window.scrollBy(0, 200)")
            button_expand.click()
        except:
            pass
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