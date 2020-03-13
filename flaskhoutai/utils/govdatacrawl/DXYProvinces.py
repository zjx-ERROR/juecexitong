from bs4 import BeautifulSoup
import re
import json
import datetime
import requests
import time

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
}

class Crawler:
    def __init__(self):
        self.session = requests.session()
        self.session.headers.update(headers)
        self.crawl_timestamp = int()

    def run(self):
        while True:
            try:
                self.crawler()
            except Exception:
                pass
            finally:
                print(self.crawl_timestamp)
                time.sleep(300)

    def crawler(self):
        self.crawl_timestamp = int(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)
        try:
            r = self.session.get(url='https://3g.dxy.cn/newh5/view/pneumonia')
        except requests.exceptions.ChunkedEncodingError:
            pass
        else:
            soup = BeautifulSoup(r.content, 'lxml')

            area_information = re.search(r'\[(.*)\]', str(soup.find('script', attrs={'id': 'getAreaStat'})))

            if area_information:
                return self.area_parser(area_information=area_information)


    def area_parser(self, area_information):
        area_information = json.loads(area_information.group(0))
        for area in area_information:
            area.pop('cities')
            area['crawlTime'] = self.crawl_timestamp
        return area_information


def main():
    crawler = Crawler()
    return crawler.crawler()

if __name__ == '__main__':
    main()


