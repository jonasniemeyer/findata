import re
import numpy as np
import datetime as dt
from utils import _headers
from bs4 import BeautifulSoup
import pandas as pd
import requests

class SECFiling:
    def __init__(self, file: str) -> None:
        self._file = file
        self._header = self._file[:self._file.find("</SEC-HEADER>")]
        self._document = self._file[self._file.find("<DOCUMENT>"):]
        self._subject_information, self._filer_information = self._split_header()
        
        self._filer = []
        for item in self._filer_information:
            if len(item) == 0:
                continue
            filer = {}
            filer["name"] = self._parse_name(item)
            filer["cik"] = self._parse_cik(item)
            try:
                filer["sic"] = self._parse_sic(item)
            except:
                filer["sic"] = None
            self._filer.append(filer)
        
        self._subject = []
        for item in self._subject_information:
            if len(item) == 0:
                continue
            subject = {}
            subject["name"] = self._parse_name(item)
            subject["cik"] = self._parse_cik(item)
            try:
                subject["sic"] = self._parse_sic(item)
            except:
                subject["sic"] = None
            self._subject.append(subject)
            
        self._form_type = self._parse_form_type()
        self._filing_date = self._parse_filing_date()
        
        self._is_html = True if "html" in self._file else False
    
    def _split_header(self):
        
        filer_section_start = self.header.find("FILER:")
        if filer_section_start == -1:
            filer_section_start = self.header.find("FILED BY:")   
        subject_section_start = self.header.find("SUBJECT COMPANY:")
        
        if subject_section_start > filer_section_start:
            raise ValueError("subject section comes after filer section")
        
        subject_section = self.header[subject_section_start:filer_section_start]   
        subject_section = subject_section.split("SUBJECT COMPANY:")
        
        filer_section = self.header[filer_section_start:]
        if self.header.find("FILER:") == -1:
            filer_section = filer_section.split("FILED BY:")[1:]
        else:
            filer_section = filer_section.split("FILER:")[1:]
        
        return subject_section, filer_section

    def _header_information(self) -> dict:
        self.company_information = {}
        self.company_information["filer"] = self.filer
        self.company_information["subject"] = self.subject
        self.company_information["form_type"], self.company_information["amendment"] = self.form_type
        self.company_information["filing_date"] = self.filing_date
        
        return self.company_information

    def _parse_name(self, section) -> str:
        name = re.findall("COMPANY CONFORMED NAME:\t{3}(.+)", section)[0]
        name = name.strip().lower().title()
        return name

    def _parse_cik(self, section) -> int:
        cik = int(re.findall("CENTRAL INDEX KEY:\t{3}([0-9]+)", section)[0])
        return cik
    
    def _parse_sic(self, section) -> int:
        sic = int(re.findall("STANDARD INDUSTRIAL CLASSIFICATION:\t{1}.+\[([0-9]+)\]", section)[0])
        return sic
    
    def _parse_form_type(self) -> tuple:
        form = re.findall("FORM TYPE:\t{2}(.+)\n", self._file)[0]
        amendment = True if form.endswith("/A") else False
        return form, amendment

    def _parse_filing_date(self) -> str:
        date = re.findall("FILED AS OF DATE:\t{2}([0-9]+)", self._file)[0]
        year = int(date[:4])
        month = int(date[4:6])
        day = int(date[6:])
        date = dt.date(year, month, day).isoformat()
        return date

    @classmethod
    def from_url(cls, url: str):
        txt = requests.get(
            url = url,
            headers = _headers
        ).text
        return cls(txt)
    
    @property
    def file(self) -> str:
        return self._file
    
    @property
    def header(self) -> str:
        return self._header
    
    @property
    def document(self) -> str:
        return self._document
    
    @property
    def header_information(self):
        return self._header_information()

    @property
    def filer(self) -> dict:
        return self._filer
    
    @property
    def subject(self) -> dict:
        return self._subject

    @property
    def form_type(self) -> str:
        return self._form_type

    @property
    def filing_date(self) -> str:
        return self._filing_date
    
    @property
    def is_html(self):
        return self._is_html

    def __str__(self) -> str:
        filer_names = [item["name"] for item in self.filer]
        subject_names = [item["name"] for item in self.subject]
        if len(self.subject) == 0:
            return (
                f"{self.form_type[0]} Filing"   
                f"(Date: {self.filing_date}; "
                f"Filer: {'/'.join(filer_names)})"
                )
        else:
            return (
                f"{self.form_type[0]} Filing"   
                f"(Date: {self.filing_date}; "
                f"Filer: {'/'.join(filer_names)}; "
                f"Subject: {'/'.join(subject_names)})"
            )

    def __repr__(self) -> str:
        filer_names = [item["name"] for item in self.filer]
        subject_names = [item["name"] for item in self.subject]
        if len(self.subject) == 0:
            return (
                f"{self.form_type[0]} Filing"   
                f"(Date: {self.filing_date}; "
                f"Filer: {'/'.join(filer_names)})"
                )
        else:
            return (
                f"{self.form_type[0]} Filing"   
                f"(Date: {self.filing_date}; "
                f"Filer: {'/'.join(filer_names)}; "
                f"Subject: {'/'.join(subject_names)})"
            )


class Filing13D(SECFiling):
    def __init__(self, file: str) -> None:
        super().__init__(file)
        self._subject_cusip = self._parse_cusip()
        self._percentage_acquired = self._parse_percentage_acquired()
        self._shares_acquired = self._parse_shares_acquired()
    
    def _parse_cusip(self) -> str:
        try:
            cusip = re.findall("(?i)CUSIP NO\..+([a-z0-9]{9})", self.file)[0]
        except:
            cusip = re.findall(
                "[\( >]*[0-9A-Z]{1}[0-9]{3}[0-9A-Za-z]{2}[- ]*[0-9]{0,2}[- ]*[0-9]{0,1}[\) \n<]",
                file
            )[0].strip().replace(" ", "")
        
        return cusip

    def _parse_percentage_acquired(self) -> float:
        found = False
        for row in self.document.split("\n"):
            if found is True:
                percentage = re.findall("([0-9]{1,3}.[0-9]{,2})%", row)[0]
                percentage = float(percentage) / 100
                break
            if re.findall("(?i)PERCENT OF CLASS REPRESENTED BY AMOUNT IN ROW", row):
                found = True
                try:
                    percentage = re.findall("(?i)PERCENT OF CLASS REPRESENTED BY AMOUNT IN ROW.+?([0-9]{1,3}.[0-9]{2})%", row)[0]
                    percentage = float(percentage) / 100
                    break
                except:
                    pass
        
        return percentage

    def _parse_shares_acquired(self) -> int:
        found = False
        for row in self.document.split("\n"):
            if found is True:
                shares = re.findall("([0-9,]+).+", row)[0]
                shares = int(shares.replace(",", ""))
                break
            if re.findall("(?i)AGGREGATE AMOUNT BENEFICIALLY OWNED BY EACH REPORTING PERSON", row):
                found = True
                try:
                    shares = re.findall("(?i)AGGREGATE AMOUNT BENEFICIALLY OWNED BY EACH REPORTING PERSON.+?([0-9,]+).+", row)[0]
                    shares = int(shares.replace(",", ""))
                    break
                except:
                    pass
        
        return shares
    
    @property
    def subject_cusip(self) -> str:
        return self._subject_cusip
    
    @property
    def percentage_acquired(self) -> float:
        return self._percentage_acquired
    
    @property
    def shares_acquired(self) -> int:
        return self._shares_acquired

class Filing13G(Filing13D):
    def __init__(self, file: str) -> None:
        super().__init__(file)


