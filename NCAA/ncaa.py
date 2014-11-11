__author__ = 'Hao Lin'

'''
Library defines ORM database accessor classes for NCAA
'''

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref, sessionmaker, reconstructor
from sqlalchemy.ext.declarative import declarative_base

import re
import os
import datetime

from collections import OrderedDict, defaultdict

engine = create_engine('mysql://hooper:michael@localhost/QuantHoops', echo=True)
metadata = MetaData()

## -- CLASSES --

Base = declarative_base()

# - Schedule -- /
class Schedule(Base):
    __tablename__ = 'shedule'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    game_id = Column('game_id', Integer, ForeignKey('game.id', onupdate='cascade'),
                     primary_key=True)
    squad_id = Column('squad_id', Integer, ForeignKey('squad.id', onupdate='cascade'),
                     primary_key=True)
    type = Column('type', Enum('home', 'away','neutral','tournament'))

    def __init__(self, game_id, squad_id, type):
        self.game_id = game_id
        self.squad_id = squad_id
        self.type = type


# - Game -- /
class Game(Base):
    """
    Game holds references to two Squads. Holds a collection of references
    to SquadMembers (from both Squads). Allow for specification of Winner.
    Also hold vital statistics such as where and when.

    Many-to-many map to Squads via Schedule, one-to-many map to
    PlayerStatSheets.
    """
    __tablename__ = 'game'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    discriminator = Column(String(128))
    __mapper_args__ = {'polymorphic_on' : discriminator}

    id = Column(Integer, primary_key=True)

    date = Column(Date)

    # Map squads playing via schedule cross-reference Table
    # opponents = relationship('Squad',
    #                          secondary=schedule,
    #                          backref=backref('schedule', order_by=date))
    winner_id = Column(Integer, ForeignKey('squad.id', onupdate='cascade'))
    winner = relationship('Squad', foreign_keys=[winner_id],
                          backref=backref('wins', order_by=date))
    winner_score = Column(Integer)

    loser_id = Column(Integer, ForeignKey('squad.id', onupdate='cascade'))
    loser = relationship('Squad', foreign_keys=[loser_id],
                         backref=backref('losses', order_by=date))
    loser_score = Column(Integer)

    # Post season
    # postseason = Column(Boolean)
    # overtime = Column(Integer)

    location = Column(String(128))
    attendance = Column(Integer)
    #TODO: officials may be a new class ?
    officials = Column(String(128))
    # NOTE boxscore = one-to-many map to PlayerStatSheets.

    def __init__(self, game_id, winner_id, loser_id, winner_score,loser_score,
                 date=None, location=None, attendance=None, officials=None):
        # First and 2nd Teams date Location attendance and officials are mandatory.
        # Location equals to Home team's location, or a specified neutral site
        # Specify loser and winner;
        # If the game haven't happened yet (future game), do not scrape it
        self.id = game_id
        self.date = date
        self.winner_id = winner_id
        self.loser_id = loser_id
        self.winner_score = winner_score
        self.loser_score = loser_score
        self.location = location
        self.attendance = attendance
        self.officials = officials


    # def __contains__(self, squad):
    #     return squad in game.opponents

    def __repr__(self):
        teams = "%s vs. %s" % (self.opponents[0].team.name,
                                self.opponents[1].team.name)
        date = self.date.strftime('%h %d, %Y')
        return "<Game('%s', '%s')>" % (teams, date)


# - Player -- /
class Player(Base):
    """Players possess a one-to-many mapping to SquadMembers,
    which are essentially chrono-sensitive versions of the Player. For
    example, a Player's corresponding SquadMember from 2010-11 will not
    have access to that Player's statistics from 2011-12, nor will these
    latest statistics be incorporated into the earlier SquadMember's record.
    This allows for more realistic simulations."""
    __tablename__ = "player"
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)

    # NOTE career = one-to-many mapping to SquadMembers

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return "<Player('%s %s')>" % (self.first_name, self.last_name)


