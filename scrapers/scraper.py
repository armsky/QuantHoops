__author__ = 'Hao Lin'

import urls
from QuantHoops.NCAA.ncaa import *

import urllib
import re
from bs4 import BeautifulSoup
from scraper_helper import *

from dateutil.parser import *
from sqlalchemy import *
from sqlalchemy.orm import relationship, backref, sessionmaker, reconstructor
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql://hooper:michael@localhost/QuantHoops', echo=True)
Session = sessionmaker(bind=engine, autocommit=True, autoflush=False)
session = Session()





def team_parser(season_id, division):
    try:
        row = session.query(Season).filter_by(id=season_id).first()
        gender = row.gender
        url = "http://stats.ncaa.org/team/inst_team_list/%s?division=%s" % (season_id, division)
        team_links = get_team_link(url)

        team_records = list()
        for team in team_links:
            ncaa_id = int(team["href"].split("=")[-1])
            name = team.string

            team_record = Team(name, gender, ncaa_id)
            if session.query(Team).filter_by(id=ncaa_id).first() is None:
                team_records.append(team_record)
        session.add_all(team_records)
        # session.commit()

    except:
        session.rollback()
        raise


def squad_parser(season_id, division):
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
                squad_record = Squad(division, year, team_record)
                squad_records.append(squad_record)
                print year, division, ncaa_id

        session.add_all(squad_records)
        # session.commit()

    except:
        session.rollback()
        raise


def conference_parser(season_id, division):
    try:
        row = session.query(Season).filter_by(id=season_id).first()
        year = row.year
        url = "http://stats.ncaa.org/team/inst_team_list/%s?division=%s" % (season_id, division)
        soup = soupify(url)
        # print soup
        conference_a_list = list(set([x.find('a') for x in soup.findAll('li')]))
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
        squad_records = []
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
                    # session.commit()

        session.flush()

    except:
        session.rollback()
        raise


def schedule_parser(season_id, team_id):
    year = session.query(Season).filter_by(id=season_id).first().year
    url = "http://stats.ncaa.org/team/index/%s?org_id=%s" % (season_id, team_id)
    soup = soupify(url)
    game_ids = []
    schedule_records = []
    #TODO: there maybe team not in NCAA, they don't have <a> tag
    links = soup.find_all('table')[1].find_all(lambda tag: tag.name == 'a' and tag.findParent('td', attrs={'class':'smtext'}))
    opponent_flag = False
    for link in links:
        print link
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
            # A neutral Game
            else:
                team_type = "neutral"
                opponent_type = "neutral"

            # Both teams are NCAA team
            opponent_flag = True

        #contains game information (id, score and other vital statistics)
        elif re.search("game", link["href"]):
            game_id = int(link["href"].split("?")[0].split("/")[3])
            if game_id == 587470:
                print "+++++"
                print season_id, team_id
            game_ids.append(game_id)
            score_string_list = link.string.split(" ")

            # A regular game
            # Both winner_id and loser_id will be squad_id
            if score_string_list[0] == "W":
                winner_id = session.query(Squad).filter(Squad.team_id == team_id,
                                                        Squad.year == year).first().id
                #A tournament game
                if not opponent_flag:
                    # Use fake squad_id (0) and fake year (0)
                    loser_id = session.query(Squad).filter(Squad.team_id == 0,
                                                           Squad.year == 0).first().id
                else:
                    loser_id = session.query(Squad).filter(Squad.team_id == opponent_id,
                                                           Squad.year == year).first().id
                winner_score = score_string_list[1]
                loser_score = score_string_list[3]
            #score_string_list[0] == "L"
            else:
                loser_id = session.query(Squad).filter(Squad.team_id == team_id,
                                                       Squad.year == year).first().id
                #A tournament game
                if not opponent_flag:
                    #set up a fake squad_id (0) and fake year
                    winner_id = session.query(Squad).filter(Squad.team_id == 0,
                                                            Squad.year == 0).first().id
                else:
                    winner_id = session.query(Squad).filter(Squad.team_id == opponent_id,
                                                            Squad.year == year).first().id

                winner_score = score_string_list[3]
                loser_score = score_string_list[1]



            print winner_id, loser_id
            if session.query(Game).filter_by(id=game_id).first() is None:
                game_record = Game(game_id, winner_id, loser_id, winner_score, loser_score)
                session.add(game_record)
                # session.commit()

            # Create Schedule records based on two teams
            if opponent_flag:
                if game_id and session.query(Schedule).filter_by(game_id=game_id).first() is None:

                    session.add_all([Schedule(game_id,winner_id,team_type),
                                    Schedule(game_id,loser_id,opponent_type)])
                    # session.commit()
                opponent_flag = False
            # One of the team if not a NCAA team
            else:
                # Create Schedule records based on one teams
                team_type = "tournament"
                if game_id and session.query(Schedule).filter_by(game_id=game_id).first() is None:
                    squad_id = session.query(Squad).filter(Squad.team_id == team_id,
                                                        Squad.year == year).first().id
                    session.add(Schedule(game_id,squad_id,team_type))
                    # session.commit()


