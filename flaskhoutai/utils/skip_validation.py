from utils.dbutils import mysqlpool
from instance import config
import pymysql
from flask import request,jsonify,g
from utils.token_utils import ResolveCacheToken

def skip_validation(url2):
    msgid = url2[:len(url2) - 6]
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        if conn.query_one("select * from {} where id=%s".format(config.TABLENAME20),[msgid]):
            msg= conn.query_one("select * from {} where id=%s".format(config.TABLENAME20),[msgid])
            if msg["url2"]== url2:
                return True
        else:
            return False





def login_validate():
    if request.is_json:
        token = request.get_json().get("token")
    else:
        token = request.headers.get("token")

    p = ResolveCacheToken().resolve(token)
    g.token = p

    if not isinstance(p, dict):
        return jsonify({
            "code": -1,
            "data": "请重新登陆"
        })

    elif request.method == "OPTIONS":
        return jsonify({
            "code": 1,
            "data": "预检成功"
        })