# - SquadMember -- /
class SquadMember(Base):
    """This is the class that holds individual game statistics for a Player.
    Many-to-one maps to Player, Squad, and Game"""
    __tablename__ = 'squadmember'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)

    player_id = Column(Integer, ForeignKey('player.id', onupdate='cascade'))
    player = relationship('Player', backref=backref('career', order_by=id))

    squad_id = Column(Integer, ForeignKey('squad.id', onupdate='cascade'))
    squad = relationship('Squad', backref=backref('roster', order_by=id))

    name = Column(String(64), nullable=False)
    jersey = Column(Integer)
    position = Column(String(2))
    height = Column(String(8))        # i.e 6-11
    year = Column(String(8))       # i.e., year in college (Freshman, etc.)
    games_played = Column(Integer)
    games_started = Column(Integer)

    stats_id = Column(Integer, ForeignKey('statscache.id', onupdate='cascade'))
    stats = relationship('SquadMemberDerivedStats', backref=backref('referent', uselist=False, order_by=id))

    # NOTE statsheets = one-to-many mapping to PlayerStatSheets

    # Vital-ish stats

    def __init__(self, player_id, squad_id, name, jersey=None, position=None,
                 height=None, year=None, games_played=None, games_started=None, stats_id=None):
        self.player_id = player_id
        self.squad_id = squad_id
        self.name = name
        self.jersey = jersey
        self.position = position
        self.height = height
        self.year = year
        self.games_played = games_played
        self.games_started = games_started
        self.stats_id = stats_id

    def __repr__(self):
        return "<SquadMember('%s %s', '%s', '%s')>" % \
                (self.player.first_name, self.player.last_name,
                 self.squad.team.name, self.squad.season)


# - PlayerStatSheet -- /
class PlayerStatSheet(Base):
    """Contains the stats of one SquadMember in one Game"""
    __tablename__ = 'playerstatsheet'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    squadmember_id = Column(Integer, ForeignKey('squadmember.id', onupdate='cascade'))
    squadmember = relationship('SquadMember', backref=backref('statsheets', order_by=id))

    game_id = Column(Integer, ForeignKey('game.id', onupdate='cascade'))
    game = relationship('Game', backref=backref('boxscore', order_by=id))

    # Individual Game Statistics
    minutes_played = Column(Float)
    field_goals_made = Column(Integer)
    field_goals_attempted = Column(Integer)
    field_goals_percentage = Column(Float)
    three_field_goals_made = Column(Integer)
    three_field_goals_attempted = Column(Integer)
    three_field_goals_percentage = Column(Float)
    free_throws_made = Column(Integer)
    free_throws_attempted = Column(Integer)
    free_throws_percentage = Column(Float)
    points = Column(Integer)
    average_points = Column(Float)
    offensive_rebounds = Column(Integer)
    defensive_rebounds = Column(Integer)
    total_rebounds = Column(Integer)
    average_rebounds = Column(Float)
    assists = Column(Integer)
    turnovers = Column(Integer)
    steals = Column(Integer)
    blocks = Column(Integer)
    fouls = Column(Integer)
    double_doubles = Column(Integer)
    triple_doubles = Column(Integer)

    #calculated Statistics
    minutes_percentage = Column(Float)

    stats = {
        'minutes_played':'minutes_played',
        'field_goals_made':'field_goals_made',
        'field_goals_attempted':'field_goals_attempted',
        'field_goals_percentage':'field_goals_percentage',
        'three_field_goals_made':'three_field_goals_made',
        'three_field_goals_attempted':'three_field_goals_attempted',
        'three_field_goals_percentage':'three_field_goals_percentage',
        'free_throws_made':'free_throws_made',
        'free_throws_attempted':'free_throws_attempted',
        'free_throws_percentage':'free_throws_percentage',
        'points':'points',
        'average_points':'average_points',
        'offensive_rebounds':'offensive_rebounds',
        'defensive_rebounds':'defensive_rebounds',
        'total_rebounds':'total_rebounds',
        'average_rebounds':'average_rebounds',
        'turnovers':'turnovers',
        'steals':'steals',
        'blocks':'blocks',
        'fouls':'fouls',
        'double_doubles':'double_doubles',
        'triple_doubles':'triple_doubles'
    }

    def __init__(self, squadmember_id, game_id):
        self.squadmember_id = squadmember_id
        self.game_id = game_id
        for stat, val in self.stats.items():
            setattr(self, stat, val)

    def __repr__(self):
        # name = "%s %s" % (self.squadmember.player.first_name,
        #                   self.squadmember.player.last_name)
        # game = "%s vs. %s" % (self.game.opponents[0].team.name,
        #                       self.game.opponents[1].team.name)
        # date = self.game.date.strftime('%h %d, %Y')
        print self.stats


