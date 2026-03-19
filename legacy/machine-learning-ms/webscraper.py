"""
First Webscraper Build, v1.0
Scrapes /r/Berkeley
@author Misha Lubich
"""

import requests 
from bs4 import BeautifulSoup as bs
import csv


URL = "https://www.reddit.com/r/berkeley/"
r = requests.get(URL) 


soap = bs(r.content, 'html5lib')
print(soap.prettify())
