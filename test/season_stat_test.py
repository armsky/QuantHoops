import unittest

from NCAA.ncaa import PlayerSeasonStat
from NCAA import settings

__author__ = 'Hao Lin'


class SeasonStatTest(unittest.TestCase):

    def test_player_season_stat(self):

        engine = settings.create_engine("men")
        session = settings.create_session(engine)

        squadmember_id = 84783

        player_season_stat_obj = session.query(PlayerSeasonStat).filter_by(squadmember_id=squadmember_id).first()

        self.assertIsNone(player_season_stat_obj)


if __name__ == "__main__":
    simple_test = SeasonStatTest()
    simple_test.test_player_season_stat()
