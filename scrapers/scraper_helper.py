__author__ = 'Hao Lin'


import traceback
import urllib
import datetime
from bs4 import BeautifulSoup

def soupify(url):
    """
    Takes a url and returns parsed html via BeautifulSoup and urllib.
    Used by the scrapers.
    """
    url_connection = urllib.urlopen(url)
    html = url_connection.read()
    soup = BeautifulSoup(html)
    url_connection.close()
    return soup


def get_team_link(url):
    soup = soupify(url)
    team_links = list(set([x.find('a') for x in soup.find_all('td')]))
    return team_links


def write_error_to_file(message):
    today = datetime.date.today()
    file_name = str(today.year)+"_"+str(today.month)+"_"+str(today.day)+".txt"
    file_path = '../Logs/%s'% file_name
    with open(file_path, "a") as f:
        f.write("========"+str(datetime.datetime.now())+"========\n")
        f.write(message)
        f.write(str(traceback.format_exc()))
        f.write("\n\n")

