__author__ = 'Hao Lin'

import urls
from QuantHoops.NCAA.ncaa import *

import urllib
import re
from bs4 import BeautifulSoup
from scraper_helper import *

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref, sessionmaker, reconstructor
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql://hooper:michael@localhost/QuantHoops', echo=False)
Session = sessionmaker(bind=engine)
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
        session.commit()

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
            # else:
            #     print "$$$$$$"
                print year, division, ncaa_id
        session.add_all(squad_records)
        session.commit()

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
        for conference in conference_a_list:
            if conference and re.search("changeConference", conference["href"]):
                conference_id = conference["href"].split("(")[1].split(".")[0]
                if conference_id != "-1);" and conference_id != "0":
                    conference_name = conference.string
                    if session.query(Conference).filter_by(id=conference_id).first() is None:
                        conference_record_list.append(Conference(conference_id, conference_name))

                        url = "http://stats.ncaa.org/team/inst_team_list?academic_year=%s&amp;" \
                            "conf_id=%s&amp;division=%s&amp;sport_code=MBB" % (year, conference_id, division)
                        team_links = get_team_link(url)
                        for team_link in team_links:
                            ncaa_id = int(team_link["href"].split("=")[1])
                            

        session.add_all(conference_record_list)
        session.commit()



    except:
        session.rollback()
        raise





def schedule_parser(season_id, team_id):
    url = "http://stats.ncaa.org/team/index/%s?org_id=%s" % (season_id, team_id)
    soup = soupify(url)

    game_ids = []
    links = soup.find_all('table')[1].find_all(lambda tag: tag.name == 'a' and tag.findParent('td', attrs={'class':'smtext'}))
    for link in links:
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

        #contains game information (id, score and other vital statistics)
        elif re.search("game", link["href"]):
            print link
            game_id = int(link["href"].split("?")[0].split("/")[3])
            game_ids.append(game_id)
            score_string_list = link.string.split(" ")

            # if score_string_list[0] == "W":
        # Create Schedule records based on two teams
        if game_id and session.query(Schedule).filter_by(game_id=game_id).first() is None:
                session.add_all([Schedule(game_id,team_id,team_type),
                                Schedule(game_id,opponent_id,opponent_type)])
    #
    # for game_id in game_ids:
    #     print game_id
        # game_parser(game_id)
    #use team id to search squad id






def game_parser(game_id):
    """
    Check the game_id before parse, since the page should be the same
    i.e.:
    http://stats.ncaa.org/game/index/2785974?org_id=260
    http://stats.ncaa.org/game/index/2785974?org_id=133
    :param game_id:
    :return:
    """
    print "some"




# Insert all Teams and Squads (for Men)
rows = session.query(Season).all()
for row in rows:
    season_id = row.id

    print season_id
    for i in ["1", "2", "3"]:
        # print "###############"
        # team_parser(season_id, i)
        # squad_parser(season_id, i)
        conference_parser(season_id, i)

session.close()