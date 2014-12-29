__author__ = 'Hao Lin'

import urllib
import urllib2
import httplib
from bs4 import BeautifulSoup



url = "http://stats.ncaa.org/team/index/12020?org_id=807"

urllib2.urlopen(url)
url_connection = urllib.urlopen(url)
html = url_connection.read()
soup = BeautifulSoup(html)
url_connection.close()

tr_list = soup.find('table', attrs={'class': 'mytable', 'align': 'center'}).find_all('tr')
for tr in tr_list:
    # This contains game information
    if len(tr.find_all('td')) == 3 and not tr.has_attr('class'):
        both_teams_are_ncaa = False
        winner_id = None
        loser_id = None
        game_td_list = tr.find_all('td', attrs={'class': 'smtext'})
        opponent = game_td_list[1].find('a')
        result = game_td_list[2].find('a')

        game_id = int(result['href'].split("?")[0].split("/")[-1])
        print result, game_id