# -*- coding: utf-8 -*-
import scrapy


class GoogleSpider(scrapy.Spider):
    name = "google"
    allowed_domains = ["google.com"]
    start_urls = (
        'http://www.google.com/',
    )

    def parse(self, response):
        pass
