from setuptools import find_packages, setup

with open("README.md", "r") as file:
    long_description = file.read()

setup(
    name="findata",
    version="0.0.1",
    author="Jonas Niemeyer",
    description="Functionalities to scrape financial and macroeconomic data sets from the web",
    packages=["findata"]
)