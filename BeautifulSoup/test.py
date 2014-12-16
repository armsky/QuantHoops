__author__ = 'Hao Lin'

import urllib
from bs4 import BeautifulSoup


url = "http://stats.ncaa.org/team/index/12020?org_id=460"

html = urllib.urlopen(url).read()
soup = BeautifulSoup(html)
# print soup
count = 1
tr_list = soup.find('table', attrs={'class':'mytable', 'align':'center'}).find_all('tr')
print tr_list

# print tr_list[11].find_all('td', attrs={'class':'smtext'})[1]
for tr in tr_list:
    # This contains game information

    if len(tr.find_all('td')) == 3 and not tr.has_attr('class'):
        both_teams_are_ncaa = False
        winner_id = None
        loser_id = None
        game_td_list = tr.find_all('td', attrs={'class':'smtext'})
        opponent = game_td_list[1].find('a')
        result = game_td_list[2].find('a')

        # if game_td_list[1].find('a') is None:

        if len(game_td_list[1].contents) == 3:
            print game_td_list[1].contents[2].strip()
        count = count + 1
