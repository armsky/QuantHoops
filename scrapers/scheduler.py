__author__ = 'Hao Lin'

import sys
import getopt
sys.path.insert(1, '../NCAA')
from ncaa import *
import settings
from scraper import *
from sqlalchemy import *
import datetime


def initial_team_squad_scrap(engine):
    session = settings.create_session(engine)
    seasons = session.query(Season).all()
    session.close()
    try:
        for season_record in seasons:
            season_id = season_record.id
            print "#####"+str(season_id), str(datetime.datetime.now())
            for division in [1, 2, 3]:
                session = settings.create_session(engine)
                # Men&Women year 2010 only has division I
                if season_id == 10260 or season_id == 10261:
                    if division != 1:
                        print "$$$$"
                        print division, season_id
                        continue
                # Men&Women year 2011 only has division I and III
                if season_id == 10440 or season_id == 10420:
                    if division == 2:
                        print "$$$$"
                        print division, season_id
                        continue
                print "*****", str(datetime.datetime.now())
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


def initial_schedule_game_player_scrap(engine, season):
    squad_id_finish_list = []

    session = settings.create_session(engine)
    if season:
        season_year = int(season)
        squads = session.query(Squad).filter_by(year=season_year).all()
    else:
        squads = session.query(Squad).all()
    squadmembers_per_squad = session.query(SquadMember).group_by(SquadMember.squad_id).all()

    for squadmember_record in squadmembers_per_squad:
        squad_id_finish_list.append(squadmember_record.squad_id)
    session.close()

    try:
        for squad_record in squads:
            # If the squad_id != fake_id (non-ncaa squad id)
            if squad_record.id != 1:
                session = settings.create_session(engine)
                schedule_parser(session, squad_record)
                # game_parser() is inside schedule_parser()
                if squad_record.id not in squad_id_finish_list:
                    player_parser(session, squad_record)
                    # squadmember_parser() is inside player_parser()
                else:
                    print 'Already scrapped, skip squad_id: ', squad_record.id
                session.close()

    except Exception, e:
        error_message = """

        squad_id: %s
        This combination may not exists.

        %s
        """ % (squad_record.id, e)
        write_error_to_file(str(error_message))
        raise


def initial_season_stat_scrap(engine, gender, season):
    session = settings.create_session(engine)
    if season:
        season_year = int(season)
        squads = session.query(Squad).filter_by(year=season_year).all()
    else:
        squads = session.query(Squad).all()
    session.close()

    try:
        for squad_record in squads:
            if squad_record.id != 1:
                print "%%%% squad_id is "+str(squad_record.id), str(datetime.datetime.now())
                session = settings.create_session(engine)
                season_stat_parser(session, squad_record, gender)

    except Exception, e:
        message = """

        squad_id: %s
        team_id: %s
        season_id: %s
        This combination may not exists.

        %s
        """ % (squad_record.id, squad_record.season_id, squad_record.team_id, e)
        write_error_to_file(str(message))
        raise


def initial_game_stat_scrap(engine):
    session = settings.create_session(engine)
    games = session.query(Game).filter_by(has_stat=0).order_by(asc(Game.id)).all()
    session.close()
    try:
        for game_record in games:
            print "%%%% game_id is "+str(game_record.id), str(datetime.datetime.now())
            session = settings.create_session(engine)
            game_stat_parser(session, game_record)
            session.close()
    except Exception, e:
        message = """

        game_id: %s
        Something wrong in game_stat_parser

        %s
        """ % (game_record.id, e)
        write_error_to_file(message)
        raise


def initial_game_detail_scrap(engine):
    session = settings.create_session(engine)
    games = session.query(Game).filter_by(has_detail=0).order_by(asc(Game.id)).all()
    session.close()
    try:
        for game_record in games:
            session = settings.create_session(engine)
            gamedetail_parser(session, game_record)
            session.close()
    except Exception, e:
        message = """

        game_id: %s
        Something wrong in game_detail_parser

        %s
        """ % (game_record.id, e)
        write_error_to_file(message)
        raise


def new_team_squad_scrap(engine):
    session = settings.create_session(engine)
    this_season_id = session.query(func.max(Season.id)).first()[0]
    session.close()

    try:
        print "#####"+str(this_season_id)
        for division in [1, 2, 3]:
            session = settings.create_session(engine)
            print "*****"
            team_parser(session, this_season_id, division)
            squad_parser(session, this_season_id, division)
            conference_parser(session, this_season_id, division)
            session.close()
    except Exception, e:
        error_message = """

        this_season_id: %s
        division: %s
        This combination may not exists.

        %s
        """ % (this_season_id, division, e)
        write_error_to_file(error_message)
        raise


