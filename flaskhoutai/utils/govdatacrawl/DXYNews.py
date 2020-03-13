# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import re
import json
import time

import datetime
import requests


headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
}


class Crawler:
    def __init__(self):
        self.session = requests.session()
        self.session.headers.update(headers)
        self.crawl_timestamp = int()

    # def run(self):
    #     while True:
    #         self.crawler()
    #         time.sleep(60)

    def crawler(self):
        self.crawl_timestamp = int(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)
        try:
            r = self.session.get(url='https://3g.dxy.cn/newh5/view/pneumonia')
        except requests.exceptions.ChunkedEncodingError:
            pass
        soup = BeautifulSoup(r.content, 'lxml')

        news = re.search(r'\[(.*?)\]', str(soup.find('script', attrs={'id': 'getTimelineService'})))

        if news:
            return self.news_parser(news=news)

    def news_parser(self, news):
        news = json.loads(news.group(0))
        pre_data = []
        for _news in news:
            pre_data_dict = {}
            pre_data_dict['pubDate'] = _news['pubDate']
            pre_data_dict['title'] = _news['title']
            pre_data_dict['summary'] = _news['summary'].replace('\n','').replace(' ','')
            pre_data_dict['infoSource'] = _news['infoSource']
            pre_data_dict['crawlTime'] = self.crawl_timestamp
            pre_data.append(pre_data_dict)
        return pre_data



def main():
    crawler = Crawler()
    return crawler.crawler()

if __name__ == '__main__':
    print(main())