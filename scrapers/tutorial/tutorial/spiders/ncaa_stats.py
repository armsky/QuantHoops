# -*- coding: utf-8 -*-
import scrapy


class NcaaStatsSpider(scrapy.Spider):
    name = "ncaa_stats"
    allowed_domains = ["http://stats.ncaa.org/team/inst_team_list"]
    start_urls = (
        'http://www.http://stats.ncaa.org/team/inst_team_list/',
    )

    def parse(self, response):
        pass
