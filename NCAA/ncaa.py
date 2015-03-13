__author__ = 'Hao Lin'

'''
Library defines ORM database accessor classes for NCAA
'''

import sys
import settings
from sqlalchemy import *
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

try:
    # sys.argv[1] shoud be "-g", sys.argv[2] should be gender -- Men or Women
    engine = settings.create_engine(sys.argv[2])
except:
    print "No database specified..."
    raise
metadata = MetaData()

# -- CLASSES --

Base = declarative_base()


# - Schedule -- /
class Schedule(Base):
    """
    One game will have two schedules for both team, indicate which one is
    home team, and which one is away team.
    """
    __tablename__ = 'schedule'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    game_id = Column(Integer, ForeignKey('game.id', onupdate='cascade', ondelete='cascade'),
                     primary_key=True)
    squad_id = Column(Integer, ForeignKey('squad.id', onupdate='cascade', ondelete='cascade'),
                      primary_key=True)
    type = Column('type', Enum('home', 'away', 'neutral', 'tournament'))

    def __init__(self, game_id, squad_id, type):
        self.game_id = game_id
        self.squad_id = squad_id
        self.type = type


# - Game -- /
class Game(Base):
    """
    Game holds references to two Squads. Holds a collection of total score,
    first & second half score, first & second overtime score.
    Allow for specification of winner and loser.
    Also hold vital statistics such as where and when and attendance.

    Many-to-many map to Squads via Schedule, one-to-many map to PlayerGameStat.
    """
    __tablename__ = 'game'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    has_stat = Column(Integer)
    has_detail = Column(Integer)

    winner_id = Column(Integer, ForeignKey('squad.id', onupdate='cascade', ondelete='cascade'))
    winner_score = Column(Integer)
    winner_first_half_score = Column(Integer)
    winner_second_half_score = Column(Integer)
    winner_first_OT_score = Column(Integer)
    winner_second_OT_score = Column(Integer)

    loser_id = Column(Integer, ForeignKey('squad.id', onupdate='cascade', ondelete='cascade'))
    loser_score = Column(Integer)
    loser_first_half_score = Column(Integer)
    loser_second_half_score = Column(Integer)
    loser_first_OT_score = Column(Integer)
    loser_second_OT_score = Column(Integer)

    location = Column(String(128))
    attendance = Column(Integer)
    officials = Column(String(128))

    def __init__(self, game_id, winner_id, loser_id, winner_score, loser_score,
                 date=None, location=None, attendance=None, officials=None):
        # First and 2nd Teams date Location attendance and officials are mandatory.
        # Location equals to Home team's location, or a specified neutral site
        # Specify loser and winner;
        # If the game haven't happened yet (future game), do not scrape it
        self.id = game_id
        self.date = date
        self.has_stat = 0
        self.has_detail = 0
        self.winner_id = winner_id
        self.loser_id = loser_id
        self.winner_score = winner_score
        self.loser_score = loser_score
        self.location = location
        self.attendance = attendance
        self.officials = officials

    def __repr__(self):
        id = self.id
        date = self.date.strftime('%h %d, %Y')
        return "<Game('%s', '%s')>" % (id, date)


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
    """This is the class that holds Player's basic information.
    Many-to-one maps to Player, Squad, and Game"""
    __tablename__ = 'squadmember'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)

    player_id = Column(Integer, ForeignKey('player.id', onupdate='cascade', ondelete='cascade'))
    player = relationship('Player', backref=backref('career', order_by=id))

    squad_id = Column(Integer, ForeignKey('squad.id', onupdate='cascade', ondelete='cascade'))
    squad = relationship('Squad', backref=backref('roster', order_by=id))

    name = Column(String(64), nullable=False)
    jersey = Column(Integer)
    position = Column(String(8))
    height = Column(String(8))        # i.e 6-11
    year = Column(String(8))       # i.e., year in college (Freshman, etc.)
    games_played = Column(Integer)
    games_started = Column(Integer)

    def __init__(self, player_id, squad_id, name, jersey=None, position=None,
                 height=None, year=None, games_played=None, games_started=None):
        self.player_id = player_id
        self.squad_id = squad_id
        self.name = name
        self.jersey = jersey
        self.position = position
        self.height = height
        self.year = year
        self.games_played = games_played
        self.games_started = games_started

    def __repr__(self):
        return "<SquadMember('%s %s', '%s', '%s')>" % \
            (self.player.first_name, self.player.last_name,
             self.squad.team.name, self.squad.season)


