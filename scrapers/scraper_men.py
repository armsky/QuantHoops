__author__ = 'Hao Lin'

import re
import sys
from QuantHoops.NCAA.ncaa_men import *
from scraper_helper import *
from dateutil.parser import *
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql://root:QuantH00p!@localhost/Men_NCAA', echo=True)
Session = sessionmaker(bind=engine, autocommit=True, autoflush=False)


def team_parser(session, season_id, division):
    try:
        row = session.query(Season).filter_by(id=season_id).first()
        url = "http://stats.ncaa.org/team/inst_team_list/%s?division=%s" % (season_id, division)
        team_links = get_team_link(url)

        team_records = list()
        for team in team_links:
            ncaa_id = int(team["href"].split("=")[-1])
            name = team.string

            team_record = Team(name, ncaa_id)
            if session.query(Team).filter_by(id=ncaa_id).first() is None:
                team_records.append(team_record)
        session.add_all(team_records)
        session.flush()

    except:
        session.rollback()
        raise


def squad_parser(session, season_id, division):
    try:
        row = session.query(Season).filter_by(id=season_id).first()
        year = row.year
        url = "http://stats.ncaa.org/team/inst_team_list/%s?division=%s" % (season_id, division)
        team_links = get_team_link(url)

        squad_records = list()
        for team in team_links:
            ncaa_id = int(team["href"].split("=")[1])
            # name = team.string
            team_record = session.query(Team).filter_by(id=ncaa_id).first()
            print team_record.id, year, division

            if session.query(Squad).filter(Squad.year == year,
                                    Squad.division == division,
                                    Squad.team_id == ncaa_id).first() is None:
                squad_record = Squad(division, season_id, year, team_record.id)
                squad_records.append(squad_record)
                print year, division, ncaa_id

        session.add_all(squad_records)
        session.flush()

    except:
        session.rollback()
        raise


def conference_parser(session, season_id, division):
    try:
        row = session.query(Season).filter_by(id=season_id).first()
        year = row.year
        url = "http://stats.ncaa.org/team/inst_team_list/%s?division=%s" % (season_id, division)
        soup = soupify(url)
        conference_a_list = list(set([x.find('a') for x in soup.find_all('li')]))
        conference_record_list = []
        conference_id_list = []
        for conference in conference_a_list:
            if conference and re.search("changeConference", conference["href"]):
                conference_id = conference["href"].split("(")[1].split(".")[0]
                if conference_id != "-1);" and conference_id != "0":
                    conference_id_list.append(conference_id)
                    conference_name = conference.string
                    if session.query(Conference).filter_by(id=conference_id).first() is None:
                        conference_record_list.append(Conference(conference_id, conference_name))
                        session.add(Conference(conference_id, conference_name))

        #update Squad records with conference information
        for conference_id in conference_id_list:
            url = "http://stats.ncaa.org/team/inst_team_list?academic_year=%s&amp;" \
                "conf_id=%s&amp;division=%s&amp;sport_code=MBB" % (year, conference_id, division)
            team_links = get_team_link(url)
            for team_link in team_links:
                team_id = int(team_link["href"].split("=")[1])
                print "******"
                print team_id, year, division
                squad_record = session.query(Squad).filter(Squad.team_id == team_id,
                                             Squad.year == year,
                                             Squad.division == division).first()
                if squad_record:
                    squad_record.conference_id = conference_id
                    session.add(squad_record)

        session.flush()

    except:
        session.rollback()
        raise


