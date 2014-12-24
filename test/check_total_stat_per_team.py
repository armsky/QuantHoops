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
print len(squad_season_stat_list)
for squad_season_record in squad_season_stat_list:
    squad_id = squad_season_record.squad_id
    session.query(SquadGameStat).filter_by(squadid=squad_id).all()

print "done"