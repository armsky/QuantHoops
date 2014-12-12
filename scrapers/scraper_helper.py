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
        f.write("\n")
        f.write(str(traceback.format_exc()))
        f.write("\n\n")


def preprocess_stat_list(stat_list):
    # A number followed by '*' means season high
    # A number followed by '/' means game high
    # A number followed by '-' means team high
    # Need to eliminate them
    translate_table = dict((ord(char), u'') for char in "*/-")
    for stat in stat_list:
        if stat.string == u'\xa0' or stat.string == ' ' or stat.string is None:
            stat.string = '0'
        stat.string = stat.string.translate(translate_table)
    return stat_list


def get_current_year():
    today = datetime.date.today()
    return str(today.year)


def get_current_month():
    today = datetime.date.today()
    return str(today.month)