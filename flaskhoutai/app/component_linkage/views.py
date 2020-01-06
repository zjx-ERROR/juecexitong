#! usr/bin/python


from flask import Blueprint, request, jsonify,g
import pymysql
import json
from instance import config
from utils.dbutils import mysqlpool
from functools import reduce

# 创建组件联动的相关操作蓝图
component_linkage = Blueprint("component_linkage", __name__)

@component_linkage.route("/return_component_id/", methods=["POST"])
def return_component_id():
    """返回关联组件ID"""
    json_data = request.get_json()
    reportId = json_data.get("eportId")
    tableName = json_data["chartObj"]["tableName"]
    zujian = json_data["chartObj"]["zujianId"]
    if zujian == "":
        return jsonify({
            "code": 1,
            "data": []
        })
    elif reportId:
        try:
            conn = mysqlpool.get_conn()
            with conn.swich_db(config.WOWRKSHEET01, cursor=pymysql.cursors.Cursor) as cursor:
                component_id = conn.query_all("select componentid from {} where reportDBid=%s".format([config.TABLENAME5]),
                                              [reportId])
                list_01 = []
                for i in component_id:
                    columnMap_01 = conn.query_all("select columnMap,jsonstr from {} where id=%s".format(config.TABLENAME3), [i])
                    if columnMap_01[0][0] != None:
                        columnmap = eval(columnMap_01[0][0])
                        list_all = []
                        jk = []
                        for k in list(columnmap):
                            jk.append(k)
                            dict2 = str(columnmap[k]).replace(';', ',')

                            for j in [dict2]:
                                list_all.append(j)
                        data = [json.loads("[" + n + "]") for n in list_all]

                        dict_name = dict(zip(jk, data))
                        if tableName in dict_name and zujian != i[0]:
                            list_01.append({"componentid": i[0], "jsonstr": columnMap_01[0][1]})

            func = lambda x, y: x if y in x else x + [y]
            data_list = reduce(func, [[], ] + list_01)
            return jsonify({
                "code": 1,
                "data": data_list
            })

        except Exception as e:
            raise e


@component_linkage.route("/return_specified_field/", methods=["POST"])
def return_relation_id():
    json_data = request.get_json()
    componnent_id = json_data.get('zujianId')
    uid= g.token["id"]
    if componnent_id:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01, cursor=pymysql.cursors.Cursor) as cursor:
            worksheet_name = conn.query_one("select mSchema from {} where id = %s".format(config.TABLENAME3),
                                            componnent_id)
        if worksheet_name and worksheet_name[0]:
            # 关联组件名
            relation_worksheet_list = [worksheet_name[0]]
            conn = mysqlpool.get_conn()
            with conn.swich_db("%s_db"%uid) as cursor:
                data1 = conn.query_one('select begin_table from {} where end_table = %s'.format(config.ME2_TABLENAME4),
                                       worksheet_name[0])
                data2 = conn.query_one('select end_table from {} where begin_table = %s'.format(config.ME2_TABLENAME4),
                                       worksheet_name[0])
            if data1:
                for i in data1:
                    relation_worksheet_list.append(list(i.values())[0])
            if data2:
                for i in data2:
                    relation_worksheet_list.append(list(i.values())[0])
            jsondata = []
            conn = mysqlpool.get_conn()
            with conn.swich_db(config.WOWRKSHEET01) as cursor:
                for j in relation_worksheet_list:
                    result = conn.query_all("select id,jsonstr from {} where mSchema = %s".format(config.TABLENAME3), j)
                    if result:
                        jsondata.append(result)
                    return jsonify({'code': 1, 'data': jsondata})
    else:
        return jsonify({'code': 1, 'data': None})
