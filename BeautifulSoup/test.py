__author__ = 'Hao Lin'

import urllib
import urllib2
import httplib
from bs4 import BeautifulSoup



url = "http://stats.ncaa.org/game/box_score/779010"

urllib2.urlopen(url)
url_connection = urllib.urlopen(url)
html = url_connection.read()
soup = BeautifulSoup(html)
url_connection.close()

tables = soup.find_all('table')
print len(tables)
for table in tables[4:]:
    if not table.find_all('tr', {"class":"smtext"}):
        print "None"
    else:
        print "Good"