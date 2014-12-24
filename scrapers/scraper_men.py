__author__ = 'Hao Lin'

import re
import sys
reload(sys)
sys.setdefaultencoding("utf8")
sys.path.insert(1, '../NCAA')
from ncaa_men import *
from scraper_helper import *
from dateutil.parser import *
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql://root:QuantH00p!@localhost/NCAA_Men', echo=False)
Session = sessionmaker(bind=engine, autocommit=True, autoflush=False)


def team_parser(session, season_id, division):
    try:
        # row = session.query(Season).filter_by(id=season_id).first()
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
            team_id = int(team["href"].split("=")[1])
            team_record = session.query(Team).filter_by(id=team_id).first()

            if session.query(Squad).filter(Squad.year == year,
                                    Squad.division == division,
                                    Squad.team_id == team_id).first() is None:
                squad_record = Squad(division, season_id, year, team_record.id)
                squad_records.append(squad_record)
                print team_id, year, division, "added"

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
        if soup is None:
            error_message = """
            url: %s
            This page may not exist.
            """ % url
            write_error_to_file(error_message)
            return
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
    if soup is None:
        error_message = """
        url: %s
        This page may not exist.
        """ % url
        write_error_to_file(error_message)
        return
    """NOTE: there maybe team not in NCAA, they don't have <a> tag"""
    try:
        # links = soup.find_all('table')[1].find_all(lambda tag: tag.name == 'a' and tag.findParent('td', attrs={'class':'smtext'}))
        tr_list = soup.find('table', attrs={'class':'mytable', 'align':'center'}).find_all('tr')
        for tr in tr_list:
            # This contains game information
            if len(tr.find_all('td')) == 3 and not tr.has_attr('class'):
                both_teams_are_ncaa = False
                winner_id = None
                loser_id = None
                game_td_list = tr.find_all('td', attrs={'class':'smtext'})
                opponent = game_td_list[1].find('a')
                result = game_td_list[2].find('a')
                # This is a future game, skip
                if result is None:
                    print "This is a future game with %s, skip" % game_td_list[1].string.strip() \
                            if len(game_td_list[1]) == 1 else game_td_list[1].contents[2].strip()
                # A game that already happened
                else:
                    # Opponent team is a ncaa team
                    if opponent is not None:
                        opponent_id = int(opponent["href"].split("?")[1].split("=")[1])

                        if len(opponent.contents) == 1:
                            # The opponent is the home team
                            if '@ ' in opponent.contents[0].strip():
                                opponent_type = "home"
                                team_type = "away"
                            # The opponent is the away team
                            else:
                                team_type = "home"
                                opponent_type = "away"
                        # Both teams are neutral
                        else:
                            team_type = "neutral"
                            opponent_type = "neutral"

                        both_teams_are_ncaa = True

                    # A tournament game: Opponent is a non-ncaa team
                    else:
                        print "Opponent team is not a ncaa team"
                        both_teams_are_ncaa = False
                        non_ncaa_id = 1

                    game_id = int(result['href'].split("?")[0].split("/")[-1])
                    print game_id
                    # An example of score_string: W 91 - 88 (2OT)
                    score_string_list = result.string.split(" ")
                    try:
                        if score_string_list[0] == "W":
                            winner_id = squad_id
                            # tournament game
                            if not both_teams_are_ncaa:
                                # Use fake squad_id = 1
                                loser_id = non_ncaa_id
                            # A regular game
                            else:
                                loser_id = session.query(Squad).filter(Squad.team_id == opponent_id,
                                                                    Squad.season_id == season_id).first().id
                            winner_score = score_string_list[1]
                            loser_score = score_string_list[3]
                        elif score_string_list[0] == "L":
                            loser_id = squad_id
                            # tournament game
                            if not both_teams_are_ncaa:
                                # Use fake squad_id = 1
                                winner_id = non_ncaa_id
                            # A regular game
                            else:
                                winner_id = session.query(Squad).filter(Squad.team_id == opponent_id,
                                                                    Squad.season_id == season_id).first().id

                            winner_score = score_string_list[3]
                            loser_score = score_string_list[1]
                    except:
                            message = """
                            team_id: %s
                            season_id: %s
                            do not exist in database""" % (opponent_id, season_id)
                            write_error_to_file(message)
                            pass

                    if winner_id and loser_id:
                        if session.query(Game).filter_by(id=game_id).first() is None:
                            game_record = Game(game_id, winner_id, loser_id, winner_score, loser_score)
                            session.add(game_record)
                            session.flush()
                            game_parser(session, game_record)

                        # Create Schedule records based on two teams
                        if both_teams_are_ncaa:
                            if game_id and session.query(Schedule).filter_by(game_id=game_id).first() is None:

                                session.add_all([Schedule(game_id,winner_id,team_type),
                                                Schedule(game_id,loser_id,opponent_type)])
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
        if soup is None:
            error_message = """
            url: %s
            This page may not exist.
            """ % url
            write_error_to_file(error_message)
            return
        tables = soup.find_all('table')

        #score table could have 0, 1 or 2 OverTime
        score_details = tables[0]
        first_team_tds = score_details.find_all('tr')[1].find_all('td', {"align":"right"})
        second_team_tds = score_details.find_all('tr')[2].find_all('td', {"align":"right"})

        # Some games don't have first and second half (i.e. game: 744710)
        if len(first_team_tds) >= 3:
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
        #TODO: different layout (table)
        game_details = tables[2]
        game_record.date = parse(game_details.find_all('td')[1].string.split(' ')[0]).date()
        game_record.location = game_details.find_all('td')[3].string
        try:
            game_record.attendance = int(game_details.find_all('td')[5].contents[0].replace(',',''))
        except:
            game_record.attendance = None
        # Officials info in the tables[3]
        game_record.officials = tables[3].find_all('td')[1].string.strip()

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
        if soup is None:
            error_message = """
            url: %s
            This page may not exist.
            """ % url
            write_error_to_file(error_message)
            return
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

                squadmember_record = session.query(SquadMember).filter(SquadMember.squad_id==squad_id,
                                                     SquadMember.player_id==player_id).first()
                # Add new squad_member record
                if squadmember_record is None:
                    session.add(SquadMember(player_id, squad_id, name, jersey, position,
                                            height, year, games_played, games_started))
                # Update existing squad_member record
                else:
                    squadmember_record.games_played = games_played
                    squadmember_record.games_started = games_started
                    session.add(squadmember_record)
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
    if soup is None:
        error_message = """
        url: %s
        This page may not exist.
        """ % url
        write_error_to_file(error_message)
        return
    team_stats = None
    opnt_stats = None
    player_stat_trs = soup.find_all('tr', attrs={'class':'text'})
    #TODO: http://stats.ncaa.org/team/stats?org_id=10972&sport_year_ctl_id=12020
    # If this page has an empty table, skip it.
    if not player_stat_trs:
        error_message = """
        url: %s
        This page has empty table, skip.
        """ % url
        write_error_to_file(error_message)
        return
    for player_stat_tr in player_stat_trs:
        player_stat_tds = player_stat_tr.find_all('td')
        if player_stat_tds[1].find('a') is not None:
            player_id = player_stat_tds[1].find('a')['href'].split('=')[-1]
        # Pre-process the list, all none value or white space will be "0"
        player_stat_list = preprocess_stat_list(player_stat_tds)
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
            squadmember = session.query(SquadMember).filter(SquadMember.squad_id == squad_id,
                                              SquadMember.player_id == player_id).first()
            if squadmember:
                if session.query(PlayerSeasonStat).filter_by(squadmember_id=squadmember.id).first() is None:
                    session.add(PlayerSeasonStat(squadmember.id, stats))
                else:
                    # The season is ongoing, update it every time
                    if is_current_season_ongoing(squad_record.year):
                        session.add(PlayerSeasonStat(squadmember.id, stats))
                    # The season is over, don't need to update
                    else:
                        print "squadmember season stat (id=%s) already existed" % squadmember.id

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
    team_stat_tr = team_stat_trs[1]
    # Scrap Team's Total stat
    team_stat_list = preprocess_stat_list(team_stat_tr.find_all('td'))
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
            'double_doubles':team_stat_list[28].string,
            'triple_doubles':team_stat_list[29].string
        }

    # Some page don't have opponent's stat
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

    if team_stats is not None and opnt_stats is not None:
        # Combine Total_stats and Team_stats and Opnt_stats
        stats = dict(total_stats.items() + team_stats.items() + opnt_stats.items())
    elif team_stats is None and opnt_stats is not None:
        stats = dict(total_stats.items() + opnt_stats.items())
    elif team_stats is not None and opnt_stats is None:
        stats = dict(total_stats.items() + team_stats.items())
    else:
        stats = total_stats

    # If this season is over
    if not is_current_season_ongoing(squad_record.year):
        if session.query(SquadSeasonStat).filter_by(squad_id=squad_id).first() is None:
            print "$$$ Found squad season stat"
            squad_season_stat_record = SquadSeasonStat(squad_id, stats)
            session.add(squad_season_stat_record)
        else:
            print "squad season stat (id=%s) already existed" % squad_id
    # The season is ongoing, need to UPDATE database every time
    else:
        squad_season_stat_record = session.query(SquadSeasonStat).filter_by(squad_id=squad_id).first()
        if squad_season_stat_record is None:
            print "$$$ Found squad season stat"
            squad_season_stat_record = SquadSeasonStat(squad_id, stats)
            session.add(squad_season_stat_record)
        else:
            print "$$$ squad season stat need to be updated"
            squad_season_stat_record.update(stats)
            session.add(squad_season_stat_record)

    session.flush()


