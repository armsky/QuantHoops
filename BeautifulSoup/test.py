__author__ = 'Hao Lin'

import urllib
import urllib2
import httplib
from bs4 import BeautifulSoup



url = "http://stats.ncaa.org/game/box_score/3523706"

urllib2.urlopen(url)
url_connection = urllib.urlopen(url)
html = url_connection.read()
soup = BeautifulSoup(html)
url_connection.close()

print soup

