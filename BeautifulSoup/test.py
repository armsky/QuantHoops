__author__ = 'Hao Lin'

import urllib
from bs4 import BeautifulSoup

#url = "http://stats.ncaa.org/team/index/11540?org_id=26172"
# url = "http://stats.ncaa.org/team/inst_team_list/11540?division=1.0"
url = "http://stats.ncaa.org/game/box_score/29165"

html = urllib.urlopen(url).read()
soup = BeautifulSoup(html)
# print soup

tables = soup.find_all('table')
#tables[0] has team name and team id
team_links = [x.find('a') for x in tables[0].find_all('td')]
team_links = filter(None, team_links)
print team_links

# Two teams are both NCAA team
if len(team_links) == 2:
    first_team_id = int(team_links[0]["href"].split("=")[-1])
    second_team_id = int(team_links[1]["href"].split("=")[-1])

print first_team_id
print second_team_id