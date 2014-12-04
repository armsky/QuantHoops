__author__ = 'Hao Lin'

import urllib
from bs4 import BeautifulSoup

#url = "http://stats.ncaa.org/team/index/11540?org_id=26172"
# url = "http://stats.ncaa.org/team/inst_team_list/11540?division=1.0"
url = "http://stats.ncaa.org/game/box_score/28633"

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
else:
    team_id = int(team_links[0]["href"].split("=")[-1])

for table in tables[4:]:
    if table.find_all('tr', {"class":"smtext"})[0].find_all('td')[0].a == None:
        continue

    if len(team_links) == 2:
        #table[4] is the first team
        if tables.index(table) == 4:
            team_id = first_team_id
        #table[5] is the second team
        elif tables.index(table) == 5:
            team_id = second_team_id
    try:
        player_stat_tr_list = table.find_all('tr', {"class":"smtext"})
        for player_stat_tr in player_stat_tr_list:
            player_stat_list = player_stat_tr.find_all('td')
            # player_stat
            if player_stat_list[0].a != None:
                player_id = player_stat_list[0].find('a')['href'].split("=")[-1]

                # A number followed by '*' means season high
                # A number followed by '/' means game high
                # A number followed by '-' means team high
                translate_table = dict((ord(char), u'') for char in "*/-")
                stats = {
                    'minutes_played':player_stat_list[2].string.translate(translate_table),
                    'field_goals_made':player_stat_list[3].string.translate(translate_table),
                    'field_goals_attempted':player_stat_list[4].string.translate(translate_table),
                    'three_field_goals_made':player_stat_list[5].string.translate(translate_table),
                    'three_field_goals_attempted':player_stat_list[6].string.translate(translate_table),
                    'free_throws_made':player_stat_list[7].string.translate(translate_table),
                    'free_throws_attempted':player_stat_list[8].string.translate(translate_table),
                    'points':player_stat_list[9].string.translate(translate_table),
                    'offensive_rebounds':player_stat_list[10].string.translate(translate_table),
                    'defensive_rebounds':player_stat_list[11].string.translate(translate_table),
                    'total_rebounds':player_stat_list[12].string.translate(translate_table),
                    'assists': player_stat_list[13].string.translate(translate_table),
                    'turnovers':player_stat_list[14].string.translate(translate_table),
                    'steals':player_stat_list[15].string.translate(translate_table),
                    'blocks':player_stat_list[16].string.translate(translate_table),
                    'fouls':player_stat_list[17].string.translate(translate_table)
                }
                print stats

            # TEAM stats
            elif player_stat_list[0].a is None and (player_stat_list[0].string.strip() == 'TEAM' or \
                                                    player_stat_list[0].string.strip() == 'Team'):
                translate_table = dict((ord(char), u'') for char in "*/-")
                team_stats = {
                    'team_offensive_rebounds':player_stat_list[10].string.translate(translate_table),
                    'team_defensive_rebounds':player_stat_list[11].string.translate(translate_table),
                    'team_total_rebounds':player_stat_list[12].string.translate(translate_table),
                    'team_turnovers':player_stat_list[14].string.translate(translate_table),
                    'team_fouls':player_stat_list[17].string.translate(translate_table),
                }

        # Squad total stats
        total_stat_tr = table.find_all('tr', {"class":"grey_heading"})[1]
        total_stat_list = total_stat_tr.find_all("td", {"align":"right"})
        translate_table = dict((ord(char), u'') for char in "*/-")
        total_stats = {
            'minutes_played':total_stat_list[0].string.translate(translate_table),
            'field_goals_made':total_stat_list[1].string.translate(translate_table),
            'field_goals_attempted':total_stat_list[2].string.translate(translate_table),
            'three_field_goals_made':total_stat_list[3].string.translate(translate_table),
            'three_field_goals_attempted':total_stat_list[4].string.translate(translate_table),
            'free_throws_made':total_stat_list[5].string.translate(translate_table),
            'free_throws_attempted':total_stat_list[6].string.translate(translate_table),
            'points':total_stat_list[7].string.translate(translate_table),
            'offensive_rebounds':total_stat_list[8].string.translate(translate_table),
            'defensive_rebounds':total_stat_list[9].string.translate(translate_table),
            'total_rebounds':total_stat_list[10].string.translate(translate_table),
            'assists': total_stat_list[11].string.translate(translate_table),
            'turnovers':total_stat_list[12].string.translate(translate_table),
            'steals':total_stat_list[13].string.translate(translate_table),
            'blocks':total_stat_list[14].string.translate(translate_table),
            'fouls':total_stat_list[15].string.translate(translate_table)
        }


    except:
        raise