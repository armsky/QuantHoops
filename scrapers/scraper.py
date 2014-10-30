__author__ = 'Hao Lin'

import urls
from QuantHoops.NCAA.ncaa import *

import urllib
import re
from bs4 import BeautifulSoup

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref, sessionmaker, reconstructor
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql://hooper:michael@localhost/QuantHoops', echo=True)
Session = sessionmaker(bind=engine)
session = Session()


def soupify(url):
    """
    Takes a url and returns parsed html via BeautifulSoup and urllib.
    Used by the scrapers.
    """
    html = urllib.urlopen(url).read()
    soup = BeautifulSoup(html)
    return soup

def team_parser(season_id, division):
    try:
        row = session.query(Season).filter_by(id=season_id).first()
        gender = row.gender
        season = row.year
        url = "http://stats.ncaa.org/team/inst_team_list/%s?division=%s" % (season_id, division)
        soup = soupify(url)
        team_links = [x.find('a') for x in soup.findAll('td')]
        for team in team_links:
            ncaa_id = int(team["href"].split("=")[-1])
            name = team.string

            team_record = Team(name, gender, ncaa_id)
            if session.query(Team).filter_by(id=ncaa_id).all():
                session.query(Team).filter_by(id=ncaa_id).delete()
            else:
                session.merge(team_record)

            squad_record = Squad(division, season, team_record)
            session.add(squad_record)
        session.commit()

    except:
        session.rollback()
        raise
    finally:
        session.close()

team_parser("11540", "1")

# try:
#
#     #Team
#     for category, link in urls.TEAM.iteritems():
#         gender = category.split('_')[0]
#         season = category.split('_')[1]
#         division = category.split('_')[2]
#
#         html = urllib.urlopen(link).read()
#         soup = BeautifulSoup(html)
#
#         for a in soup.find_all('a'):
#             href = a.get('href')
#             if re.match("/team/index/11540", href):
#                 ncaa_id = href.split("=")[-1]
#                 name = a.string
#
#                 new_record = Team(name, gender,ncaa_id)
#                 if session.query(Team).filter_by(id=ncaa_id).all():
#                     session.query(Team).filter_by(id=ncaa_id).delete()
#                 else:
#                     session.merge(new_record)
#     session.commit()
#
# except:
#     session.rollback()
#     raise
# finally:
#     session.close()