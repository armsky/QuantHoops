__author__ = 'Hao Lin'

import urllib
import urllib2
import httplib
from bs4 import BeautifulSoup



url = "http://stats.ncaa.org/team/roster/12020?org_id=585"

urllib2.urlopen(url)
url_connection = urllib.urlopen(url)
html = url_connection.read()
soup = BeautifulSoup(html)
url_connection.close()

players_info = soup.find('tbody').find_all('tr')
print players_info


