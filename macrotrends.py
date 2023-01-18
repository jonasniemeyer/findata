import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from finance_data.utils import (
    TickerError,
    MACROTRENDS_CONVERSION
)

class MacrotrendsReader:
    
    base_url = "https://www.macrotrends.net/stocks/charts/{}/{}/{}?freq={}"

    conversion = {
        "income-statement": "income statement",
        "balance-sheet": "balance sheet",
        "cash-flow-statement": "cashflow statement"
    }

    def __init__(
        self,
        ticker=None,
        name=None,
        statement="financial-statement",
        frequency="yearly",
        timestamps=False
    ):
        if statement not in ("income-statement", "balance-sheet", "cash-flow-statement", "financial-statement"):
            raise ValueError('Statement type has to be "income-statement", "balance-sheet", "cash-flow-statement" or "financial-statement"')
        
        self._ticker = ticker.upper()
        if "-" in self._ticker:
            self._ticker = self._ticker.replace("-", ".")
        
        self.name = "placeholder" if name is None else name

        if statement == "financial-statements":
            self.statement = "financial-statement"
        else:
            self.statement = statement

        if frequency in ("Y", "yearly", "A", "annual"):
            self.frequency = "Y"
        elif frequency in ("Q", "quarterly"):
            self.frequency = "Q"
        else:
            raise ValueError('Reporting Frequency has to be "yearly", "Y", "annual", "A", "quarterly" or "Q"')
        
        self.url = self.base_url.format(
            self.ticker,
            self.name,
            self.statement,
            self.frequency
        )

        self.timestamps = timestamps
    
    def read(self):
        self._open_website()
        return self._parse()

    def _open_website(self, browser="chrome", url=None):
        """
        Opens the website and the url with the according webdriver and extracts the necessary items:
        1. slider object
        2. cell width
        3. slider sensitivity
        4. scrollbar width
        The driver waits for a cookie button to appear, clicks it, and then moves to the slider of the table
        """
        if not hasattr(self, "driver"):
            options = webdriver.ChromeOptions() 
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            if browser == "chrome":
                self.driver = webdriver.Chrome(options=options)
            else:
                raise NotImplementedError
        
        if url is None:
            if self.statement == "financial-statement":
                self.driver.get(self.url.replace("financial-statement", "income-statement"))
            else:
                self.driver.get(self.url)

            name = self.driver.current_url.split("/")[-2]
            if name == "":
                self.driver.quit()
                raise TickerError(f"cannot find data with ticker {self.ticker}")
            self.name = name
            self.url = self.base_url.format(
                self.ticker,
                self.name,
                self.statement,
                self.frequency
            )
            
            try:
                button_cookies = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div[4]/div[1]/div[1]/div/button"))
                )
                button_cookies.click()
            except:
                pass
        
        else:
            self.driver.get(url)

    def _parse(self):
        data = {}
        if self.statement == "financial-statement":
            for statement in ("income-statement", "balance-sheet", "cash-flow-statement"):
                href_url = self.url.replace("financial-statement", statement)
                self._open_website(url=href_url)
                data = data | {self.conversion[statement]: self._parse_table()}
        else:
            data = self._parse_table()
        self.driver.quit()

        return data

    def _parse_table(self) -> dict:
        """
        Parses the table and returns a dictionary of dates as keys and dictionaries as values,
        each having the variables as keys and the data of the variable at the respective date as values
        """
        footer = self.driver.find_element(by=By.XPATH, value="/html/body/div[3]/footer")
        actions = ActionChains(self.driver)
        actions.move_to_element(footer).perform()
        self.slider = self.driver.find_element(by=By.ID, value="jqxScrollThumbhorizontalScrollBarjqxgrid")
        try:
            self._cell_width = self._find_cell_width()
        except:
            return {}
        if self.slider.is_displayed():
            self._slider_sensitivity = self._find_slider_sensitivity()
        else:
            self._slider_sensitivity = None
        self._scrollbar_width = self._find_scrollbar_width()
        html = self.driver.page_source
        soup = BeautifulSoup(html, "lxml")

        table = soup.find("div", {"id":"jqxgrid"})
        columns = table.find_all("div", {"role": "columnheader"})
        no_cols = len(columns) - 2
        rows = table.find_all("div", {"role": "row"})
        data = {}
        variables = []
        for row in rows:
            cell = row.find_all("div", {"role": "gridcell"})[0]
            try:
                var_name = cell.find("a").text
            except:
                var_name = cell.find("span").text
            data[MACROTRENDS_CONVERSION[var_name]] = {}
            variables.append(var_name)
        loop_control = 0
        while self._scrollbar_width > 0:
            if loop_control == 0:
                loop_control = 1
            else:
                if self._slider_sensitivity is not None:
                    distance = min(self._cell_width / self._slider_sensitivity * no_cols, self._scrollbar_width)
                    self._move_slider(distance)
                    self._scrollbar_width = self._find_scrollbar_width()
            html = self.driver.page_source
            soup = BeautifulSoup(html, "lxml")
            table = soup.find("div", {"id":"jqxgrid"})
            columns = table.find_all("div", {"role": "columnheader"})
            rows = table.find_all("div", {"role": "row"})
            for col_index, col in enumerate(columns):
                if col_index < 2:
                    continue
                date = col.find("span", {"style": "text-overflow: ellipsis; cursor: default;"}).text
                if self.timestamps:
                    date = int(pd.to_datetime(date).timestamp())
                for row_index, row in enumerate(rows):
                    cells = row.find_all("div", {"role": "gridcell"})
                    cell = cells[col_index]
                    value = cell.find("div").text
                    var_name = variables[row_index]
                    if value == "-":
                        value = None
                        data[MACROTRENDS_CONVERSION[var_name]][date] = value
                        continue
                    if var_name not in ("Basic EPS", "EPS - Earnings Per Share"):
                        value = int(float(value.strip("$").replace(".", "").replace(",", ".")) * 1_000_000)
                    else:
                        value = float(value.strip("$"))
                    data[MACROTRENDS_CONVERSION[var_name]][date] = value
            if self._slider_sensitivity is None:
                break
        return data

    def _move_slider(self, pixels) -> None:
        """
        Moves the slider n pixels to the right
        """
        move = ActionChains(self.driver)
        move.click_and_hold(self.slider).move_by_offset(pixels, 0).release().perform()

    def _find_cell_width(self) -> int:
        """
        Finds the cell width of the cells that contain the financial data values.
        They are needed to compute the minimum pixels the slider has to be moved to the right in order to see and parse the next column
        """
        html = self.driver.page_source
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("div", {"id":"jqxgrid"})
        row = table.find_all("div", {"role": "row"})[0]
        cell = row.find_all("div", {"role": "gridcell"})[2].get("style")
        width = re.findall("width:\s?([0-9]+)px", cell)[0]
        width = int(width)
        return width

    def _find_slider_sensitivity(self) -> int:
        """
        Moves the slider 1px to the right and gets the "margin-left"-attribute of the cells of the first column to check, 
        how far the table is moved to the left in response of moving the slider
        """
        self._move_slider(10)
        html = self.driver.page_source
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("div", {"id":"jqxgrid"})
        row = table.find_all("div", {"role": "row"})[0]
        cell = row.find_all("div", {"role": "gridcell"})[0].get("style")
        try:
            margin = re.findall("margin-left:\s?([0-9]+)px", cell)[0]
            margin = int(margin)
            return margin / 10
        except:
            return

    def _find_scrollbar_width(self) -> int:
        """
        Returns the width of the scrollbar (in px) right to the slider. This is needed to see, how often the slider can be moved
        to the right without touching the end of the scrollbar
        """
        html = self.driver.page_source
        width = BeautifulSoup(html, "lxml").find("div", {"id": "jqxScrollAreaDownhorizontalScrollBarjqxgrid"}).get("style")
        width = int(re.findall("width: ([0-9]+)px", width)[0])
        return width

    @property
    def ticker(self):
        return self._ticker