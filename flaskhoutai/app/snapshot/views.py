from flask import Blueprint, request, jsonify
import time
import datetime
from utils.dbutils import mysqlpool
from instance import config
import pymysql
from flask import g

# 创建快照功能蓝图
snapshot_data = Blueprint("snapshot_data", __name__)

@snapshot_data.route("/return_snapshot/", methods=["POST"])
def return_snapshot():
    """返回快照内容"""
    json_data = request.get_json()
    reportId = json_data["reportId"]
    uid = g.token["id"]
    chartData = []
    quotaData = []
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if "id" in dict(json_data).keys():
                # 历史快照 id
                history_snapshotID = json_data["id"]
                history_createDate = conn.query_one("select createDate from {} where id=%s".format(config.TABLENAME8),
                                                    history_snapshotID)
                snapshot_createdate = history_createDate["createDate"].strftime("%Y-%m-%d %H:%M:%S")
                bigArr_list = conn.query_all(
                    "select * from {} where reportId=%s and uid=%s and snapshot_createdate=%s".format(
                        config.TABLENAME7), [reportId, uid, snapshot_createdate])
                smallArr_list = conn.query_all(
                    "select * from {} where uid= %s and snapshot_createdate=%s  ".format(config.TABLENAME6),
                    [uid, snapshot_createdate])
            else:
                bigArr_list = conn.query_all("select * from {} where reportId=%s and uid=%s ".format(config.TABLENAME7),
                                             [reportId, uid])
                smallArr_list = conn.query_all("select * from {} where uid= %s ".format(config.TABLENAME6), [uid])

        if bigArr_list:
            for i in bigArr_list:
                quotaData.append(i)
        else:
            quotaData = ""
        if smallArr_list:
            for j in smallArr_list:
                chartData.append(j)
        else:
            chartData = ""
        return jsonify({
            "code": 1,
            "data": {
                "chartData": chartData,
                "quotaData": quotaData
            }
        })
    except Exception as e:
        raise e


@snapshot_data.route("/save_snapshot/", methods=["POST"])
def save_snapshot():
    "保存报表快照内容"
    json_data = request.get_json()
    bigArr = json_data["bigArr"]
    smallArr = json_data["smallArr"]
    reportId = json_data["reportId"]
    uid = g.token["id"]
    now_time = datetime.datetime.now()
    createDate = datetime.datetime.strftime(now_time, '%Y-%m-%d %H:%M:%S')
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            conn.insert_one(
                "insert into {table} (reportId,createDate,uid) values (%s,%s,%s)".format(table=config.TABLENAME8),
                [reportId, createDate, uid])
            for i in bigArr:
                id = i["id"]
                relationStr = i["relationStr"]
                size01 = i["size"]
                str01 = i["str"]
                count = conn.query_one(
                    "select count(*) as count from {table} where id=%s and reportId=%s and uid=%s and snapshot_createdate=%s".format(
                        table=config.TABLENAME7), [id, reportId, uid, createDate])
                if int(count["count"]) > 0:
                    "有重复数据，覆盖数据"
                    conn.update(
                        "update {table} set id=%s, relationStr=%s,size01=%s,str01=%s,reportId=%s, uid=%s where id=%s and reportId=%s and uid=%s and snapshot_createdate=%s".format(
                            table=config.TABLENAME7),
                        [id, relationStr, size01, str01, reportId, uid, id, reportId, uid, createDate])
                else:
                    "无重复数据  数据直接插入"
                    conn.insert_one(
                        "insert into {TABLE} (id, relationStr,size01,str01, reportId,uid,snapshot_createdate) values (%s, %s,%s,%s,%s,%s,%s)".format(
                            TABLE=config.TABLENAME7), [id, relationStr, size01, str01, reportId, uid, createDate])
            conn.commit()
            for j in smallArr:
                categoryId = j["categoryId"]
                snapshot_createDate = j["createDate"]
                snapshot_editDate = j["editDate"]
                flag = j["flag"]
                have = j["have"]
                id = j["id"]
                name1 = j["name1"]
                name2 = j["name2"]
                name3 = j["name3"]
                name4 = j["name4"]
                name5 = j["name5"]
                size = j["size"]
                thumbnail = j["thumbnail"]
                title = j["title"]
                uid = j["uid"]
                unit1 = j["unit1"]
                unit2 = j["unit2"]
                unit3 = j["unit3"]
                unit4 = j["unit4"]
                unit5 = j["unit5"]
                value1 = j["value1"]
                value2 = j["value2"]
                value3 = j["value3"]
                value4 = j["value4"]
                value5 = j["value5"]
                conn.insert_one(
                    "insert into {} (id,uid,thumbnail,categoryId,  title,name1,value1,unit1,name2, value2,unit2,name3,value3,unit3, name4,value4,unit4,name5,value5, unit5,createDate,editDate,flag,snapshot_createdate) values (%s, %s, %s, %s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s)".format(
                        config.TABLENAME6),
                    [id, uid, thumbnail, categoryId, title, name1, value1, unit1, name2, value2, unit2, name3, value3,
                     unit3, name4, value4, unit4, name5, value5, unit5, snapshot_createDate, snapshot_editDate, flag,
                     createDate])
        return jsonify({
            "code": 1,
            "data": "快照保存成功"
        })
    except Exception as e:
        raise e


@snapshot_data.route("/return_history_snapshotlist/", methods=["POST"])  # 返回历史快照信息
def return_history_snapshotlist():
    json_data = request.get_json()
    reportId = json_data["reportId"]
    uid = g.token["id"]
    snapshot_data = []
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if conn.query_one("select id, createDate from {} where uid= %s and reportId= %s order by createDate DESC".format(config.TABLENAME8),
                              [uid, reportId]):
                history_shapshot = conn.query_all(
                    "select id, createDate from {} where uid= %s and reportId= %s order by createDate DESC".format(config.TABLENAME8),
                    [uid, reportId])
                for i in history_shapshot:
                    i["createDate"] = i["createDate"].strftime("%Y-%m-%d %H:%M:%S")
                    snapshot_data.append(i)
                return jsonify({
                    "code": 1,
                    "data": snapshot_data
                })
            else:
                return jsonify({
                    "code": 1,
                    "data": []
                })
    except Exception as e:
        raise e



@snapshot_data.route("/modifyreport_styleId/", methods=["POST"])
def modifyreport_styleId():
    json_data = request.get_json()
    reportId = json_data["id"]
    styleId = json_data["styleId"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            conn.update("update {} set styleId=%s where id=%s".format(config.TABLENAME9), [styleId, reportId])
        return jsonify({
            "code": 1,
            "data": "修改成功"
        })
    except Exception as e:
        raise e
