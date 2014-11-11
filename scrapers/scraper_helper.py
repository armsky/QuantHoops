__author__ = 'Hao Lin'

from QuantHoops.NCAA.ncaa import *

import os
import urllib
import datetime
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


def write_error_to_file(message):
    today = datetime.date.today()
    file_name = str(today.year)+"_"+str(today.month)+"_"+str(today.day)
    file_path = '../Logs/%s'% file_name
    # if os.path.exists(file_path):
    with open(file_path, "a") as f:
        f.write("========"+str(datetime.datetime.now())+"========\n")
        f.write(message)
        f.write("\n\n")

