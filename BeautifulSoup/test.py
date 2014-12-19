__author__ = 'Hao Lin'

import urllib
import urllib2
import httplib
from bs4 import BeautifulSoup



url = "http://stats.ncaa.org/team/stats?org_id=618&sport_year_ctl_id=12020"

urllib2.urlopen(url)
url_connection = urllib.urlopen(url)
html = url_connection.read()
soup = BeautifulSoup(html)
url_connection.close()

team_stat_trs = soup.find_all('tr', attrs={'class':'grey_heading'})
print team_stat_trs
if len(team_stat_trs) == 3:
    opnt_stat_tr = team_stat_trs[2]
    # Scrap Team's Opponent stat
    opnt_stat_list = preprocess_stat_list(opnt_stat_tr.find_all('td'))
    opnt_stats = {
        'Opnt_minutes_played':opnt_stat_list[7].string,
        'Opnt_field_goals_made':opnt_stat_list[8].string.replace(',',''),
        'Opnt_field_goals_attempted':opnt_stat_list[9].string.replace(',',''),
        'Opnt_field_goals_percentage':opnt_stat_list[10].string,
        'Opnt_three_field_goals_made':opnt_stat_list[11].string.replace(',',''),
        'Opnt_three_field_goals_attempted':opnt_stat_list[12].string.replace(',',''),
        'Opnt_three_field_goals_percentage':opnt_stat_list[13].string,
        'Opnt_free_throws_made':opnt_stat_list[14].string.replace(',',''),
        'Opnt_free_throws_attempted':opnt_stat_list[15].string.replace(',',''),
        'Opnt_free_throws_percentage':opnt_stat_list[16].string,
        'Opnt_points':opnt_stat_list[17].string.replace(',',''),
        'Opnt_average_points':opnt_stat_list[18].string.replace(',',''),
        'Opnt_offensive_rebounds':opnt_stat_list[19].string.replace(',',''),
        'Opnt_defensive_rebounds':opnt_stat_list[20].string.replace(',',''),
        'Opnt_total_rebounds':opnt_stat_list[21].string.replace(',',''),
        'Opnt_average_rebounds':opnt_stat_list[22].string.replace(',',''),
        'Opnt_assists': opnt_stat_list[23].string.replace(',',''),
        'Opnt_turnovers':opnt_stat_list[24].string.replace(',',''),
        'Opnt_steals':opnt_stat_list[25].string.replace(',',''),
        'Opnt_blocks':opnt_stat_list[26].string.replace(',',''),
        'Opnt_fouls':opnt_stat_list[27].string.replace(',',''),
        'Opnt_double_doubles':opnt_stat_list[28].string,
        'Opnt_triple_doubles':opnt_stat_list[29].string
    }

print opnt_stats