def schedule_parser(session, squad_record):
    squad_id = squad_record.id
    team_id = squad_record.team_id
    season_id = squad_record.season_id
    url = "http://stats.ncaa.org/team/index/%s?org_id=%s" % (season_id, team_id)
    soup = soupify(url)
    #TODO: there maybe team not in NCAA, they don't have <a> tag
    try:
        links = soup.find_all('table')[1].find_all(lambda tag: tag.name == 'a' and tag.findParent('td', attrs={'class':'smtext'}))
        opponent_flag = False
        for link in links:
            print link
            winner_id = None
            loser_id = None
            #contains home/away information
            game_id = None
            if re.search("team", link["href"]):
                #TODO: What if there are incomplete data for upcoming season
                opponent_id = int(link["href"].split("?")[1].split("=")[1])
                opponent_name = link.contents[0].strip()

                # A game with home and away team
                if len(link.contents) == 1:
                    #The opponent is the home team
                    if "@ " in opponent_name:
                        opponent_type = "home"
                        team_type = "away"
                    #The opponent is the away team
                    else:
                        team_type = "home"
                        opponent_type = "away"
                # A neutral game
                else:
                    team_type = "neutral"
                    opponent_type = "neutral"

                # Both teams are NCAA team
                opponent_flag = True

            #contains game information (id, score and other vital statistics)
            elif re.search("game", link["href"]):
                game_id = int(link["href"].split("?")[0].split("/")[3])
                # game_ids.append(game_id)
                # An example of score_string: W 91 - 88 (2OT)
                score_string_list = link.string.split(" ")

                # A regular game
                try:
                    # Both winner_id and loser_id will be squad_id
                    if score_string_list[0] == "W":
                        winner_id = squad_id
                        #A tournament game
                        if not opponent_flag:
                            # Use fake squad_id (0) and fake year (0)
                            loser_id = session.query(Squad).filter(Squad.team_id == 0,
                                                                   Squad.year == 0).first().id
                        else:
                            loser_id = session.query(Squad).filter(Squad.team_id == opponent_id,
                                                                   Squad.season_id == season_id).first().id
                        winner_score = score_string_list[1]
                        loser_score = score_string_list[3]
                    #score_string_list[0] == "L"
                    else:
                        loser_id = squad_id
                        #A tournament game
                        if not opponent_flag:
                            #set up a fake squad_id (0) and fake year
                            winner_id = session.query(Squad).filter(Squad.team_id == 0,
                                                                    Squad.year == 0).first().id
                        else:
                            winner_id = session.query(Squad).filter(Squad.team_id == opponent_id,
                                                                    Squad.season_id == season_id).first().id

                        winner_score = score_string_list[3]
                        loser_score = score_string_list[1]
                except:
                    message = """
                    team_id: %s
                    season_id: %s
                    do not have valid page to scrap""" % (opponent_id, season_id)
                    write_error_to_file(message)
                    pass

                print winner_id, loser_id
                if winner_id and loser_id:
                    if session.query(Game).filter_by(id=game_id).first() is None:
                        game_record = Game(game_id, winner_id, loser_id, winner_score, loser_score)
                        session.add(game_record)
                        session.flush()
                        game_parser(session, game_record)

                    # Create Schedule records based on two teams
                    if opponent_flag:
                        if game_id and session.query(Schedule).filter_by(game_id=game_id).first() is None:

                            session.add_all([Schedule(game_id,winner_id,team_type),
                                            Schedule(game_id,loser_id,opponent_type)])
                        opponent_flag = False
                    # One of the team if not a NCAA team
                    else:
                        # Create Schedule records based on one teams
                        team_type = "tournament"
                        if game_id and session.query(Schedule).filter_by(game_id=game_id).first() is None:
                            session.add(Schedule(game_id,squad_id,team_type))
            session.flush()
    except Exception, e:
        message="""
        url: %s
        This page has something wrong
        %s
        """ % (url, str(e))
        write_error_to_file(message)



def game_parser(session, game_record):
    """
    Check the game_id before parse, since these two pages have the same content
    i.e.:
    http://stats.ncaa.org/game/index/2785974?org_id=260
    http://stats.ncaa.org/game/index/2785974?org_id=133
    :param game_id:
    :return:
    """
    try:
        # In case the winner is not a NCAA team
        game_id = game_record.id
        print "$$$$ game_id: "+str(game_id)

        url = "http://stats.ncaa.org/game/index/%s" % (game_id)
        soup = soupify(url)
        tables = soup.find_all('table')

        #score table could have 0, 1 or 2 OverTime
        score_details = tables[0]
        first_team_tds = score_details.find_all('tr')[1].find_all('td', {"align":"right"})
        second_team_tds = score_details.find_all('tr')[2].find_all('td', {"align":"right"})

        first_team_is_winner = int(first_team_tds[-1].string) > int(second_team_tds[-1].string)
        game_record.winner_first_half_score = first_team_tds[0].string if first_team_is_winner else second_team_tds[0].string
        game_record.loser_first_half_score = second_team_tds[0].string if first_team_is_winner else first_team_tds[0].string
        game_record.winner_second_half_score = first_team_tds[1].string if first_team_is_winner else second_team_tds[1].string
        game_record.loser_second_half_score = second_team_tds[1].string if first_team_is_winner else first_team_tds[1].string
        # If has 1st OT
        if len(first_team_tds) >= 4:
            game_record.winner_first_OT_score = first_team_tds[2].string if first_team_is_winner else second_team_tds[2].string
            game_record.loser_first_OT_score = second_team_tds[2].string if first_team_is_winner else first_team_tds[2].string
        # If has 2nd OT
        if len(first_team_tds) >= 5:
            game_record.winner_second_OT_score = first_team_tds[3].string if first_team_is_winner else second_team_tds[3].string
            game_record.loser_second_OT_score = second_team_tds[3].string if first_team_is_winner else first_team_tds[3].string

        # Game details (date, location, etc) in tables[2]
        game_details = tables[2]
        game_record.date = parse(game_details.find_all('td')[1].string.split(' ')[0]).date()
        game_record.location = game_details.find_all('td')[3].string
        try:
            game_record.attendance = int(game_details.find_all('td')[5].contents[0].replace(',',''))
        except:
            game_record.attendance = None
        game_record.officials = soup.find_all('table')[3].find_all('td')[1].string.strip()

        session.add(game_record)
        print game_record.date, game_record.location, game_record.attendance, game_record.officials
    except IndexError, index_error:
        error_message = """

            game_id: %s
            page: %s
            may not exists.
        """ % (game_id, url)
        write_error_to_file(str(index_error)+error_message)
    except Exception, e:
        write_error_to_file(str(e))
        raise

    finally:
        session.flush()