# - DerivedStats -- /
class DerivedStats(Base):
    __tablename__ = 'statscache'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)

    # Polymorphic: DerivedStatsPlayer, DerivedStatsSquad
    type = Column(String(32))
    __mapper_args__ = {'polymorphic_on' : type}

    # One-to-One relationship with Squad / SquadMember

    # Derived statistics -- all calculated on load, stored in self.stats

    sumfields = [
        # Sums
        'minutes_played',
        'field_goals_made',
        'field_goals_attempted',
        'threes_made',
        'threes_attempted',
        'free_throws_made',
        'free_throws_attempted',
        'points',
        'offensive_rebounds',
        'defensive_rebounds',
        'total_rebounds',
        'assists',
        'turnovers',
        'steals',
        'blocks',
        'fouls'
    ]

    pctfields = {
        # Ratios
        'fg_pct'     : ('field_goals_made', 'field_goals_attempted'),
        'threes_pct' : ('threes_made', 'threes_attempted'),
        'ft_pct'     : ('free_throws_made', 'free_throws_attempted'),
        'ppm'        : ('points', 'minutes_played'),
        'lpm'        : ('field_goals_attempted', 'minutes_played'),
        # Averages
        'field_goal_avg' : ('field_goals_made', 'games_played'),
        'looks_avg'      : ('field_goals_attempted', 'games_played'),
        'threes_avg'     : ('threes_made', 'games_played'),
        'free_throws_avg': ('free_throws_made', 'games_played'),
        'points_avg'     : ('points', 'games_played'),
        'rebounds_avg'   : ('total_rebounds', 'games_played'),
        'steals_avg'     : ('steals', 'games_played'),
        'assists_avg'    : ('assists', 'games_played'),
        'blocks_avg'     : ('blocks', 'games_played'),
        'fouls_avg'      : ('fouls', 'games_played'),
        'turnovers_avg'  : ('turnovers', 'games_played')
    }

    # Sums
    games_played = Column(Float)
    minutes_played = Column(Float)
    field_goals_made = Column(Float)
    field_goals_attempted = Column(Float)
    threes_made = Column(Float)
    threes_attempted = Column(Float)
    free_throws_made = Column(Float)
    free_throws_attempted = Column(Float)
    points = Column(Float)
    offensive_rebounds = Column(Float)
    defensive_rebounds = Column(Float)
    total_rebounds = Column(Float)
    assists = Column(Float)
    turnovers = Column(Float)
    steals = Column(Float)
    blocks = Column(Float)
    fouls = Column(Float)

    # Ratios
    fg_pct = Column(Float)
    threes_pct = Column(Float)
    ft_pct = Column(Float)
    ppm = Column(Float)
    lpm = Column(Float)

    # Averages
    field_goal_avg = Column(Float)
    looks_avg = Column(Float)
    threes_avg = Column(Float)
    free_throws_avg = Column(Float)
    points_avg = Column(Float)
    rebounds_avg = Column(Float)
    steals_avg = Column(Float)
    assists_avg = Column(Float)
    blocks_avg = Column(Float)
    fouls_avg = Column(Float)
    turnovers_avg = Column(Float)

    def __init__(self, stats):
        '''Load stats into object'''
        for stat, val in stats.items():
            setattr(self, stat, val)

    def __getitem__(self, item):
        '''Alias of getattr'''
        return getattr(self, item)

    def __setitem__(self, item, val):
        '''Alias of setattr'''
        return setattr(self, item, val)

    def items(self):
        '''For iteration'''
        keys = self.sumfields + self.pctfields.keys()
        return [(key, getattr(self, key)) for key in keys]

    def __repr__(self):
        items = ["'%s': %f" % (k, v) for k, v in self.items()]
        return "<DerivedStats(%s)>" % ', '.join(items)