def game_stat_parser(session, game_record):
    game_id = game_record.id
    # NCAA website has minion portions of games that don't have date information
    # This game usually either has a stat page, so skip it and delete
    if game_record.date is None:
        return
    year = str(game_record.date).split('-')[0]
    if int(str(game_record.date).split('-')[1]) >= 10:
        year = str(int(year)+1)
    url = "http://stats.ncaa.org/game/box_score/%s" % game_id
    soup = soupify(url)
    if soup is None:
        error_message = """
        url: %s
        This page may not exist.
        """ % url
        write_error_to_file(error_message)
        return
    team_stats = None
    tables = soup.find_all('table')
    #tables[0] has team name and team id
    team_links = [x.find('a') for x in tables[0].find_all('td')]
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
                        # Pre-process the list, all none value or white space will be "0"
                        # Also remove the "*/-"
                        player_stat_list = preprocess_stat_list(player_stat_list)

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
                            continue

                        stats = {
                            'minutes_played':player_stat_list[2].string,
                            'field_goals_made':player_stat_list[3].string,
                            'field_goals_attempted':player_stat_list[4].string,
                            'three_field_goals_made':player_stat_list[5].string,
                            'three_field_goals_attempted':player_stat_list[6].string,
                            'free_throws_made':player_stat_list[7].string,
                            'free_throws_attempted':player_stat_list[8].string,
                            'points':player_stat_list[9].string,
                            'offensive_rebounds':player_stat_list[10].string,
                            'defensive_rebounds':player_stat_list[11].string,
                            'total_rebounds':player_stat_list[12].string,
                            'assists': player_stat_list[13].string,
                            'turnovers':player_stat_list[14].string,
                            'steals':player_stat_list[15].string,
                            'blocks':player_stat_list[16].string,
                            'fouls':player_stat_list[17].string
                        }
                        # print stats
                        if session.query(PlayerGameStat).filter(PlayerGameStat.squadmember_id==squadmember_id,
                                                             PlayerGameStat.game_id==game_id).first() is None:
                            session.add(PlayerGameStat(squadmember_id, game_id, stats))
                            session.flush()
                    # TEAM stats
                    elif player_stat_list[0].a is None and (player_stat_list[0].string.strip() == 'TEAM' or \
                                                            player_stat_list[0].string.strip() == 'Team'):
                        # Pre-process the list, all none value or white space will be "0"
                        player_stat_list = preprocess_stat_list(player_stat_list)
                        team_stats = {
                            'team_offensive_rebounds':player_stat_list[10].string,
                            'team_defensive_rebounds':player_stat_list[11].string,
                            'team_total_rebounds':player_stat_list[12].string,
                            'team_turnovers':player_stat_list[14].string,
                            'team_fouls':player_stat_list[17].string,
                        }

            # Squad total stats
            total_stat_tr = table.find_all('tr', {"class":"grey_heading"})[1]
            # Pre-process the list, all none value or white space will be "0"
            # Also remove the "*/-"
            total_stat_list = preprocess_stat_list(total_stat_tr.find_all("td", {"align":"right"}))
            total_stats = {
                'minutes_played':total_stat_list[0].string,
                'field_goals_made':total_stat_list[1].string,
                'field_goals_attempted':total_stat_list[2].string,
                'three_field_goals_made':total_stat_list[3].string,
                'three_field_goals_attempted':total_stat_list[4].string,
                'free_throws_made':total_stat_list[5].string,
                'free_throws_attempted':total_stat_list[6].string,
                'points':total_stat_list[7].string,
                'offensive_rebounds':total_stat_list[8].string,
                'defensive_rebounds':total_stat_list[9].string,
                'total_rebounds':total_stat_list[10].string,
                'assists': total_stat_list[11].string,
                'turnovers':total_stat_list[12].string,
                'steals':total_stat_list[13].string,
                'blocks':total_stat_list[14].string,
                'fouls':total_stat_list[15].string
            }
            if team_stats is not None:
                stats = dict(total_stats.items() + team_stats.items())
                if game_record.has_stat == 0:
                    print "$$$$$ Found squad game stat"
                    squad_game_stat_record = SquadGameStat(squad_id, game_id, stats)
                    session.add(squad_game_stat_record)
                    # Update
                    game_record_to_update = session.query(Game).filter_by(id=game_id).first()
                    game_record_to_update.has_stat = 1
                    session.add(game_record_to_update)
                    session.flush()
                else:
                    print "squad game stat (squad_id=%s, squad_id=%s) already existed" % (squad_id, game_id)

        except:
            error_message = """
            game_id: %s
            squad_id: %s
            This combination may not exists.
            """ % (game_id, squad_id)
            write_error_to_file(error_message)

def gamedetail_parser(session, game_record):
    game_id = game_record.id
    print game_id
    url = "http://stats.ncaa.org/game/play_by_play/%s" % game_id
    soup = soupify(url)
    if soup is None:
        error_message = """
        url: %s
        This page may not exist.
        """ % url
        write_error_to_file(error_message)
        return
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


def is_current_season_ongoing(season_year):
    if int(season_year) < get_current_year():
        return False
    elif int(season_year) == get_current_year():
        if int(get_current_month()) >= 5:
            return False
    else:
        return True

