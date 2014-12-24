__author__ = 'Hao Lin'

import sys
reload(sys)
sys.setdefaultencoding("utf8")
sys.path.insert(1, '../scrapers')
sys.path.insert(1, '../NCAA')
from scraper_men import *
from ncaa_men import *
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql://root:QuantH00p!@localhost/NCAA_Men', echo=False)
Session = sessionmaker(bind=engine, autocommit=True, autoflush=False)

session = Session()
squad_season_stat_list = session.query(SquadSeasonStat).all()

for squad_season_record in squad_season_stat_list:
    squad_id = squad_season_record.squad_id
    print squad_id
    total_stats = {
            'field_goals_made':squad_season_record.field_goals_made,
            'field_goals_attempted':squad_season_record.field_goals_attempted,
            'three_field_goals_made':squad_season_record.three_field_goals_made,
            'three_field_goals_attempted':squad_season_record.three_field_goals_attempted,
            'free_throws_made':squad_season_record.free_throws_made,
            'free_throws_attempted':squad_season_record.free_throws_attempted,
            'points':squad_season_record.points,
            'offensive_rebounds':squad_season_record.offensive_rebounds,
            'defensive_rebounds':squad_season_record.defensive_rebounds,
            'total_rebounds':squad_season_record.total_rebounds,
            'assists': squad_season_record.assists,
            'turnovers':squad_season_record.turnovers,
            'steals':squad_season_record.steals,
            'blocks':squad_season_record.blocks,
            'fouls':squad_season_record.fouls
        }

    stats_sum = {
        'field_goals_made':0,
        'field_goals_attempted':0,
        'three_field_goals_made':0,
        'three_field_goals_attempted':0,
        'free_throws_made':0,
        'free_throws_attempted':0,
        'points':0,
        'offensive_rebounds':0,
        'defensive_rebounds':0,
        'total_rebounds':0,
        'assists': 0,
        'turnovers':0,
        'steals':0,
        'blocks':0,
        'fouls':0
    }
    game_stat_list = session.query(SquadGameStat).filter_by(squad_id=squad_id).all()
    for game_stat_record in game_stat_list:
        stats = {
                'field_goals_made':game_stat_record.field_goals_made,
                'field_goals_attempted':game_stat_record.field_goals_attempted,
                'three_field_goals_made':game_stat_record.three_field_goals_made,
                'three_field_goals_attempted':game_stat_record.three_field_goals_attempted,
                'free_throws_made':game_stat_record.free_throws_made,
                'free_throws_attempted':game_stat_record.free_throws_attempted,
                'points':game_stat_record.points,
                'offensive_rebounds':game_stat_record.offensive_rebounds,
                'defensive_rebounds':game_stat_record.defensive_rebounds,
                'total_rebounds':game_stat_record.total_rebounds,
                'assists': game_stat_record.assists,
                'turnovers':game_stat_record.turnovers,
                'steals':game_stat_record.steals,
                'blocks':game_stat_record.blocks,
                'fouls':game_stat_record.fouls
            }
        for k, v in stats_sum.iteritems():
            # print stats.get(k)
            stats_sum[k] = v + stats.get(k)
            # if k == "field_goals_made":
            #     print v
    # print zip(total_stats.iteritems(), stats_sum.iteritems())
    print cmp(total_stats, stats_sum)
    print total_stats
    print stats_sum
    print "========================"
    """
        total_stats = {
            'field_goals_made':squad_season_record.field_goals_made,
            'field_goals_attempted':squad_season_record.field_goals_attempted,
            'field_goals_percentage':squad_season_record.field_goals_percentage,
            'three_field_goals_made':squad_season_record.three_field_goals_made,
            'three_field_goals_attempted':squad_season_record.three_field_goals_attempted,
            'three_field_goals_percentage':squad_season_record.three_field_goals_percentage,
            'free_throws_made':squad_season_record.free_throws_made,
            'free_throws_attempted':squad_season_record.free_throws_attempted,
            'free_throws_percentage':squad_season_record.free_throws_percentage,
            'points':squad_season_record.points,
            'average_points':squad_season_record.average_points,
            'offensive_rebounds':squad_season_record.offensive_rebounds,
            'defensive_rebounds':squad_season_record.defensive_rebounds,
            'total_rebounds':squad_season_record.total_rebounds,
            'average_rebounds':squad_season_record.average_rebounds,
            'assists': squad_season_record.assists,
            'turnovers':squad_season_record.turnovers,
            'steals':squad_season_record.steals,
            'blocks':squad_season_record.blocks,
            'fouls':squad_season_record.fouls,
            'double_doubles':squad_season_record.double_doubles,
            'triple_doubles':squad_season_record.triple_doubles
        }
    """