# - PlayerGameStat -- /
class PlayerGameStat(Base):
    """Contains the stats of one SquadMember in one Game"""
    __tablename__ = 'playergamestat'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    squadmember_id = Column(Integer, ForeignKey('squadmember.id', onupdate='cascade', ondelete='cascade'))
    game_id = Column(Integer, ForeignKey('game.id', onupdate='cascade', ondelete='cascade'))

    # Individual Game Statistics
    minutes_played = Column(String(16))
    field_goals_made = Column(Integer)
    field_goals_attempted = Column(Integer)
    three_field_goals_made = Column(Integer)
    three_field_goals_attempted = Column(Integer)
    free_throws_made = Column(Integer)
    free_throws_attempted = Column(Integer)
    points = Column(Integer)
    offensive_rebounds = Column(Integer)
    defensive_rebounds = Column(Integer)
    total_rebounds = Column(Integer)
    assists = Column(Integer)
    turnovers = Column(Integer)
    steals = Column(Integer)
    blocks = Column(Integer)
    fouls = Column(Integer)

    def __init__(self, squadmember_id, game_id, stats):
        self.squadmember_id = squadmember_id
        self.game_id = game_id
        for k, v in stats.iteritems():
            setattr(self, k, v)


# - SquadGameStat -- /
class SquadGameStat(Base):
    """Contains the stats of one Squad in one Game"""
    __tablename__ = 'squadgamestat'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    squad_id = Column(Integer, ForeignKey('squad.id', onupdate='cascade', ondelete='cascade'))
    game_id = Column(Integer, ForeignKey('game.id', onupdate='cascade', ondelete='cascade'))

    # Individual Game Statistics
    minutes_played = Column(String(16))
    field_goals_made = Column(Integer)
    field_goals_attempted = Column(Integer)
    three_field_goals_made = Column(Integer)
    three_field_goals_attempted = Column(Integer)
    free_throws_made = Column(Integer)
    free_throws_attempted = Column(Integer)
    points = Column(Integer)
    offensive_rebounds = Column(Integer)
    defensive_rebounds = Column(Integer)
    total_rebounds = Column(Integer)
    assists = Column(Integer)
    turnovers = Column(Integer)
    steals = Column(Integer)
    blocks = Column(Integer)
    fouls = Column(Integer)

    # team_stats that cannot assigned to players
    team_offensive_rebounds = Column(Integer)
    team_defensive_rebounds = Column(Integer)
    team_total_rebounds = Column(Integer)
    team_turnovers = Column(Integer)
    team_fouls = Column(Integer)

    def __init__(self, squad_id, game_id, stats):
        self.squad_id = squad_id
        self.game_id = game_id
        for k, v in stats.iteritems():
            setattr(self, k, v)


# - PlayerSeasonStat -- /
class PlayerSeasonStat(Base):
    """Contains the stats of one SquadMember in one Season"""
    __tablename__ = 'playerseasonstat'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    squadmember_id = Column(Integer, ForeignKey('squadmember.id', onupdate='cascade', ondelete='cascade'))

    # Individual Game Statistics
    minutes_played = Column(String(16))
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

    def __init__(self, squadmember_id, stats):
        self.squadmember_id = squadmember_id
        for k, v in stats.iteritems():
            setattr(self, k, v)


