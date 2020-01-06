#! usr/bin/python

from flask import Blueprint, request, jsonify, Response ,g
from instance import config
import pymysql
import json
from xpinyin import Pinyin
from utils.dbutils import redis
from utils.token_utils import TokenMaker
from utils.dbutils import mysqlpool

# 创建数据采集的蓝图
public_data = Blueprint("public_data", __name__)

@public_data.route("/return_table_msg/", methods=["POST"])
def return_table_msg():
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.DBNAME3) as cursor:
        fetdata = conn.query_all('select id,cityEn,cityZh,provinceZh from city where provinceEn="guangdong"')
    return Response(json.dumps({"code": 1, "data": fetdata}), mimetype='application/json')

@public_data.route("/save_apitable/", methods=['POST'])
def save_apitable():
    obj = request.get_json()
    table_name = obj["tableName"]
    table_type = obj["tableType"]
    group_name = obj["groupName"]
    conn = mysqlpool.get_conn()
    uid = g.token.get("id")
    with conn.swich_db("%s_db"%uid) as cursor:
        if conn.query_one('select * from {TABLE} where worksheet_name = %s'.format(TABLE=config.ME2_TABLENAME2), table_name):
            return jsonify({"code": -1, "data": "改表名已存在"})
        elif not conn.query_one('select * from {TABLE} where id = %s'.format(TABLE=config.ME2_TABLENAME3), table_type):
            return jsonify({"code": -1, "data": "表类型不存在"})
        else:
            groupid = conn.query_one('select groupid from {TABLE} where type_name = %s'.format(TABLE=config.ME2_TABLENAME1), group_name)
            if groupid:
                try:
                    conn.insert_one(
                        'insert into {TABLE}(worksheet_name,groupid,origin_type_id) values(%s,%s,%s)'.format(TABLE=config.ME2_TABLENAME2),
                        [table_name, groupid, table_type])
                except Exception as e:
                    return jsonify({"code": -1, "data": "创建表失败"})
                else:
                    return jsonify({"code": -1, "data": "操作成功"})
            else:
                return jsonify({"code": -1, "data": "该分组不存在"})


@public_data.route("/save_pctable/", methods=['POST'])
def save_pctable():
    """
    保存工作表
    :return:
    """
    obj = request.get_json()
    table_type = obj["tableType"]
    change_table_datas = obj["changeTableDatas"]
    uid = g.token.get("id")
    conn = mysqlpool.get_conn()
    with conn.swich_db("%s_db" % uid,cursor=pymysql.cursors.Cursor) as cursor:
        for ctd in change_table_datas:
            if len(ctd):
                table_name = Pinyin().get_pinyin(ctd["tableName"], '')
                if conn.query_one('select * from {TABLE} where worksheet_name = %s'.format(config.ME2_TABLENAME2), table_name):
                    return jsonify({"code": -1, "data": "%s表已存在" % ctd["tableName"]})
                else:
                    try:
                        conn.insert_one(
                            'insert into {TABLE}(worksheet_name,groupid,worksheet_name_cn,origin_type_id) values(%s,%s,%s,%s)'.format(config.ME2_TABLENAME2),
                            [table_name, ctd["groupName"], ctd["tableName"], table_type])
                        cursor.commit()
                    except Exception as e:
                        return jsonify({"code": -1, "data": 'insert into' + str(e)})
                    try:
                        conn.create(
                            'create table ' + table_name + '_cn' + ' (id int primary key auto_increment,prime_name varchar(128),cn_name varchar(128),status int default 1)')
                        cursor.commit()
                    except Exception as e:
                        return jsonify({"code": -1, "data": str(e)})
                    try:
                        conn.insert_many(
                            'insert into ' + table_name + '_cn' + '(prime_name,cn_name,status) values(%s,%s,%s)',
                            [tuple(i.values())[0:3] for i in ctd["tableField"]])
                        cursor.commit()
                    except Exception as e:
                        return jsonify({"code": -1, "data": str(e)})
                    try:
                        conn.show('use %s;'%config.WOWRKSHEET01)
                        oldb = conn.query_all(
                            'select ds.link,cl.firTitle,cl.subTitle from {TABLE1} as ds,{TABLE2} as cl where cl.id = %s and ds.id = cl.datasourceId;'.format(TABLE1=config.TABLENAME4,TABLE2=config.TABLENAME46),
                            ctd["tableId"])[0]
                        conn.show("use %s_db" % uid)
                        old_table = oldb[0].replace('jdbc:mysql://127.0.0.1:3306/', '')
                        conn.create('create table ' + table_name + ' like ' + old_table + '.fetchdata_prp;')
                        cursor.commit()
                        conn.insert_one(
                            'insert into ' + "%s_db" % uid + '.' + table_name + ' select * from ' + old_table + '.fetchdata_prp where t1=%s and t2=%s;',
                            [oldb[1], oldb[2]])
                        cursor.commit()
                    except Exception as e:
                        return jsonify({"code": -1, "data": 'select' + str(e)})

    return jsonify({"code": 1, "data": "操作成功"})


@public_data.route("/cache_target/", methods=['POST'])
def cache_target():
    """
    缓存指标
    :return:
    """
    obj = request.get_json()
    token = obj["token"]
    datasource_id = obj["datasourceId"]
    reids_key = TokenMaker().generate_token(token, datasource_id)
    redis.set(reids_key, )


