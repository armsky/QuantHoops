__author__ = 'Hao Lin'

import sys
import getopt
sys.path.insert(1, '../NCAA')
from ncaa import *
import settings
from scraper import *
from sqlalchemy import *


def fix_game_with_no_date(engine):
    """

    :param engine:
    :return: None
    """
    session = settings.create_session(engine)
    games = session.query(Game).filter_by(date=None).order_by(asc(Game.id)).all()
    for game_record in games:
        game_parser(session, game_record)
    session.close()


def fix_dup_gamestat(engine):
    """

    :param engine:
    :return: None
    """
    session = settings.create_session(engine)
    dup_game_id = session.query(SquadGameStat.game_id)\
        .group_by(SquadGameStat.game_id).having(func.count(SquadGameStat.game_id) > 2).all()
    print dup_game_id
    for gamestat_list in dup_game_id:
        game_id = gamestat_list[0]
        dup_records = session.query(SquadGameStat.id, SquadGameStat.squad_id).filter_by(game_id=game_id).all()
        print dup_records
        squad_list = []
        for dup_record in dup_records:
            record_id = dup_record[0]
            squad_id = dup_record[1]
            if squad_id not in squad_list:
                squad_list.append(squad_id)
            else:
                try:
                    session.query(SquadGameStat).filter_by(id=record_id).delete()
                    print record_id, "deleted"
                except:
                    print record_id, "delete failed"

    session.close()


def fix_dup_game_in_one_day(engine):
    """
    This happens rarely. ncaa posted the first game, later they found the data was wrong,
    so they post the second page (with a new assigned game_id) and took down the first page.
    Our database scrapped both of the games page but only need to keep one (the one with
    larger game_id).
    We will skip squad_id = 1 because that represents all non-ncaa squads
    :param engine:
    :return: None
    """
    session = settings.create_session(engine)
    dup_games = session.query(Game.id, Game.date, Game.winner_id).\
        filter(and_(Game.winner_id != 1, Game.loser_id != 1, Game.date != None)).\
        group_by(Game.date, Game.winner_id).having(func.count(Game.id) > 1).all()
    for game_info in dup_games:
        game_id = game_info[0]
        session.query(Game).filter_by(id=game_id).delete()
        print "Game: ", game_id, " deleted."


def fix_only_one_gamestat(engine):
    """
    Some games might only have one stat record due to the broken scraping process.
    (But if the other team is a non-ncaa team, there is no need to fix)
    :param engine:
    :return: None
    """

    session = settings.create_session(engine)
    game_id_list = session.query(SquadGameStat.game_id)\
        .group_by(SquadGameStat.game_id).having(func.count(SquadGameStat.game_id) == 1).all()
    # Compare each game_id in table Schedule
    for game_id_result in game_id_list:
        game_id = game_id_result[0]
        schedules = session.query(Schedule).filter_by(game_id=game_id).all()
        if len(schedules) == 2:
            # Has two schedules for each team, need to be fixed
            game_record = session.query(Game).filter_by(id=game_id).first()
            print game_record
            game_stat_parser(session, game_record)
            print "added 1 game_stat"

    session.close()


def main(argv):
    gender = ''
    process = ''
    season = ''
    try:
        opts, args = getopt.getopt(argv, "g:p:s:", ["gender", "process=", "season="])
    except getopt.GetoptError:
        print 'scheduler.py -g <gender> -p <process> -s <season>'
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-g", "--gender"):
            gender = arg
            if gender != "men" and gender != "women":
                print "Gender wrong, please only use 'Men' or 'Women'."
                sys.exit()
        elif opt in ("-p", "--process"):
            process = arg
        elif opt in ("-s", "--season"):
            season = arg

    engine = settings.create_engine(gender)

    if process == "fix_game_with_no_date" or process == "date":
        fix_game_with_no_date(engine)
    elif process == "fix_dup_gamestat" or process == "dup_gamestat":
        fix_dup_gamestat(engine)
    elif process == "fix_dup_game_in_one_day" or process == "dup_game":
        fix_dup_game_in_one_day(engine)
    elif process == "fix_only_one_gamestat" or process == "single_gamestat":
        fix_only_one_gamestat(engine)
    elif process == "all":
        fix_game_with_no_date(engine)
        fix_dup_gamestat(engine)
    else:
        print "Process name not exists... Quit"
        sys.exit()

if __name__ == "__main__":
    main(sys.argv[1:])