def player_parser(session, squad_record):
    squad_id = squad_record.id
    season_id = squad_record.season_id
    team_id = squad_record.team_id

    try:
        url = "http://stats.ncaa.org/team/roster/%s?org_id=%s" % (season_id, team_id)
        soup = soupify(url)
        players_info = soup.find('tbody').find_all('tr')
        for one_player in players_info:
            info = one_player.find_all('td')
            jersey = info[0].string
            name = info[1].string
            try:
                player_id = int(float(info[1].find('a')['href'].split('=')[-1]))
            except:
                player_id = None
            position = info[2].string
            height = info[3].string
            year = info[4].string
            games_played = info[5].string
            games_started = info[6].string
            print "$$$$"
            print player_id, squad_id, name, jersey, position,\
                    height, year, games_played, games_started
            if player_id:
                if session.query(Player).filter_by(id=player_id).first() is None:
                    session.add(Player(player_id, name))
                if session.query(SquadMember).filter(SquadMember.squad_id==squad_id,
                                                     SquadMember.player_id==player_id).first() is None:
                    session.add(SquadMember(player_id, squad_id, name, jersey, position,
                                            height, year, games_played, games_started))
        session.flush()

    # If this season&squad combination doesn't exist
    except Exception, e:
        error_message = """

            season_id: %s
            team_id: %s
            This combination may not exists.

            %s
        """ % (season_id, team_id, str(e))
        write_error_to_file(error_message)


def season_stat_parser(session, squad_record):
    squad_id = squad_record.id
    season_id = squad_record.season_id
    team_id = squad_record.team_id

    url = "http://stats.ncaa.org/team/stats?org_id=%s&sport_year_ctl_id=%s" % (team_id, season_id)
    soup = soupify(url)
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
                'double_doubles':player_stat_list[28].string,
                'triple_doubles':player_stat_list[29].string
            }
            player_id = player_stat_list[1].find('a')['href'].split('=')[-1]
            squadmember = session.query(SquadMember).filter(SquadMember.squad_id == squad_id,
                                              SquadMember.player_id == player_id).first()
            if squadmember:
                if session.query(PlayerSeasonStat).filter_by(squadmember_id=squadmember.id).first() is None:
                    print "FOUND 1 player"
                    session.add(PlayerSeasonStat(squadmember.id, stats))
        # session.flush()

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
                'team_double_doubles':player_stat_list[28].string,
                'team_triple_doubles':player_stat_list[29].string
            }


    team_stat_trs = soup.find_all('tr', attrs={'class':'grey_heading'})
    for team_stat_tr in team_stat_trs:
        team_stat_list = team_stat_tr.find_all('td')
        if team_stat_list[1].string == "Totals":
            team_stat_list = team_stat_tr.find_all('td')
            print team_stat_list
            total_stats = {
                    'minutes_played':team_stat_list[7].string,
                    'field_goals_made':team_stat_list[8].string.replace(',',''),
                    'field_goals_attempted':team_stat_list[9].string.replace(',',''),
                    'field_goals_percentage':team_stat_list[10].string,
                    'three_field_goals_made':team_stat_list[11].string.replace(',',''),
                    'three_field_goals_attempted':team_stat_list[12].string.replace(',',''),
                    'three_field_goals_percentage':team_stat_list[13].string,
                    'free_throws_made':team_stat_list[14].string.replace(',',''),
                    'free_throws_attempted':team_stat_list[15].string.replace(',',''),
                    'free_throws_percentage':team_stat_list[16].string,
                    'points':team_stat_list[17].string.replace(',',''),
                    'average_points':team_stat_list[18].string.replace(',',''),
                    'offensive_rebounds':team_stat_list[19].string.replace(',',''),
                    'defensive_rebounds':team_stat_list[20].string.replace(',',''),
                    'total_rebounds':team_stat_list[21].string.replace(',',''),
                    'average_rebounds':team_stat_list[22].string.replace(',',''),
                    'assists': team_stat_list[23].string.replace(',',''),
                    'turnovers':team_stat_list[24].string.replace(',',''),
                    'steals':team_stat_list[25].string.replace(',',''),
                    'blocks':team_stat_list[26].string.replace(',',''),
                    'fouls':team_stat_list[27].string.replace(',',''),
                    'double_doubles':"0" if team_stat_list[28].string == u'\xa0' else team_stat_list[28].string,
                    'triple_doubles':"0" if team_stat_list[29].string == u'\xa0' else team_stat_list[29].string
                }
            #combine Total_stats and Team_stats
            print "$$$$1"
            print total_stats, team_stats
            stats = dict(total_stats.items() + team_stats.items())
            print stats

            if session.query(SquadSeasonStat).filter_by(squad_id=squad_id).first() is None:
                print "$$$ Found squad season stat"
                squad_season_stat_record = SquadSeasonStat(squad_id, stats)
                session.add(squad_season_stat_record)
    session.flush()


