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

        overall_information = re.search(r'\{("id".*?)\]\}', str(soup.find('script', attrs={'id': 'getStatisticsService'})))

        if overall_information:
            return self.overall_parser(overall_information=overall_information)

    def overall_parser(self, overall_information):
        overall_information = json.loads(overall_information.group(0))
        overall_information.pop('id')
        overall_information.pop('createTime')
        overall_information.pop('modifyTime')
        overall_information.pop('imgUrl')
        overall_information.pop('deleted')
        overall_information.pop('dailyPics')
        overall_information.pop('marquee')
        overall_information.pop('dailyPic')
        overall_information['crawlTime'] = self.crawl_timestamp
        overall_information['countRemark'] = overall_information['countRemark'].replace(' 疑似', '，疑似').replace(' 治愈', '，治愈').replace(' 死亡', '，死亡').replace(' ', '')
        return [overall_information]

def main():
    crawler = Crawler()
    return crawler.crawler()

if __name__ == '__main__':
    print(main())