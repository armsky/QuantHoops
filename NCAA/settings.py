__author__ = 'Hao Lin'

import sys
import sqlalchemy
from sqlalchemy.orm import sessionmaker


def create_engine(gender, user=None, password=None, host=None, echo=False):
    """SQL connections, SQL execution and high-level DB-API interface.

    :param gender: Men or Women
    :param user: Database user name
    :param password: Database user password
    :param host: Database hostname
    :param echo=False: if True, the Engine will log all statements
        as well as a repr() of their parameter lists to the engines
        logger, which defaults to sys.stdout.
    :return: SQLAlchemy `Engine` instance
    """
    if user is None:
        user = "root"
    if password is None:
        password = "QuantH00p!"
    if host is None:
        host = "localhost"
    if gender == "men":
        database = "NCAA_Men"
    elif gender == "women":
        database = "NCAA_Women"
    else:
        print "No database specified or gender wrong..."
        sys.exit()

    engine = sqlalchemy.create_engine('mysql://'+user+':'+password+'@'+host+'/'+database, echo=echo)
    return engine


def create_session(engine):
    """create a session object based on engine

    :return : session
    """
    Session = sessionmaker(bind=engine, autocommit=True, autoflush=False)
    session = Session()
    return session