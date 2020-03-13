import datetime
import requests

total_url = "https://water.tisson.cn/epidemic/searchMap"
increase_url = "https://water.tisson.cn/epidemic/searchMap"
headers = {"Host": "water.tisson.cn",
        "Origin": "https://water.tisson.cn",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.4.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat",
        "Referer": "https://water.tisson.cn/epidemic/outbreakMap.html"}
form_data = {"add":1}

class Crawler:
    def __init__(self):
        self.session = requests.session()
        self.session.headers.update(headers)
        self.crawl_timestamp = int()


    def crawler(self):
        self.crawl_timestamp = int(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)
        try:
            total_data = self.session.post(url='https://water.tisson.cn/epidemic/searchMap').json()
            increase_data = self.session.post(url='https://water.tisson.cn/epidemic/searchMap',data=form_data).json()
        except requests.exceptions.ChunkedEncodingError:
            pass
        else:
            increaseids = []
            if increase_data:
                increaseids = [idata['id'] for idata in increase_data]
            if total_data:
                for tdata in total_data:
                    if tdata['id'] in increaseids:
                        tdata['increase'] = 1
                    else:
                        tdata['increase'] = 0
                    tdata['crawlTime'] = self.crawl_timestamp
                    tdata.pop('id')

            return total_data



def main():
    crawler = Crawler()
    return crawler.crawler()

if __name__ == '__main__':
    main()

