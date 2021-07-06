import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from finance_data.utils import (
    TickerError,
    macrotrends_conversion
)

class MacrotrendsReader:
    
    url_long = "https://www.macrotrends.net/stocks/charts/{}/{}/{}?freq={}"
    url_short = "https://www.macrotrends.net/stocks/charts/{}"

    conversion = {
        "income-statement": "income_statement",
        "balance-sheet": "balance_sheet",
        "cash-flow-statement": "cashflow_statement"
    }

    def __init__(
        self,
        ticker = None,
        statement = "financial-statement",
        frequency = "Y",
        name = None
    ):

        if ticker is None or statement is None or frequency is None:
            raise ValueError("Arguments have to be either a url or a combination of a ticker, a statement-type and a frequency, plus an optional name")
        elif statement not in ("income-statement", "balance-sheet", "cash-flow-statement", "financial-statement"):
            raise ValueError('Statement type has to be "income-statement", "balance-sheet", "cash-flow-statement" or "financial-statement"')
        elif frequency not in ("Q", "Y"):
            raise ValueError('Reporting Frequency has to be yearly ("Y") or quarterly ("Q")')
        self._ticker = ticker.upper()
        if "-" in self._ticker:
            self._ticker = self._ticker.replace("-", ".")
        self.statement = statement
        self.frequency = frequency
        if name is None:
            self.url = self.url_short.format(self.ticker)
        else:
            self.name = name
            self.url = self.url_long.format(
                self.ticker,
                self.name,
                self.statement,
                self.frequency
            )

    def open_website(self, browser="Chrome", url=None):
        """
        Opens the website and the url with the according webdriver and extracts the necessary items:
        1. slider object
        2. cell width
        3. slider sensitivity
        4. scrollbar width
        The driver waits for a cookie button to appear, clicks it, and then moves to the slider of the table
        """
        if not hasattr(self, "driver"):
            if browser == "Chrome":
                self.driver = webdriver.Chrome()
            else:
                raise NotImplementedError
        
        if not hasattr(self, "name"):
            self.driver.get(self.url)
            self.name = self.driver.current_url.split("/")[-2]
            if self.name == "charts" or "?" in self.name:
                self.driver.quit()
                raise TickerError(f"cannot find the website with ticker {self.ticker}")
            self.url = self.url_long.format(
                self.ticker,
                self.name,
                self.statement,
                self.frequency
            )
        
        if url is None:
            if self.statement == "financial-statement":
                self.driver.get(self.url.replace("financial-statement", "income-statement"))
            else:
                self.driver.get(self.url)
        else:
            self.driver.get(url)

        if url is None:
            try:
                button_cookies = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div[5]/div[1]/div[1]/div/button"))
                )
                button_cookies.click()
            except:
                pass

    def parse(self):
        data = {}
        if self.statement == "financial-statement":
            for statement in ("income-statement", "balance-sheet", "cash-flow-statement"):
                href_url = self.url.replace("financial-statement", statement)
                self.open_website(url = href_url)
                data = data | {self.conversion[statement]: self._parse()}
        else:
            data = self._parse()
        self.driver.quit()

        return data

    def _parse(self) -> dict:
        """
        Parses the table and returns a dictionary of dates as keys and dictionaries as values,
        each having the variables as keys and the data of the variable at the respective date as values
        """
        footer = self.driver.find_element_by_xpath("/html/body/footer")
        actions = ActionChains(self.driver)
        actions.move_to_element(footer).perform()
        self.slider = self.driver.find_element_by_id("jqxScrollThumbhorizontalScrollBarjqxgrid")
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
            data[macrotrends_conversion[var_name]] = {}
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
                for row_index, row in enumerate(rows):
                    cells = row.find_all("div", {"role": "gridcell"})
                    cell = cells[col_index]
                    value = cell.find("div").text
                    var_name = variables[row_index]
                    if value == "-":
                        value = None
                        data[macrotrends_conversion[var_name]][date] = value
                        continue
                    if var_name not in ("Basic EPS", "EPS - Earnings Per Share"):
                        value = int(float(value.strip("$").replace(".", "").replace(",", ".")) * 1_000_000)
                    else:
                        value = float(value.strip("$"))
                    data[macrotrends_conversion[var_name]][date] = value
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

    def from_url(cls, url):
        frequency = url[-1]
        url_split = url.split("/")
        ticker = url_split[5]
        name = url_split[6]
        statement = url_split[7].rstrip(f"?freq={frequency}")
        return MacrotrendsReader(
            ticker = ticker,
            statement = statement,
            frequency = frequency,
            name = name
        )

    @property
    def ticker(self):
        return self._ticker
