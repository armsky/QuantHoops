__author__ = 'Hao Lin'

import sys
import getopt
sys.path.insert(1, '../scrapers')
sys.path.insert(1, '../NCAA')
import settings
from scraper import *
from ncaa import *
from sqlalchemy import *


def check_team_stat(engine, season):
    total_squad_num = 0
    matched_num = 0
    unmatch_num = 0
    season_year = int(season)
    session = settings.create_session(engine)
    squad_list = session.query(Squad).filter_by(year=season_year).all()

    try:
        for squad_record in squad_list:
            total_squad_num += 1
            squad_season_record = session.query(SquadSeasonStat).filter_by(squad_id=squad_record.id).first()
            if squad_season_record:
                squad_id = squad_season_record.squad_id
                print "##### squad_id: "+str(squad_id)
                total_stats = {
                    'field_goals_made': squad_season_record.field_goals_made,
                    'field_goals_attempted': squad_season_record.field_goals_attempted,
                    'three_field_goals_made': squad_season_record.three_field_goals_made,
                    'three_field_goals_attempted': squad_season_record.three_field_goals_attempted,
                    'free_throws_made': squad_season_record.free_throws_made,
                    'free_throws_attempted': squad_season_record.free_throws_attempted,
                    'points': squad_season_record.points,
                    'offensive_rebounds': squad_season_record.offensive_rebounds,
                    'defensive_rebounds': squad_season_record.defensive_rebounds,
                    'total_rebounds': squad_season_record.total_rebounds,
                    'assists':  squad_season_record.assists,
                    'turnovers': squad_season_record.turnovers,
                    'steals': squad_season_record.steals,
                    'blocks': squad_season_record.blocks,
                    'fouls': squad_season_record.fouls
                }
                stats_sum = {
                    'field_goals_made': 0,
                    'field_goals_attempted': 0,
                    'three_field_goals_made': 0,
                    'three_field_goals_attempted': 0,
                    'free_throws_made': 0,
                    'free_throws_attempted': 0,
                    'points': 0,
                    'offensive_rebounds': 0,
                    'defensive_rebounds': 0,
                    'total_rebounds': 0,
                    'assists':  0,
                    'turnovers': 0,
                    'steals': 0,
                    'blocks': 0,
                    'fouls': 0
                }
                game_stat_list = session.query(SquadGameStat).filter_by(squad_id=squad_id).all()
                for game_stat_record in game_stat_list:
                    stats = {
                        'field_goals_made': game_stat_record.field_goals_made,
                        'field_goals_attempted': game_stat_record.field_goals_attempted,
                        'three_field_goals_made': game_stat_record.three_field_goals_made,
                        'three_field_goals_attempted': game_stat_record.three_field_goals_attempted,
                        'free_throws_made': game_stat_record.free_throws_made,
                        'free_throws_attempted': game_stat_record.free_throws_attempted,
                        'points': game_stat_record.points,
                        'offensive_rebounds': game_stat_record.offensive_rebounds,
                        'defensive_rebounds': game_stat_record.defensive_rebounds,
                        'total_rebounds': game_stat_record.total_rebounds,
                        'assists':  game_stat_record.assists,
                        'turnovers': game_stat_record.turnovers,
                        'steals': game_stat_record.steals,
                        'blocks': game_stat_record.blocks,
                        'fouls': game_stat_record.fouls
                    }
                    for k, v in stats_sum.iteritems():
                        stats_sum[k] = v + stats.get(k)
                print cmp(total_stats, stats_sum)
                if cmp(total_stats, stats_sum) == 0:
                    matched_num += 1
                else:
                    unmatch_num += 1
                print total_stats
                print stats_sum
                print "========================"
            else:
                print "******"
                print "squad_id: ", str(squad_record.id), "has no season stat"
        print "total squad number: ", total_squad_num
        print matched_num, " of them matched."
        print unmatch_num, " of them are not matched."
    except:
        raise
    session.close()


def check_player_stat(engine, season):
    total_player_num = 0
    matched_num = 0
    unmatch_num = 0
    season_year = int(season)
    session = settings.create_session(engine)
    squad_list = session.query(Squad).filter_by(year=season_year).all()



def main(argv):
    gender = ''
    ptype = ''
    season = ''
    try:
        opts, args = getopt.getopt(argv, "g:t:s:", ["gender", "type=", "season="])
    except getopt.GetoptError:
        print 'test.py -g <gender> -t <type> -s <season>'
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-g", "--gender"):
            gender = arg
            if gender != "men" and gender != "women":
                print "Gender wrong, please only use 'Men' or 'Women'."
                sys.exit()
        elif opt in ("-t", "--type"):
            ptype = arg
        elif opt in ("-s", "--season"):
            season = arg

    engine = settings.create_engine(gender)

    if ptype == "team_stat":
        check_team_stat(engine, season)


if __name__ == "__main__":
    main(sys.argv[1:])