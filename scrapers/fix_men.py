__author__ = 'armsky'

from scraper_men import *
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql://root:QuantH00p!@localhost/NCAA_Men', echo=False)
Session = sessionmaker(bind=engine, autocommit=True, autoflush=False)

# Before run this script, the squad_member is 19042
squad_id_list = []
with open("../Database/missing_players.txt") as f:
    lines = f.readlines()
    for line in lines:
        if "squad_id:" in line:
            squad_id = line.strip().split(': ')[-1]
            if squad_id not in squad_id_list:
                squad_id_list.append(squad_id)

for squad_id in squad_id_list:
    session = Session()
    squad_record = session.query(Squad).filter_by(id=squad_id).first()
    if squad_record is not None:
        player_parser(session, squad_record)
    session.close()

f.close()