__author__ = 'Hao Lin'

from scraper import  *

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql://hooper:michael@localhost/QuantHoops', echo=True)
Session = sessionmaker(bind=engine, autocommit=True, autoflush=False)


#TODO Too much scraping time might got connection confused

#TODO Manully add fake team and fake squad as non-ncaa team
#fake team: id=0, name=non-ncaa team, gender=Men
#fake squad: id=0, team_id=0, season_id=None, year=0

def initial_team_squad_scrap():
    session = Session()
    rows = session.query(Season).all()
    session.close()
    try:
        for row in rows:
            season_id = row.id
            print season_id
            if season_id == 10260:
                for i in ["1", "2", "3"]:
                    session = Session()
                    # year 2010 only has division I
                    if season_id == "10260" and i != "1":
                        continue
                    # year 2011 only has division I and III
                    elif season_id == "10440" and i == "2":
                        continue
                    else:
                        team_parser(session, season_id, i)
                        squad_parser(session, season_id, i)
                        conference_parser(session, season_id, i)
                        session.close()
    except Exception, e:
        error_message = """

        season_id: %s
        division: %s
        This combination may not exists.

        %s
        """ % (season_id, i, e)
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




# initial_team_squad_scrap()

# initial_schedule_game_player_scrap()

initial_season_stat_scrap()

# initial_game_stat_scrap()
