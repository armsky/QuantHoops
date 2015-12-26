__author__ = 'Hao Lin'

import sys
import sqlalchemy
from sqlalchemy.orm import sessionmaker


def create_engine(gender, user=None, password=None, host=None, echo=False):
    """SQL connections, SQL execution and high-level DB-API interface.

    :param gender: Men or Women
    :param user: database user name
    :param password: database user password
    :param host: database hostname
    :param echo=False: if True, the Engine will log all statements
        as well as a repr() of their parameter lists to the engines
        logger, which defaults to sys.stdout.
    :return: SQLAlchemy `Engine` instance
    """
    user = "linhao"
    password = "IPepsi"
    host = "192.169.234.41"
    if gender == "men":
        database = "linhao_ncaa_men"
    elif gender == "women":
        database = "linhao_ncaa_Women"
    else:
        print "No database specified or gender wrong..."
        sys.exit()

    engine = sqlalchemy.create_engine('mysql+pymysql://'+user+':'+password+'@'+host+'/'+database, echo=echo)
    return engine


def create_session(engine):
    """create a session object based on engine

    :return : session
    """
    Session = sessionmaker(bind=engine, autocommit=True, autoflush=False)
    session = Session()
    return session