def new_schedule_game_player_scrap(engine):
    session = settings.create_session(engine)
    this_season_id = session.query(func.max(Season.id)).first()[0]
    squads = session.query(Squad).filter_by(season_id=this_season_id).all()
    session.close()
    try:
        for squad_record in squads:
            # If the squad_id != fake_id (non-ncaa squad id)
            if squad_record.id != 1:
                print "####", squad_record.id, str(datetime.datetime.now())
                session = settings.create_session(engine)
                schedule_parser(session, squad_record)
                # game_parser() is inside schedule_parser()
                player_parser(session, squad_record)
                # squadmember_parser() is inside player_parser()
                session.close()
    except Exception, e:
        error_message = """

        squad_id: %s
        This combination may not exists.

        %s
        """ % (squad_record.id, e)
        write_error_to_file(str(error_message))
        raise


def new_season_stat_scrap(engine, gender):
    session = settings.create_session(engine)
    this_season_id = session.query(func.max(Season.id)).first()[0]
    squads = session.query(Squad).filter_by(season_id=this_season_id).all()
    session.close()

    try:
        for squad_record in squads:
            # If the squad_id != fake_id (non-ncaa squad id)
            if squad_record.id != 1:
                print "%%%% squad_id is "+str(squad_record.id), str(datetime.datetime.now())
                session = settings.create_session(engine)
                season_stat_parser(session, squad_record, gender)
                session.close()
    except Exception, e:
        message = """

        squad_id: %s
        team_id: %s
        season_id: %s
        This combination may not exists.

        %s
        """ % (squad_record.id, squad_record.season_id, squad_record.team_id, e)
        write_error_to_file(str(message))
        raise


def new_game_stat_scrap(engine):
    session = settings.create_session(engine)
    games = session.query(Game).filter_by(has_stat=0).order_by(asc(Game.id)).all()
    session.close()
    try:
        for game_record in games:
            print "%%%% game_id is "+str(game_record.id), str(datetime.datetime.now())
            session = settings.create_session(engine)
            game_stat_parser(session, game_record)
            session.close()

    except Exception, e:
        message = """

        game_id: %s
        Something wrong in game_stat_parser

        %s
        """ % (game_record.id, e)
        write_error_to_file(message)
        raise


def new_game_detail_scrap(engine):
    session = settings.create_session(engine)
    games = session.query(Game).filter_by(has_detail=0).order_by(asc(Game.id)).all()
    session.close()
    try:
        for game_record in games:
            print "%%%% game_id is "+str(game_record.id), str(datetime.datetime.now())
            session = settings.create_session(engine)
            gamedetail_parser(session, game_record)
            session.close()
    except Exception, e:
        message = """

        game_id: %s
        Something wrong in game_detail_parser

        %s
        """ % (game_record.id, e)
        write_error_to_file(message)
        raise


def main(argv):
    gender = ''
    ptype = ''
    process = ''
    season = ''
    try:
        opts, args = getopt.getopt(argv, "g:t:p:s:", ["gender", "type=", "process=", "season="])
    except getopt.GetoptError:
        print 'scheduler.py -g <gender> -t <type> -p <process> -s <season>'
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-g", "--gender"):
            gender = arg
            if gender != "men" and gender != "women":
                print "Gender wrong, please only use 'Men' or 'Women'."
                sys.exit()
        elif opt in ("-t", "--type"):
            ptype = arg
        elif opt in ("-p", "--process"):
            process = arg
        elif opt in ("-s", "--season"):
            season = arg

    engine = settings.create_engine(gender)

    # Create fake (non-ncaa) team and squad
    # fake team: id=1, name=non-ncaa team
    # fake squad: id=1, team_id=1, season_id=None, division=0, year=0
    session = settings.create_session(engine)
    if session.query(Team).filter(Team.id==1).first() is None:
        fake_team_record = Team("non-ncaa team", 1)
        session.add(fake_team_record)
        session.flush()
    if session.query(Squad).filter(Squad.team_id==1).first() is None:
        fake_squad_record = Squad(0, None, 0, 1, None)
        session.add(fake_squad_record)
        session.flush()
    session.close()

    if ptype == "new":
        if process == "team_squad" or process == "1":
            new_team_squad_scrap(engine)
        elif process == "schedule_game_player" or process == "2":
            new_schedule_game_player_scrap(engine)
        elif process == "season_stat" or process == "3":
            new_season_stat_scrap(engine, gender)
        elif process == "game_stat" or process == "4":
            new_game_stat_scrap(engine)
        elif process == "game_detail" or process == "5":
            new_game_detail_scrap(engine)
        else:
            print "Process name not exists... Quit"
            sys.exit()
    elif ptype == "initial":
        if process == "team_squad" or process == "1":
            initial_team_squad_scrap(engine)
        elif process == "schedule_game_player" or process == "2":
            initial_schedule_game_player_scrap(engine, season)
        elif process == "season_stat" or process == "3":
            initial_season_stat_scrap(engine, gender, season)
        elif process == "game_stat" or process == "4":
            initial_game_stat_scrap(engine)
        elif process == "game_detail" or process == "5":
            initial_game_detail_scrap(engine)
        else:
            print "Process name not exists... Quit"
            sys.exit()

if __name__ == "__main__":
    main(sys.argv[1:])