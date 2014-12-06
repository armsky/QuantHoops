__author__ = 'Hao Lin'

import urllib
from bs4 import BeautifulSoup

url = "http://stats.ncaa.org/team/stats?org_id=413&sport_year_ctl_id=12020"

html = urllib.urlopen(url).read()
soup = BeautifulSoup(html)
# print soup

team_stats = None
player_stat_trs = soup.find_all('tr', attrs={'class':'text'})
for player_stat_tr in player_stat_trs:
    player_stat_list = player_stat_tr.find_all('td')
    if player_stat_list[1].string != 'TEAM' and player_stat_list[1].string != 'Player':
        stats = {
            'minutes_played':player_stat_list[7].string,
            'field_goals_made':player_stat_list[8].string,
            'field_goals_attempted':player_stat_list[9].string,
            'field_goals_percentage':player_stat_list[10].string,
            'three_field_goals_made':player_stat_list[11].string,
            'three_field_goals_attempted':player_stat_list[12].string,
            'three_field_goals_percentage':player_stat_list[13].string,
            'free_throws_made':player_stat_list[14].string,
            'free_throws_attempted':player_stat_list[15].string,
            'free_throws_percentage':player_stat_list[16].string,
            'points':player_stat_list[17].string,
            'average_points':player_stat_list[18].string,
            'offensive_rebounds':player_stat_list[19].string,
            'defensive_rebounds':player_stat_list[20].string,
            'total_rebounds':player_stat_list[21].string,
            'average_rebounds':player_stat_list[22].string,
            'assists': player_stat_list[23].string,
            'turnovers':player_stat_list[24].string,
            'steals':player_stat_list[25].string,
            'blocks':player_stat_list[26].string,
            'fouls':player_stat_list[27].string,
            'double_doubles':"0" if player_stat_list[28].string == u'\xa0' else player_stat_list[28].string,
            'triple_doubles':"0" if player_stat_list[29].string == u'\xa0' else player_stat_list[29].string
        }

    if player_stat_list[1].string == 'TEAM':
        team_stats = {
            'team_points':player_stat_list[17].string,
            'team_average_points':player_stat_list[18].string,
            'team_offensive_rebounds':player_stat_list[19].string,
            'team_defensive_rebounds':player_stat_list[20].string,
            'team_total_rebounds':player_stat_list[21].string,
            'team_average_rebounds':player_stat_list[22].string,
            'team_assists': player_stat_list[23].string,
            'team_turnovers':player_stat_list[24].string,
            'team_steals':player_stat_list[25].string,
            'team_blocks':player_stat_list[26].string,
            'team_fouls':player_stat_list[27].string,
            'double_doubles':"0" if (player_stat_list[28].string == u'\xa0' or player_stat_list[28].string == None)\
                                    else player_stat_list[28].string,
            'triple_doubles':"0" if (player_stat_list[29].string == u'\xa0' or player_stat_list[29].string == None)\
                                    else player_stat_list[29].string
        }
        print player_stat_list
        print player_stat_list[28]
