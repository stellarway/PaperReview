# -*- coding: utf-8 -*-
import scrapy
import pandas as pd
from datetime import date
import time
from urllib import parse
from NaverNews.items import NavernewsItem

start = '2016.01.01'
end = '2016.12.31'

class NewsspiderSpider(scrapy.Spider):
    name = 'NewsSpider'
    start_urls = []

    keyword = '금리'
    # keyword = getattr(self, 'key', None)

    for i in pd.date_range(start=start, end=end):
        date=i.strftime('%Y%m%d')
        url='https://search.naver.com/search.naver?where=news&query={0}&sort=1&photo=0&field=0&reporter_article=&pd=3&ds={1}&de={1}&docid=&nso=so%3Add%2Cp%3Afrom{1}to{1}%2Ca%3Aall&mynews=1&refresh_start=0&related=0'.format(keyword, date)           
        start_urls.append(url)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url,
                                cookies={'news_office_checked': '1001,1018,2227'},
                                        callback=self.parse)


    def parse(self, response):
        
        for item in response.css('ul.type01 li'):
            url = item.css('a::attr(href)').get()
            
            if 'yna' in url:
                yield response.follow(url, self.parse_yna)
            if 'curType=read' in url:
                query_str = parse.parse_qs(parse.urlsplit(url).query)
                url = 'https://www.edaily.co.kr/news/read?newsId='+query_str['newsid'][0]
                yield response.follow(url, self.parse_edaily)
            if 'edaily' in url:
                yield response.follow(url, self.parse_edaily)
            if 'einfomax' in url:
                yield response.follow(url, self.parse_einfomax)
            if 'news.naver' in url:
                yield response.follow(url, self.parse_naver)

        next_page=response.css('div.paging a.next::attr(href)').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)


    def parse_yna(self, response):

        item= NavernewsItem()
        try:

            bodyList = response.css('div.article *::text').extract()

            title = response.css('h1.tit-article::text').get()
            source_of = '연합뉴스'
            date = response.css('span.tt::text').get()
            body=''.join(bodyList).replace('\r','').replace('\t','').replace('\n\n','')
            url = response.url

            item['source_of'] = source_of
            item['title'] = title
            item['date'] = date
            item['body'] = body
            item['url'] =url
            
            yield item

        except:
            item['url']= response.url
            item['title'] = '연합뉴스 에러'

            yield item
            # pass

  
    def parse_edaily(self, response):

        item= NavernewsItem()
        try:
            
            bodyList = response.css('div.news_body *::text').extract()

            title = response.css('div.news_titles h2::text').get()
            source_of = '이데일리'
            date= response.css('div.dates ul li::text').extract()[1].replace('등록', '')
            body=''.join(bodyList).replace('\r','').replace('\t','').replace('\n\n','').replace('  ','')
            url = response.url

            item['source_of'] = source_of
            item['title'] = title
            item['date'] = date
            item['body'] = body
            item['url'] =url
            

            yield item

        except:
            item['url']= response.url
            item['title'] = '이데일리 에러'

            yield item


    def parse_einfomax(self, response):

        item= NavernewsItem()
        try:

            bodyList = response.css('article.article-veiw-body *::text').extract()

            title = response.css('div.article-head-title::text').get()
            source_of = '연합인포맥스'
            date= response.css('ul.no-bullet li::text').extract()[1].replace(' 승인 ', '')
            body=''.join(bodyList).replace('\r','').replace('\t','').replace('\n\n','')
            url = response.url

            item['source_of'] = source_of
            item['title'] = title
            item['date'] = date
            item['body'] = body
            item['url'] =url

            yield item

        except:
            item['url']= response.url
            item['title'] = '연합인포맥스 에러'

            yield item


    def parse_naver(self, response):

        item= NavernewsItem()
        try:

            bodyList = response.css('div._article_body_contents *::text').extract()

            title = response.css('h3#articleTitle::text').get()
            source_of = response.css('div.press_logo a *::attr(title)').get()
            date = response.css('div.sponsor span.t11::text').get()
            body = ''.join(bodyList).replace('\r','').replace('\t','').replace('\n\n','').replace('// flash 오류를 우회하기 위한 함수 추가','').replace('function _flash_removeCallback() {}','')
            url = response.url
            
            item= NavernewsItem()

            item['source_of'] = source_of
            item['title'] = title
            item['date'] = date
            item['body'] = body
            item['url'] =url

            yield item

        except:
            item['url']= response.url
            item['title'] = '네이버뉴스 에러'

            yield item