# - SquadSeasonStat -- /
class SquadSeasonStat(Base):
    """Contains the stats of one Squad in one Season"""
    __tablename__ = 'squadseasonstat'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    squad_id = Column(Integer, ForeignKey('squad.id', onupdate='cascade', ondelete='cascade'), primary_key=True)

    # Team's total season Statistics
    minutes_played = Column(String(16))
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

    # Opponent's total season Statistics
    Opnt_minutes_played = Column(String(16))
    Opnt_field_goals_made = Column(Integer)
    Opnt_field_goals_attempted = Column(Integer)
    Opnt_field_goals_percentage = Column(Float)
    Opnt_three_field_goals_made = Column(Integer)
    Opnt_three_field_goals_attempted = Column(Integer)
    Opnt_three_field_goals_percentage = Column(Float)
    Opnt_free_throws_made = Column(Integer)
    Opnt_free_throws_attempted = Column(Integer)
    Opnt_free_throws_percentage = Column(Float)
    Opnt_points = Column(Integer)
    Opnt_average_points = Column(Float)
    Opnt_offensive_rebounds = Column(Integer)
    Opnt_defensive_rebounds = Column(Integer)
    Opnt_total_rebounds = Column(Integer)
    Opnt_average_rebounds = Column(Float)
    Opnt_assists = Column(Integer)
    Opnt_turnovers = Column(Integer)
    Opnt_steals = Column(Integer)
    Opnt_blocks = Column(Integer)
    Opnt_fouls = Column(Integer)
    Opnt_double_doubles = Column(Integer)
    Opnt_triple_doubles = Column(Integer)

    # Team_stats that cannot assigned to players
    team_points = Column(Integer)
    team_average_points = Column(Float)
    team_offensive_rebounds = Column(Integer)
    team_defensive_rebounds = Column(Integer)
    team_total_rebounds = Column(Integer)
    team_average_rebounds = Column(Float)
    team_assists = Column(Integer)
    team_turnovers = Column(Integer)
    team_steals = Column(Integer)
    team_blocks = Column(Integer)
    team_fouls = Column(Integer)
    team_double_doubles = Column(Integer)
    team_triple_doubles = Column(Integer)

    def __init__(self, squad_id, stats):
        self.squad_id = squad_id
        for k, v in stats.iteritems():
            setattr(self, k, v)

    def update(self, stats):
        for k, v in stats.iteritems():
            setattr(self, k, v)


# - Squad -- /
class Squad(Base):
    """Squads contain basic information of a Team in a given season.

    One-to-many maps to SquadMembers, Games. Many-to-one map to Team."""
    __tablename__ = 'squad'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('team.id', onupdate='cascade', ondelete='cascade'))
    season_id = Column(Integer, ForeignKey('season.id', onupdate='cascade', ondelete='cascade'))
    year = Column(Integer, nullable=False)
    division = Column(String(4), nullable=False)
    conference_id = Column(Integer, ForeignKey('conference.id', onupdate='cascade', ondelete='cascade'))

    def __init__(self, division, season_id, year, team_id=None, conference=None):
        self.division = division
        self.season_id = season_id
        self.year = year
        if team_id is not None:
            self.team_id = team_id
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

    One-to-many maps to Squads."""
    __tablename__ = 'team'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)

    # NOTE squads = one-to-many map to Squads

    def __init__(self, name, id):
        self.name = name
        self.id = id


# - Season -- /
class Season(Base):
    """
    Use ncaa_id to determine season and gender, no matter what the division is.
    """
    __tablename__ = 'season'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)


# - Conference -- /
class Conference(Base):
    """
    A team may belong to different conference in different year and division.

    So conference will have one-to-one maps to Squad.
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


# - GameDetail -- /
class GameDetail(Base):
    """
    Play-by-Play information

    Many-to-one maps to Game.
    """
    __tablename__ = "gamedetail"
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('game.id', onupdate='cascade', ondelete='cascade'))
    # section could be 1st Half, 2nd Half with or without 1st OT
    section = Column(String(16))

    time = Column(String(16))
    score = Column(String(16))
    squad_id = Column(Integer, ForeignKey('squad.id', onupdate='cascade', ondelete='cascade'))
    detail = Column(String(256))

    def __init__(self, game_id, section, time, score, squad_id, detail):
        self.game_id = game_id
        self.section = section
        self.time = time
        self.score = score
        self.squad_id = squad_id
        self.detail = detail


Base.metadata.create_all(engine, checkfirst=True)
