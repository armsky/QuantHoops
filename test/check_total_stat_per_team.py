__author__ = 'Hao Lin'

import sys
reload(sys)
sys.setdefaultencoding("utf8")
sys.path.insert(1, '../scrapers')
from scraper_men import *
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql://root:QuantH00p!@localhost/NCAA_Women', echo=False)
Session = sessionmaker(bind=engine, autocommit=True, autoflush=False)

session = Session()
squad_id_list = session.query(Squad).all().id
for squad_id in squad_id_list:
    print squad_id