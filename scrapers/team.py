__author__ = 'Hao Lin'

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref, sessionmaker, reconstructor
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('mysql://hooper:michael@localhost/QuantHoops', echo=False)

from bs4 import BeautifulSoup

from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class Team(Base):
    __tablename__ = 'team'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    # NOTE squads = one-to-many map to Squads
    # NOTE aliases = one-to-many map to TeamAliases

    def __init__(self, name, id=None):
        self.name = name
        if id is not None:
            self.id = id


new_record = Team('me again')
session.add(new_record)
session.commit()