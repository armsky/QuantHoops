__author__ = 'Hao Lin'

import urllib
from bs4 import BeautifulSoup

#url = "http://stats.ncaa.org/team/index/11540?org_id=26172"
# url = "http://stats.ncaa.org/team/inst_team_list/11540?division=1.0"
url = "http://stats.ncaa.org/game/play_by_play/26962"

html = urllib.urlopen(url).read()
soup = BeautifulSoup(html)
# print soup

tables = soup.find_all("table")
gamedetail_records = []
for table in tables[5:]:
    if tables.index(table) == 5:
        section = "1st Half"

    elif tables.index(table) == 7:
        section = "2nd Half"
    elif tables.index(table) == 9:
        section = "1st OT"
    elif tables.index(table) == 11:
        section = "2nd OT"

    print section