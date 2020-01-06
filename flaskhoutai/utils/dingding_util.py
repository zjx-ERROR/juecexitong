# !/usr/bin/python
# -*- conding:utf8-*-

import requests
import json
from instance.config import DING_URL


def ding(text,atMobiles=""):
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    # 定义信息函数
    text_info = {
        "msgtype": "text",
        "at": {
            "atMobiles": [
                atMobiles
            ],
            "isAtAll": False
        },
        "text": {
            "content": text
        }
    }

    requests.post(DING_URL, json.dumps(text_info), headers=headers)


if __name__ == '__main__':
    text = "钉钉发送测试"
    ding(text)
