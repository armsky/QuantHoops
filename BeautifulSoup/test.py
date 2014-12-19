__author__ = 'Hao Lin'

import urllib
import urllib2
import httplib
from bs4 import BeautifulSoup



url = "http://stats.ncaa.org/team/stats?org_id=10972&sport_year_ctl_id=12020"

urllib2.urlopen(url)
url_connection = urllib.urlopen(url)
html = url_connection.read()
soup = BeautifulSoup(html)
url_connection.close()

player_stat_trs = soup.find_all('tr', attrs={'class':'text'})
if player_stat_trs is None:
    print "return"
else:
    print player_stat_trs

