__author__ = 'Hao Lin'

import urllib
from bs4 import BeautifulSoup

#url = "http://stats.ncaa.org/team/index/11540?org_id=26172"
# url = "http://stats.ncaa.org/team/inst_team_list/11540?division=1.0"
url = "http://stats.ncaa.org/team/inst_team_list?academic_year=2015&conf_id=-1&division=2&sport_code=MBB"

html = urllib.urlopen(url).read()
soup = BeautifulSoup(html)

# print soup.prettify()

#print soup.title.string.strip()

all_a = soup.find_all('td')
for a in all_a:
    print a