__author__ = 'Hao Lin'

import urllib
from bs4 import BeautifulSoup

#url = "http://stats.ncaa.org/team/index/11540?org_id=26172"
url = "http://stats.ncaa.org/team/inst_team_list#"

html = urllib.urlopen(url).read()
soup = BeautifulSoup(html)

print soup.prettify()

#print soup.title.string.strip()

# all_a = soup.find_all('a')
# for a in all_a:
#     print a