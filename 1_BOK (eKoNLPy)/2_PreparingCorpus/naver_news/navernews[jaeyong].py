# -*- coding: utf-8 -*-

import scrapy
from tutorial.items import NewsItem
from datetime import date
from datetime import timedelta, date
import re

# startdate과 enddate 사이에 있는 날짜들을 만들어 주는 함수
def daterange(date1, date2):
    for n in range(int ((date2 - date1).days)+1):
        yield date1 + timedelta(n)

class NavernewsSpider(scrapy.Spider):
    name = 'navernews'

    # 20050101~20171231까지 
    # 246850건 중에서 244495건 -> 2355개 손실 (연합인포맥스 link 에러, 빈 내용의 기사)

    startDate = date(2005, 1, 1)   #시작날짜
    endDate = date(2017, 12, 31)     #종료날짜
    # endDate = date.today()
    keyword = '금리'                 #키워드

    dateList = []
    start_urls = []

    # 이메일 pattern
    pattern = r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
    
    # date를 href에 맞는 형식으로 만들어 준다.
    for dt in daterange(startDate, endDate):
        dateList.append(dt.strftime("%Y.%m.%d"))
    
    # date를 이용하여 start_urls을 만들어준다.
    for i in dateList:
        reqURL = "https://search.naver.com/search.naver?where=news&query={}&sort=1&photo=0&field=0&reporter_article=&pd=3&ds={}&de={}&docid=&nso=so%3Add%2Cp%3Afrom{}to{}%2Ca%3Aall&mynews=1&refresh_start=0&related=0".format(keyword, i, i, i.replace(".",""), i.replace(".",""))
        start_urls.append(reqURL)


    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url,
                                #연합뉴스, 연합인포, 이데일리를 지정하는 쿠키 
                                 cookies={'news_office_checked':'1001,1018,2227'},
                                 callback=self.parse)
        
    def parse(self, response):
        for i in response.css('div.news ul.type01 li'):
            # 제목에 딸린 href
            href = i.css('dt a::attr(href)').get()

            # news office에 따라 yield를 지정
            # 연합인포맥스
            if i.css('dd.txt_inline a::attr(href)').get()=='#':
                yield response.follow(href, self.yhif_news)
            # 네이버뉴스에서의 이데일리, 연합뉴스
            else:
                naver_href = i.css('dd.txt_inline a::attr(href)').get()
                yield response.follow(naver_href, self.naver_news)

        # next page
        next_page = response.css('div.paging a.next::attr(href)').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)


    # 연합인포맥스를 제외한 이데일리, 연합뉴스는 네이버 뉴스에 있는 기사를 크롤링


    # 연합인포뉴스
    # 연합인포뉴스는 가끔 삭제된 기사의 href가 있음
    def yhif_news(self, response):
        try:
            endRe = re.compile(r'\(.?끝.?\)')
            item = NewsItem()
            item['href'] = response.url
            item['title'] = response.css('div.article-header-wrap div.article-head-title::text').get()
            bodyList = response.css('section.user-snb article.article-veiw-body div#article-view-content-div *::text').getall()
            
            bodyToStr = "".join([i.strip() for i in bodyList])
            
            # 보통 기사가 (끝)으로 끝나기 때문에 짤라줌
            if not endRe.search(bodyToStr)==None:
                bodyToStr = bodyToStr.replace(endRe.search(bodyToStr).group(),'').strip()  

            # body에서 이메일 지움
            bodyToStr = re.sub(pattern = self.pattern, repl = '', string = bodyToStr)
            item['content'] = bodyToStr.replace('@yna.co.kr', '')
            
            datetime = re.split(' ', response.css('section.article-head-info div.info-text ul.no-bullet li::text').getall()[1])
            item['date'] = re.sub('[.]','',datetime[2])

            yield item
        except:
            item['title'] = "연합인포맥스 에러"
            item['href'] = response.url
                
            yield item


    # 네이버 뉴스
    def naver_news(self, response):
        item = NewsItem()
        item['href'] = response.url
        try:
            # entertain in href
            if "entertain.naver.com" in response.url:  
                bodyList = response.css('div.end_body_wrp div#articeBody *::text').getall()
                chkBodyList = [i.strip() for i in bodyList][:-4]
                bodyToStr = "".join(chkBodyList)
                item['content'] = re.sub(pattern = self.pattern, repl = '', string = bodyToStr)
                item['title'] = response.css('div.end_ct_area h2.end_tit::text').get().strip()
                datetime = re.split(" ", response.css('div.article_info span.author em::text').get())

            # sports in href
            elif "sports.news.naver.com" in response.url: 
                bodyList = response.css('div.content_area div#newsEndContents *::text').getall()
                chkBodyList = [i.strip() for i in bodyList][:-3]
                bodyToStr = "".join(chkBodyList)
                item['content'] = re.sub(pattern = self.pattern, repl = '', string = bodyToStr)
                item['title'] = response.css('div.content_area div.news_headline h4::text').get().strip()
                date = response.css('div.content_area div.news_headline div.info span::text').get()
                datetime = re.split(" ", re.sub('기사입력', '', date).strip())

            # 나머지 네이버 뉴스
            else:
                newOffice = response.css('div.press_logo a img::attr(title)').get()
                
                # 이데일리, 연합뉴스 각각 content를 다르게 다룸
                cutHead = response.css("div.article_body div#articleBodyContents script:not([class])::text").get()
                bodyText = response.css('div.article_body div#articleBodyContents *::text').getall()
                
                # 이데일리 
                if newOffice=="이데일리":
                    cutTail = response.css("div.article_body div#articleBodyContents p:not([class])::text").get()
                    
                    # 이데일리 기사가 네이버 형식일 때, 중복되는 기사 본문의 앞부분과 뒷부분을 제거
                    bodyToStr = "".join([i.strip() for i in bodyText]).replace(cutHead.strip(),"")

                    if cutTail:
                        bodyToStr = bodyToStr.replace(cutTail.strip(),"")

                # 연합뉴스 
                else:
                    cutTail = response.css("div.article_body div#articleBodyContents a:not([class])::text").get()

                    # 연합뉴스 기사가 네이버 형식일 때, 중복되는 기사 본문의 앞부분과 뒷부분을 제거
                    if cutTail:
                        bodyToStr = "".join([i.strip() for i in bodyText]).replace(cutHead.strip(),"").split(cutTail)[0]
                    else:
                        bodyToStr = "".join([i.strip() for i in bodyText]).replace(cutHead.strip(),"")
                

                item['content'] = re.sub(pattern = self.pattern, repl = '', string = bodyToStr)
                item['title'] = response.css('div.article_info h3#articleTitle::text').get()

                datetime = re.split(" ", response.css('div.article_info div.sponsor span.t11::text').get())

                item['date'] = re.sub('[.]', '', datetime[0])

            yield item

        except:
            item['title'] = response.css('div.article_header div.press_logo a img::attr(title)').get() + " 에러"
            item['href'] = response.url
                
            yield item