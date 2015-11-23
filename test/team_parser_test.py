import unittest

from NCAA import settings
from scrapers import scraper_helper

__author__ = 'Hao Lin'


class TeamParserTest():

    def test_team_parser(self):
        url = "http://stats.ncaa.org/team/inst_team_list/12260?division=1"
        team_links = scraper_helper.get_team_link(url)
        print team_links

if __name__ == "__main__":
    simple_test = TeamParserTest()
    simple_test.test_team_parser()
