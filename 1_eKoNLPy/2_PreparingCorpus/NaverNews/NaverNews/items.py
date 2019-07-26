# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class NavernewsItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    source_of= scrapy.Field()
    title = scrapy.Field()
    date = scrapy.Field()
    url = scrapy.Field()
    body = scrapy.Field()

    pass
