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


## -- CLASSES --

Base = declarative_base()

# - Schedule -- /
'''Schedule is the cross-reference table for establishing the many-to-many
map from Squads to Games.'''
schedule = Table('schedule', Base.metadata,
        Column('game_id', Integer, ForeignKey('game.id', onupdate='cascade')),
        Column('squad_id', Integer, ForeignKey('squad.id', onupdate='cascade')),
        Column('type', Enum('home', 'away'))
)

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

    discriminator = Column(String)
    __mapper_args__ = {'polymorphic_on' : discriminator}

    id = Column(Integer, primary_key=True)

    date = Column(Date)

    # Map squads playing via schedule cross-reference Table
    opponents = relationship('Squad',
                             secondary=schedule,
                             backref=backref('schedule', order_by=date))
    winner_id = Column(Integer, ForeignKey('squad.id', onupdate='cascade'))
    winner = relationship('Squad', foreign_keys=[winner_id],
                          backref=backref('wins', order_by=date))
    winner_score = Column(Integer)

    loser_id = Column(Integer, ForeignKey('squad.id', onupdate='cascade'))
    loser = relationship('Squad', foreign_keys=[loser_id],
                         backref=backref('losses', order_by=date))
    loser_score = Column(Integer)

    # Post season
    postseason = Column(Boolean)
    overtime = Column(Integer)

    location = Column(String)
    attendance = Column(String)
    #TODO: officials may be a new class ?
    officials = Column(String)
    # NOTE boxscore = one-to-many map to PlayerStatSheets.

    def __init__(self, home_team, away_team, date, location,
                 attendance, officials, loser=None, winner=None,
                 winner_score=None, loser_score=None, postseason=False):
        # First and 2nd Teams date Location attendance and officials are mandatory.
        # Location equals to Home team's location, or a specified neutral site
        # Specify loser and winner optionally; if one is missing, the other will be inferred.
        # If the game haven't happened yet (future game), do not scrape it
        self.opponents.append(home_team)
        self.opponents.append(away_team)
        self.date = date
        self.location = location
        self.attendance = attendance
        self.officials = officials

        self.postseason = postseason

        self.winner_score = winner_score
        self.loser_score = loser_score

        if loser is not None:
            self.loser = loser
            if winner is None:
                if self.loser.id==self.home_id:
                    # Away team was winner
                    self.winner = away_team
                else:
                    # Home team was winner
                    self.winner = home_team

        if winner is not None:
            self.winner = winner
            if loser is None:
                if self.winner.id==self.home_id:
                    # Away team was loser
                    self.loser = away_team
                else:
                    # Home team was loser
                    self.winner = home_team

    # def __contains__(self, squad):
    #     return squad in game.opponents

    def __repr__(self):
        teams = "%s vs. %s" % (self.opponents[0].team.name,
                                self.opponents[1].team.name)
        date = self.date.strftime('%h %d, %Y')
        return "<Game('%s', '%s')>" % (teams, date)


# - Player -- /
class Player(Base):
    """Players hold vital statistics like height, number, position, etc.
    They do NOT themselves contain and performance statistics or team
    affiliation. Instead, they possess a one-to-many mapping to SquadMembers,
    which are essentially chrono-sensitive versions of the Player. For
    example, a Player's corresponding SquadMember from 2010-11 will not
    have access to that Player's statistics from 2011-12, nor will these
    latest statistics be incorporated into the earlier SquadMember's record.
    This allows for more realistic simulations."""
    __tablename__ = "player"

    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    middle_name = Column(String)
    last_name = Column(String, nullable=False)
    name_suffix = Column(String)

    height = Column(String)        # i.e 6-11
    weight = Column(Integer)        # Pounds
    position = Column(String)

    # NOTE career = one-to-many mapping to SquadMembers

    def __init__(self, first_name, last_name, middle_name=None,
                 name_suffix=None, id=None, height=None,
                 position=None):
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.name_suffix = name_suffix

        if id is not None: self.id = id
        if height is not None: self.height = height
        if position is not None: self.position = position

    def __repr__(self):
        return "<Player('%s %s')>" % (self.first_name, self.last_name)


# - SquadMember -- /
class SquadMember(Base):
    """This is the class that holds individual game statistics for a Player.
    Many-to-one maps to Player, Squad, and Game"""
    __tablename__ = 'squadmember'

    id = Column(Integer, primary_key=True)

    player_id = Column(Integer, ForeignKey('player.id', onupdate='cascade'))
    player = relationship('Player', backref=backref('career', order_by=id))

    squad_id = Column(Integer, ForeignKey('squad.id', onupdate='cascade'))
    squad = relationship('Squad', backref=backref('roster', order_by=id))

    stats_id = Column(Integer, ForeignKey('statscache.id', onupdate='cascade'))
    stats = relationship('SquadMemberDerivedStats', backref=backref('referent', uselist=False, order_by=id))

    # NOTE statsheets = one-to-many mapping to PlayerStatSheets

    # Vital-ish stats
    jersey = Column(Integer)
    year = Column(String)       # i.e., year in college (Freshman, etc.)
    games_played = Column(Integer)
    games_started = Column(Integer)

    def __init__(self, player, squad, jersey=None, year=None,
                 games_played=None, games_started=None):
        self.player = player
        self.squad = squad
        if jersey is not None:
            self.jersey = jersey
        if year is not None:
            self.year = year
        if games_played is not None:
            self.games_played = games_played
        if games_started is not None:
            self.games_started = games_started

    # @reconstructor
    # def _reconstruct(self):
    #     if self.stats is None:
    #         self.derive_stats()

    def __repr__(self):
        return "<SquadMember('%s %s', '%s', '%s')>" % \
                (self.player.first_name, self.player.last_name,
                 self.squad.team.name, self.squad.season)