def game_parser():
    """
    Check the game_id before parse, since the page should be the same
    i.e.:
    http://stats.ncaa.org/game/index/2785974?org_id=260
    http://stats.ncaa.org/game/index/2785974?org_id=133
    :param game_id:
    :return:
    """
    game_records = session.query(Game).distinct(Game.id).all()
    for game_record in game_records:
        try:
            game_id = game_record.id
            # In case the winner is not a NCAA team
            if game_record.winner_id != 0:
                team_id = session.query(Squad).filter_by(id=game_record.winner_id).first().team_id
            else:
                team_id = session.query(Squad).filter_by(id=game_record.loser_id).first().team_id

            print game_id, team_id

            url = "http://stats.ncaa.org/game/index/%s?org_id=%s" % (game_id, team_id)
            soup = soupify(url)

            game_details = soup.find_all('table')[2]
            game_record.date = parse(game_details.find_all('td')[1].string.split(' ')[0]).date()
            game_record.location = game_details.find_all('td')[3].string
            try:
                game_record.attendance = int(game_details.findAll('td')[5].contents[0].replace(',',''))
            except:
                game_record.attendance = None
            game_record.officials = soup.findAll('table')[3].findAll('td')[1].string.strip()

            session.add(game_record)
            print game_record.date, game_record.location, game_record.attendance, game_record.officials
        except IndexError, index_error:
            error_message = """

                game_id: %s
                team_id: %s
                page: %s
                may not exists.
            """ % (game_id, team_id, url)
            write_error_to_file(str(index_error)+error_message)
            continue
        except Exception, e:
            write_error_to_file(e)
            raise


def player_parser(season_id, team_id):
    year = session.query(Season).filter_by(id=season_id).first().year
    squad = session.query(Squad).filter(Squad.year == year,
                                    Squad.team_id == team_id).first()
    if squad:
        squad_id = squad.id
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


    # If this season&squad combination doesn't exist
    else:
        error_message = """

            season_id: %s
            team_id: %s
            This combination may not exists.
        """ % (season_id, team_id)
        write_error_to_file(error_message)


def player_stat_parser(season_id, team_id):
    squadmember_id = 1
    game_id = 523250
    stats = {
        'minutes_played':1,
        'field_goals_made':1,
        'field_goals_attempted':1,
        'field_goals_percentage':1,
        'three_field_goals_made':1,
        'three_field_goals_attempted':1,
        'three_field_goals_percentage':1,
        'free_throws_made':1,
        'free_throws_attempted':1,
        'free_throws_percentage':1,
        'points':1,
        'average_points':1,
        'offensive_rebounds':1,
        'defensive_rebounds':1,
        'total_rebounds':1,
        'average_rebounds':1,
        'turnovers':1,
        'steals':1,
        'blocks':1,
        'fouls':1,
        'double_doubles':1,
        'triple_doubles':1
    }
    player_stat_record = PlayerStatSheet(squadmember_id, game_id)
    session.add(player_stat_record)
    print player_stat_record


#Insert all Teams and Squads (for Men)
# rows = session.query(Season).all()
# try:
#     for row in rows:
#         season_id = row.id
#         print season_id
#         # for i in ["1", "2", "3"]:
#
#             # team_parser(season_id, i)
#             # squad_parser(season_id, i)
#             # conference_parser(season_id, i)
#
#         teams = session.query(Team).all()
#         for team in teams:
#             team_id = team.id
#             if team_id != 0:
#                 print "###############"
#                 print season_id, team_id
#                 # schedule_parser(season_id, team_id)
#                 player_parser(season_id, team_id)
# except Exception, e:
#     write_error_to_file(str(e))



player_stat_parser(11,12)
session.close()