class SquadMemberDerivedStats(DerivedStats):
    __mapper_args__ = {'polymorphic_identity' : 'squadmember'}

    # Note referent is one-to-one mapping to SquadMember


class SquadDerivedStats(DerivedStats):
    __mapper_args__ = {'polymorphic_identity' : 'squad'}

    # NOTE referent is one-to-one mapping to Squad


# - Squad -- /
class Squad(Base):
    """Squads contain the roster and regular season record of a Team in
    a given season.

    One-to-many maps to SquadMembers, Games. Many-to-one map to Team."""
    __tablename__ = 'squad'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    division = Column(String(4), nullable=False)
    year = Column(Integer, nullable=False)

    conference_id = Column(Integer, ForeignKey('conference.id', onupdate='cascade'))

    team_id = Column(Integer, ForeignKey('team.id', onupdate='cascade'))
    team = relationship("Team", backref=backref('squads', order_by=id))

    stats_id = Column(Integer, ForeignKey('statscache.id', onupdate='cascade'))
    stats = relationship('SquadDerivedStats', backref=backref('referent', uselist=False, order_by=id))

    # NOTE roster = one-to-many map to SquadMembers
    # NOTE schedule = many-to-many map to Games
    # NOTE wins = one-to-many map to Games
    # NOTE losses = one-to-many map to Games

    def __init__(self, division, year, team=None, conference=None):
        self.division = division
        self.year = year
        self._cache = dict()        # Cache is never persisted.
        if team is not None:
            self.team = team
        if conference is not None:
            self.conference = conference


# - Team -- /
class Team(Base):
    """Teams contain a relationship to Squads for any available years.
    Also contain relationships to alternate team names.

    NCAA uses a permanent id (org_id, which is also known as ncaa_id)to
    represent a team no matter what the season is.

    Note that IDs have been assigned explicitly to match those used by
    NCAA.com to make record linkage easier. The alternate team names
    and fuzzy matching capabilities are just in case another source is
    used.

    One-to-many maps to Squads and TeamAliases."""
    __tablename__ = 'team'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    gender = Column(Enum('Men', 'Women'), nullable=False)

    # NOTE squads = one-to-many map to Squads
    # NOTE aliases = one-to-many map to TeamAliases

    def __init__(self, name, gender, id):
        self.name = name
        self.gender = gender
        self.id = id
        # if id is not None:
        #     self.id = id


# - TeamAlias -- /
class TeamAlias(Base):
    """TeamAlias is used for record linkage. When querying the database for a
    Team by name it is not necessarily (read: usually) the case that there is
    a standardized way of referring to the Team. Different sources abbreviate
    teams in different ways, e.g. 'Pitt' versus 'Pittsburgh.' This class helps
    mitigate this problem by keeping track of different ways of referring to
    a team. Names in this class are normalized by entirely removing all
    non-alpha-numeric characters and transforming to upper case.

    TeamAliases are in a many-to-one relationship with Teams"""
    __tablename__ = 'teamalias'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)

    team_id = Column(Integer, ForeignKey('team.id', onupdate='cascade'))
    team = relationship("Team", backref=backref('aliases', order_by=id))

    # def __init__(self, name):
    #     self.name = normalize_name(name)

    def __repr__(self):
        return "<TeamAlias('%s', '%s')>" % (self.team.name, self.name)

# - Season -- /
class Season(Base):
    """
    Use ncaa_id to determine season and gender, no matter what the division
    is.
    """
    __tablename__ = 'season'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    gender = Column(Enum("Men", "Women"), nullable=False)

# - Season -- /
class Conference(Base):
    """
    A team may belong to different in different year and division
    """
    __tablename__ = "conference"
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)

    # NOTE squads = one-to-many map to Squads
    belongings = relationship("Squad")

    def __init__(self, id, name):
        self.id = id
        self.name = name



Base.metadata.create_all(engine, checkfirst=True)