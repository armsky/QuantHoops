__author__ = 'Hao Lin'

from scraper_men import *

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql://root:QuantH00p!@localhost/Men_NCAA', echo=True)
Session = sessionmaker(bind=engine, autocommit=True, autoflush=False)


#TODO Too much scraping time might got connection confused

#TODO Manully add fake team and fake squad as non-ncaa team
#fake team: id=0, name=non-ncaa team
#fake squad: id=0, team_id=0, season_id=None, year=0

def initial_team_squad_scrap():
    session = Session()
    rows = session.query(Season).all()
    session.close()
    try:
        for row in rows:
            season_id = row.id
            print season_id
            for division in ["1", "2", "3"]:
                session = Session()
                # Men&Women year 2010 only has division I
                if season_id == "10260" or season_id == "10261":
                    if division != "1":
                        continue
                # Men&Women year 2011 only has division I and III
                if season_id == "10440" or season_id == "10420":
                    if division == "2":
                        continue
                team_parser(session, season_id, division)
                squad_parser(session, season_id, division)
                conference_parser(session, season_id, division)
                session.close()
    except Exception, e:
        error_message = """

        season_id: %s
        division: %s
        This combination may not exists.

        %s
        """ % (season_id, division, e)
        write_error_to_file(error_message)
        raise

def initial_schedule_game_player_scrap():
    session = Session()
    squads = session.query(Squad).all()
    session.close()
    try:
        for squad_record in squads:
            if squad_record.id != 0:
                session = Session()
                schedule_parser(session, squad_record)
                #game_parser() is inside schedule_parser()
                player_parser(session, squad_record)
                #squadmember_parser() is inside player_parser()
                session.close()

    except Exception, e:
        error_message = """

        squad_id: %s
        This combination may not exists.

        %s
        """ %  (squad_record.id, e)
        write_error_to_file(str(error_message))
        raise


def initial_season_stat_scrap():
    session = Session()
    squads = session.query(Squad).all()
    session.close()

    try:
        for squad_record in squads:
            if squad_record.id != 0:
                session = Session()
                season_stat_parser(session, squad_record)


    except Exception, e:
        message = """

        squad_id: %s
        team_id: %s
        season_id: %s
        This combination may not exists.

        %s
        """ %  (squad_record.id, squad_record.season_id, squad_record.team_id, e)
        write_error_to_file(str(message))
        raise


def initial_game_stat_scrap():
    session = Session()
    games = session.query(Game).all()
    session.close()
    try:
        for game_record in games:
            print "%%%%"+str(game_record.id)
            session = Session()
            game_stat_parser(session, game_record)
            session.close()

    except :
        message = """
        game_id: %s
        Something wrong in game_stat_parser
        """ % (game_record.id)
        write_error_to_file(message)
        raise


def initial_game_detail_scrap():
    session = Session()
    games = session.query(Game).all()
    session.close()
    for game_record in games:
        session = Session()
        gamedetail_parser(session, game_record)
        session.close()


initial_team_squad_scrap()

# initial_schedule_game_player_scrap()

# initial_season_stat_scrap()

# initial_game_stat_scrap()

# initial_game_detail_scrap()