from flask import Blueprint, request, jsonify, Response
import json
import datetime
from utils.dbutils import mysqlpool
from instance import config
import pymysql
from flask import g

# 创建 预案 蓝图
reserve_plan = Blueprint("reserve_plan", __name__)

@reserve_plan.route("/save_reserve/", methods=["POST"])
def save_reserve():
    json_data = request.get_json()
    return jsonify({
        "code": 1,
        "data": "保存成功"
    })

@reserve_plan.route("/seacher_reserve/", methods=["POST"])
def seacher_reserve():
    json_data = request.get_json()
    param = json_data["param"]
    reserve = []
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            reserve_list = conn.query_all(
                "select * from {} where param=%s order by grade ASC".format(config.TABLENAME13), param)
        for i in reserve_list:
            reserve.append(i)
    except Exception as e:
        raise e
    return jsonify({
        "code": 1,
        "data": reserve
    })


@reserve_plan.route("/update_reserve/", methods=["POST"])
def update_reserve():
    json_data = request.get_json()
    pushArr = json_data["pushArr"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            for i in pushArr:
                param = i["param"]
                grade = i["grade"]
                number = i["number"]
                conn.update("update {} set number=%s where param=%s and grade=%s".format(config.TABLENAME13),
                            [number, param, grade])
    except Exception as e:
        raise e
    return jsonify({
        "code": 1,
        "data": "修改数据成功"
    })

@reserve_plan.route("/get_reserveparam/", methods=["POST"])
def get_reserveparam():
    """通过组件id 获取组件绑定的参数"""
    """项目比拼 预案临时接口"""
    json_data = request.get_json()
    if "id" in dict(json_data).keys():
        zujianid = json_data["id"]
        try:
            conn = mysqlpool.get_conn()
            with conn.swich_db(config.WOWRKSHEET01) as cursor:
                if conn.query_one("select reserve_param from {} where id= %s".format(config.TABLENAME3),[zujianid]):
                    reserve_param = conn.query_one("select reserve_param from {} where id= %s".format(config.TABLENAME3),[zujianid])
                    if not reserve_param["reserve_param"]:
                        reserve_param = []
                    else:
                        reserve_param = eval(reserve_param["reserve_param"])
                    param_list = conn.query_all("select * from {} where param= '拥堵系数'".format(config.TABLENAME13))
                    if not param_list:
                        param_list = []
                    return jsonify({
                        "code": 1,
                        "data": {
                            "reserve_param": reserve_param,
                            "param_list": param_list
                        }
                    })
                else:
                    return jsonify({
                        "code": 1,
                        "data": {
                            "reserve_param":"",
                            "param_list": ""
                        }
                    })
        except Exception as e:
            raise e
    else:
        return jsonify({
            "code": -1,
            "data": []
        })