def game_stat_parser(session, game_record):
    game_id = game_record.id
    year = str(game_record.date).split('-')[0]
    if int(str(game_record.date).split('-')[1]) >= 10:
        year = str(int(year)+1)
    url = "http://stats.ncaa.org/game/box_score/%s" % game_id
    soup = soupify(url)
    tables = soup.find_all('table')
    #tables[0] has team name and team id
    team_links = list(set([x.find('a') for x in tables[0].find_all('td')]))
    team_links = filter(None, team_links)
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
            print team_id, year
        try:
            squad_record = session.query(Squad).filter(Squad.team_id == team_id,
                                      Squad.year == year).first()
            if squad_record:
                squad_id = squad_record.id
                player_stat_tr_list = table.find_all('tr', {"class":"smtext"})
                for player_stat_tr in player_stat_tr_list:
                    player_stat_list = player_stat_tr.find_all('td')
                    # player_stat
                    if player_stat_list[0].a != None:
                        player_id = player_stat_list[0].find('a')['href'].split("=")[-1]

                        print squad_id, player_id
                        try:
                            squadmember_id = session.query(SquadMember).filter(SquadMember.player_id == player_id,
                                                            SquadMember.squad_id == squad_id).first().id
                        except:
                            message="""
                            game_id: %s
                            squad_id: %s
                            player_id: %s
                            This combination may not exists.
                            """ % (game_id, squad_id, player_id)
                            write_error_to_file(message)
                            print "*****"
                            continue

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
                        # print stats
                        if session.query(PlayerGameStat).filter(PlayerGameStat.squadmember_id==squadmember_id,
                                                             PlayerGameStat.game_id==game_id).first() is None:
                            session.add(PlayerGameStat(squadmember_id, game_id, stats))
                            session.flush()
                    # TEAM stats
                    elif player_stat_list[0].a is None and player_stat_list[0].string.strip() == 'TEAM':
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
            stats = dict(total_stats.items() + team_stats.items())
            if session.query(SquadGameStat).filter(SquadGameStat.squad_id==squad_id,
                                                   SquadGameStat.game_id==game_id).first() is None:
                print "$$$$$ Found squad game stat"
                squad_game_stat_record = SquadGameStat(squad_id, game_id, stats)
                session.add(squad_game_stat_record)

                session.flush()

        except:
            error_message = """
            game_id: %s
            squad_id: %s
            This combination may not exists.
            """ % (game_id, squad_id)
            write_error_to_file(error_message)
            raise

def gamedetail_parser(session, game_record):
    game_id = game_record.id
    print game_id
    url = "http://stats.ncaa.org/game/play_by_play/%s" % game_id
    soup = soupify(url)

    tables = soup.find_all("table")

    score_details = tables[0]
    first_team_tds = score_details.find_all('tr')[1].find_all('td', {"align":"right"})
    second_team_tds = score_details.find_all('tr')[2].find_all('td', {"align":"right"})
    first_team_is_winner = int(first_team_tds[-1].string) > int(second_team_tds[-1].string)
    if first_team_is_winner:
        first_squad_id = game_record.winner_id
        second_squad_id = game_record.loser_id
    else:
        second_squad_id = game_record.winner_id
        first_squad_id = game_record.loser_id

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

        table_trs = table.find_all("tr")
        for one_line in table_trs[1:]:
            score = one_line.find('td', {"align":"center"}).string
            info = one_line.find_all('td', {"class":"smtext"})
            if info:
                time = info[0].string
                if info[1].string is not None:
                    detail = info[1].string
                    squad_id = first_squad_id
                else:
                    detail = info[3].string
                    squad_id = second_squad_id

                if session.query(GameDetail).filter(GameDetail.game_id==game_id,
                                                    GameDetail.section==section,
                                                    GameDetail.time==time,
                                                    GameDetail.detail==detail).first() is None:
                    gamedetail_record = GameDetail(game_id, section, time, score, squad_id, detail)
                    gamedetail_records.append(gamedetail_record)

    session.add_all(gamedetail_records)
    session.flush()