# - PlayerStatSheet -- /
class PlayerStatSheet(Base):
    """Contains the stats of one SquadMember in one Game"""
    __tablename__ = 'playerstatsheet'

    id = Column(Integer, primary_key=True)
    squadmember_id = Column(Integer, ForeignKey('squadmember.id', onupdate='cascade'))
    squadmember = relationship('SquadMember', backref=backref('statsheets', order_by=id))

    game_id = Column(Integer, ForeignKey('game.id', onupdate='cascade'))
    game = relationship('Game', backref=backref('boxscore', order_by=id))

    # Individual Game Statistics
    minutes_played = Column(Float)
    field_goals_made = Column(Integer)
    field_goals_attempted = Column(Integer)
    threes_made = Column(Integer)
    threes_attempted = Column(Integer)
    free_throws_made = Column(Integer)
    free_throws_attempted = Column(Integer)
    points = Column(Integer)
    offensive_rebounds = Column(Integer)
    defensive_rebounds = Column(Integer)
    rebounds = Column(Integer)
    assists = Column(Integer)
    turnovers = Column(Integer)
    steals = Column(Integer)
    blocks = Column(Integer)
    fouls = Column(Integer)

    stats = [
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
        'rebounds',
        'assists',
        'turnovers',
        'steals',
        'blocks',
        'fouls'
    ]

    def __repr__(self):
        name = "%s %s" % (self.squadmember.player.first_name,
                          self.squadmember.player.last_name)
        game = "%s vs. %s" % (self.game.opponents[0].team.name,
                              self.game.opponents[1].team.name)
        date = self.game.date.strftime('%h %d, %Y')


# - DerivedStats -- /
class DerivedStats(Base):
    __tablename__ = 'statscache'
    id = Column(Integer, primary_key=True)

    # Polymorphic: DerivedStatsPlayer, DerivedStatsSquad
    type = Column(String)
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

    id = Column(Integer, primary_key=True)
    season = Column(String, nullable=False)

    team_id = Column(Integer, ForeignKey('team.id', onupdate='cascade'))
    team = relationship("Team", backref=backref('squads', order_by=id))

    stats_id = Column(Integer, ForeignKey('statscache.id', onupdate='cascade'))
    stats = relationship('SquadDerivedStats', backref=backref('referent', uselist=False, order_by=id))

    # NOTE roster = one-to-many map to SquadMembers
    # NOTE schedule = many-to-many map to Games
    # NOTE wins = one-to-many map to Games
    # NOTE losses = one-to-many map to Games

    def __init__(self, season, team=None):
        self.season = season
        self._cache = dict()        # Cache is never persisted.
        if team is not None:
            self.team = team


# - Team -- /
class Team(Base):
    """Teams contain a relationship to Squads for any available years.
    Also contain relationships to alternate team names.

    Note that IDs have been assigned explicitly to match those used by
    NCAA.com to make record linkage easier. The alternate team names
    and fuzzy matching capabilities are just in case another source is
    used.

    One-to-many maps to Squads and TeamAliases."""
    __tablename__ = 'team'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    # NOTE squads = one-to-many map to Squads
    # NOTE aliases = one-to-many map to TeamAliases

    def __init__(self, name, id=None):
        self.name = name
        if id is not None:
            self.id = id


# - TeamAlias -- /
class TeamAlias(Base):
    '''TeamAlias is used for record linkage. When querying the database for a
    Team by name it is not necessarily (read: usually) the case that there is
    a standardized way of referring to the Team. Different sources abbreviate
    teams in different ways, e.g. 'Pitt' versus 'Pittsburgh.' This class helps
    mitigate this problem by keeping track of different ways of referring to
    a team. Names in this class are normalized by entirely removing all
    non-alpha-numeric characters and transforming to upper case.

    TeamAliases are in a many-to-one relationship with Teams'''
    __tablename__ = 'teamalias'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    team_id = Column(Integer, ForeignKey('team.id', onupdate='cascade'))
    team = relationship("Team", backref=backref('aliases', order_by=id))

    def __init__(self, name):
        self.name = normalize_name(name)

    def __repr__(self):
        return "<TeamAlias('%s', '%s')>" % (self.team.name, self.name)








