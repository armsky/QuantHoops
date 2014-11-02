__author__ = 'Hao Lin'

from QuantHoops.NCAA.ncaa import *

import urllib
import re
from bs4 import BeautifulSoup

def soupify(url):
    """
    Takes a url and returns parsed html via BeautifulSoup and urllib.
    Used by the scrapers.
    """
    html = urllib.urlopen(url).read()
    soup = BeautifulSoup(html)
    return soup

def get_team_link(url):
    soup = soupify(url)
    team_links = list(set([x.find('a') for x in soup.findAll('td')]))
    return team_links