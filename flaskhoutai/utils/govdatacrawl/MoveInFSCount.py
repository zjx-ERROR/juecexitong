import datetime
import requests
import demjson


headers = {
    'Referer': 'https://qianxi.baidu.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
}

params = {'dt': 'city',
        'id': '440600',
        'type': 'move_in',
        'date': (datetime.datetime.now()-datetime.timedelta(hours=28)).strftime('%Y%m%d'),
        'callback': ''}

url = 'https://huiyan.baidu.com/migration/cityrank.jsonp'


class Crawler:
    def __init__(self):
        self.session = requests.session()
        self.session.headers.update(headers)
        self.session.params.update(params)
        self.crawl_timestamp = int()

    def crawler(self):
        self.crawl_timestamp = int(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)
        try:
            r = self.session.get(url=url)
        except requests.exceptions.ChunkedEncodingError:
            pass
        res = demjson.decode(r.text[1:-1])
        if res["errmsg"] == "SUCCESS":
            move_information = res['data']['list']
            for mi in move_information:
                mi["crawlTime"] = self.crawl_timestamp
            return move_information

def main():
    crawler = Crawler()
    return crawler.crawler()
#
if __name__ == '__main__':
    print(main())
