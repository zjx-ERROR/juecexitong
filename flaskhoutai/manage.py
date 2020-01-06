#! usr/bin/python3
# -*- coding: utf-8 -*-
from gevent import monkey;monkey.patch_all()
from app import create_app
from flask import request, jsonify, g
from utils.token_utils import ResolveCacheToken
from instance import config


app = create_app()

@app.before_request
def tokenverify():
    if request.path == "/websocket/sysupervisord":
        pass
    elif request.method == "POST":
        if request.path == "/backstage/login/":
            pass
        elif request.path in config.tokenpath:
            pass
        else:
            if request.is_json:
                token = request.get_json().get("token")
            else:
                token = request.headers.get("token")
            p = ResolveCacheToken().resolve(token)
            g.token = p

            if not isinstance(p, dict):
                return jsonify({
                    "code": 500,
                    "data": "请重新登陆"
                })
            elif request.method == "OPTIONS":
                return jsonify({
                    "code": 1,
                    "data": "预检成功"
                })
    else:
        return jsonify({
            "code": -1,
            "data": "数据格式错误"
        })

if __name__ == "__main__":
    app.run()
