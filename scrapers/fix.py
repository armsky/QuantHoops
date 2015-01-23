__author__ = 'Hao Lin'

import sys
import getopt
sys.path.insert(1, '../NCAA')
from ncaa import *
import settings
from scraper import *
from sqlalchemy import *
import datetime


def fix_game_with_no_date(engine):
    session = settings.create_session(engine)
    games = session.query(Game).filter_by(date=None).order_by(asc(Game.id)).all()
    for game_record in games:
        game_parser(session, game_record)


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

    elif process == "all":
        fix_game_with_no_date(engine)
    else:
        print "Process name not exists... Quit"
        sys.exit()

if __name__ == "__main__":
    main(sys.argv[1:])