__author__ = 'Hao Lin'

import sys
import getopt
sys.path.insert(1, '../NCAA')
from ncaa import *
import settings
from scraper import *
from sqlalchemy import *


def fix_game_with_no_date(engine):
    session = settings.create_session(engine)
    games = session.query(Game).filter_by(date=None).order_by(asc(Game.id)).all()
    for game_record in games:
        game_parser(session, game_record)
    session.close()


def fix_dup_gamestat(engine):
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


def fix_only_one_gamestat(engine):
    session = settings.create_session(engine)

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

    elif process == "all":
        fix_game_with_no_date(engine)
        fix_dup_gamestat(engine)
    else:
        print "Process name not exists... Quit"
        sys.exit()

if __name__ == "__main__":
    main(sys.argv[1:])