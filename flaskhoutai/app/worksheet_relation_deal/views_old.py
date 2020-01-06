#! usr/bin/python


from flask import Blueprint, request, jsonify
import pymysql
import json
from instance import config
import datetime
import os, base64
from app.connection_db import mycursor, mydb
from utils.dbutils import mysqldb
import redis

# 创建关联工作表之后内容的相关操作蓝图
operation_worksheet = Blueprint("operation_worksheet", __name__)


@operation_worksheet.route("/return_all_worksheets/", methods=["POST"])
def return_all_worksheets():
    """返回工作表"""
    if request.method == "POST":
        group_id = request.get_json()["id"]
        try:
            mycursor.execute('use {}'.format(config.DBNAME2))
            mycur = mydb.cursor(cursor=pymysql.cursors.DictCursor)

            if group_id == 0:
                mycur.execute("select id, worksheet_name, worksheet_name_cn from {}".format(config.ME2_TABLENAME2))
                obj_list = mycur.fetchall()
                mydb.commit()
                return jsonify({
                    "code": 1,
                    "data": obj_list
                })

            else:
                mycur.execute("select id, worksheet_name, worksheet_name_cn from {} where groupid={}".format(
                    config.ME2_TABLENAME2, group_id))
                obj_list = mycur.fetchall()
                mydb.commit()
                return jsonify({
                    "code": 1,
                    "data": obj_list
                })

        except Exception as e:
            return jsonify({
                "code": -1,
                "msg": str(e)
            })

    else:
        return jsonify({
            "code": -1,
            "msg": "返回失败"
        })


@operation_worksheet.route("/return_relation_worksheets/", methods=["POST"])
def return_relation_worksheets():
    """返回表，关联表，字段"""
    if request.method == "POST":
        file_name = request.get_json()["worksheet_name"]
        try:
            mycursor.execute('use {}'.format(config.DBNAME2))
            mycur = mydb.cursor(cursor=pymysql.cursors.DictCursor)
            content_list = []
            if mycur.execute("select * from association_table_relation where begin_table ='{}' or end_table='{}'".
                                     format(file_name, file_name)):
                if mycur.execute(
                        "select end_table from association_table_relation where begin_table='{}'".format(file_name)):
                    obj_en = mycur.fetchall()
                else:
                    obj_en = []

                if mycur.execute(
                        "select begin_table from association_table_relation where end_table='{}'".format(file_name)):
                    obj_be = mycur.fetchall()
                else:
                    obj_be = []

                for i in obj_be:
                    obj_en.append(i)

                obj_en.insert(0, {"worksheet_name": file_name})
                for j in obj_en:
                    value = list(j.values())[0]
                    mycur.execute("select file_name_cn from association_table where file_name={}".format(repr(value)))
                    cn_name = mycur.fetchall()[0]
                    d = {list(j.values())[0]: list(cn_name.values())[0]}
                    table_name = value + "_" + "cn"
                    mycur.execute("select * from {}".format(table_name))
                    obj = mycur.fetchall()
                    obj.append(d)
                    content_list.append(obj)
                mydb.commit()

                return jsonify({
                    "code": 1,
                    "data": content_list

                })
            else:
                mycur.execute(
                    "select worksheet_name_cn from worksheet_relation where worksheet_name={}".format(repr(file_name)))
                cn_name = mycur.fetchall()[0]
                d = {'{}'.format(file_name): list(cn_name.values())[0]}
                table_name = file_name + "_" + "cn"
                mycur.execute("select * from {}".format(table_name))
                obj = mycur.fetchall()
                obj.append(d)
                content_list.append(obj)
                mydb.commit()

                return jsonify({
                    "code": 1,
                    "data": content_list

                })

        except Exception as e:
            return jsonify({
                "code": -1,
                "msg": str(e)
            })

    else:
        return jsonify({
            "code": -1,
            "msg": "返回失败"
        })


@operation_worksheet.route("/return_relation_contents/", methods=["POST", "GET"])
def return_relation_contents():
    """非关联表、关联表之间的字段内容"""
    if request.method == "POST":
        json_data = request.get_json()
        columnmap = json_data["columnMap"]
        schema = json_data["schema"]

        list_all = []
        jk = []
        for i in list(columnmap):
            jk.append(i)
            dict2 = str(columnmap[i]).replace(';', ',')
            for j in [dict2]:
                list_all.append(j)
        data = [json.loads("[" + i + "]") for i in list_all]
        dict_name = dict(zip(jk, data))

        mycursor.execute('use {}'.format(config.DBNAME2))
        mycur = mydb.cursor(cursor=pymysql.cursors.DictCursor)
        content = []

        if mycur.execute("select * from association_table_relation where begin_table ='{}' or end_table='{}'".
                                 format(schema, schema)):

            if list(dict_name.keys())[0] == schema:
                for j in dict_name[schema]:
                    x_columnName = j["columnName"]
                    schema_name = schema + "-" + x_columnName
                    mycur.execute("select `{}` from {}".format(x_columnName, schema))
                    relation_list = mycur.fetchall()
                    for i in relation_list:
                        relation_list.append({schema_name: list(relation_list.pop(0).values())[0]})
                    content.append(relation_list)

                for y in list(dict_name):
                    for p in dict_name[y]:
                        columnName = p["columnName"]
                        new_columnName = y + "-" + columnName
                        mycur.execute(
                            "select * from association_table_relation where begin_table='{}' and end_table='{}' or begin_table='{}' and end_table='{}'".
                                format(schema, y, y, schema))
                        all_relation_table = mycur.fetchall()
                        for k in all_relation_table:
                            begin_table = k["begin_table"]
                            end_table = k["end_table"]
                            begin_table_cn = begin_table + "_" + "cn"
                            end_table_cn = end_table + "_" + "cn"
                            line = k["line"]
                            associated_field_01 = k["associated_field_01"]
                            associated_field_02 = k["associated_field_02"]

                            mycur.execute(
                                "select prime_name, cn_name from {} where prime_name='{}' or cn_name='{}'".format(
                                    begin_table_cn,
                                    associated_field_01,
                                    associated_field_01))
                            table_name = mycur.fetchall()[0]
                            prime_name = table_name["prime_name"]
                            cn_name = table_name["cn_name"]
                            if mycur.execute(
                                    "select count(*) from information_schema.columns where table_name = '{}' and column_name = '{}'".format(
                                        begin_table, prime_name)):
                                associated_field_01 = cn_name
                            else:
                                associated_field_01 = prime_name

                            mycur.execute(
                                "select prime_name, cn_name from {} where prime_name='{}' or cn_name='{}'".format(
                                    end_table_cn,
                                    associated_field_02,
                                    associated_field_02))
                            table_name_02 = mycur.fetchall()[0]
                            prime_name_02 = table_name_02["prime_name"]
                            cn_name_02 = table_name_02["cn_name"]
                            if mycur.execute(
                                    "select count(*) from information_schema.columns where table_name = '{}' and column_name = '{}'".format(
                                        end_table, prime_name_02)):
                                associated_field_02 = cn_name_02
                            else:
                                associated_field_02 = prime_name_02

                            if begin_table == schema:
                                data_table = end_table
                            else:
                                data_table = begin_table

                            if line == "全部联接":
                                print("---------全部联接-----------")
                                mycur.execute("SELECT {}.`{}` from {} LEFT JOIN {} on {}.`{}`={}.`{}` UNION "
                                              "SELECT {}.`{}` from {} RIGHT JOIN {} on {}.`{}`={}.`{}`".
                                              format(data_table, columnName, begin_table, end_table, begin_table,
                                                     associated_field_01, end_table, associated_field_02,
                                                     data_table, columnName, begin_table, end_table, begin_table,
                                                     associated_field_01, end_table, associated_field_02))
                                content_list = mycur.fetchall()
                                for i in content_list:
                                    content_list.append({new_columnName: list(content_list.pop(0).values())[0]})
                                content.append(content_list)
                                mydb.commit()

                            elif line == "左侧联接":
                                print("---------左侧联接-----------")
                                mycur.execute(
                                    "select {}.`{}` from {} LEFT JOIN {} on {}.`{}`={}.`{}`".format(data_table,
                                                                                                    columnName,
                                                                                                    begin_table,
                                                                                                    end_table,
                                                                                                    begin_table,
                                                                                                    associated_field_01,
                                                                                                    end_table,
                                                                                                    associated_field_02, ))
                                content_list = mycur.fetchall()
                                for i in content_list:
                                    content_list.append({new_columnName: list(content_list.pop(0).values())[0]})

                                content.append(content_list)
                                mydb.commit()

                            elif line == "右侧联接":
                                print("---------右侧联接-----------")
                                mycur.execute("select {}.`{}` from {} RIGHT JOIN {} on {}.`{}`={}.`{}`".format(
                                    data_table, columnName, begin_table, end_table, begin_table, associated_field_01,
                                    end_table, associated_field_02, ))
                                content_list = mycur.fetchall()
                                for i in content_list:
                                    content_list.append({new_columnName: list(content_list.pop(0).values())[0]})
                                content.append(content_list)
                                mydb.commit()

                            elif line == "内部联接":
                                print("---------内部联接-----------")
                                mycur.execute("select {}.`{}` from {} INNER JOIN {} on {}.`{}`={}.`{}`".format(
                                    data_table, columnName, begin_table, end_table, begin_table, associated_field_01,
                                    end_table, associated_field_02, ))
                                content_list = mycur.fetchall()
                                if content_list == ():
                                    return jsonify({
                                        "code": -1,
                                        "msg": "无数据"
                                    })
                                else:
                                    for i in content_list:
                                        content_list.append({new_columnName: list(content_list.pop(0).values())[0]})
                                    content.append(content_list)
                                mydb.commit()

                relation_all = content[0]
                for i in content[1:]:
                    for n, m in enumerate(relation_all):
                        m.update(i[n])
                return jsonify({
                    "code": 1,
                    "data": relation_all
                })

        else:
            for j in dict_name[schema]:
                print(dict_name)
                x_columnName = j["columnName"]
                schema_name = schema + "-" + x_columnName
                mycur.execute("select `{}` from {}".format(x_columnName, schema))
                relation_list = mycur.fetchall()
                for i in relation_list:
                    relation_list.append({schema_name: list(relation_list.pop(0).values())[0]})
                content.append(relation_list)
            relation_all = content[0]
            for i in content[1:]:
                for n, m in enumerate(relation_all):
                    m.update(i[n])
            return jsonify({
                "code": 1,
                "data": relation_all
            })

    else:
        return jsonify({
            "code": -1,
            "msg": "失败"
        })


@operation_worksheet.route("/save_component_db/", methods=["POST"])
def save_component_db():
    """保存修改组件到数据库"""
    if request.method == "POST":
        json_data = request.get_json()
        token = json_data["token"]
        r = redis.Redis(host='120.31.140.112', password='jcxt@123456', port=6380, db=0)
        redis_data = r.get("userID:%s" % token)[7:]
        data = json.loads(redis_data, encoding="utf-8")
        uid = data["id"]
        jsonstr = json_data["jsonstr"]
        thumbnail = json_data["thumbnail"].split(",")[-1]
        imgdata = base64.b64decode(thumbnail)
        now_time = datetime.datetime.now()
        time_01 = now_time.strftime("%Y%m%d%H%M%S")
        time_02 = now_time.strftime("%Y-%m-%d %H:%M:%S")
        path01 = "/usr/local/bigscreen/componentManagement/upload/chart/chart_" + time_01 + ".jpg"
        path = "/upload/chart/chart_" + time_01 + ".jpg"
        # path = "C:/Users\Administrator\Desktop/" + time_01 + ".jpg"
        file = open(path01, "wb")
        file.write(imgdata)
        file.close()
        theme = str(json_data["theme"])
        main_title = str(json_data["mainTitle"])
        subtitle = str(json_data["subtitle"])
        stype = str(json_data["type"])
        other_opt = str(json_data["otherOpt"])
        chartDataSourceId = str(json_data["chartDataSourceId"])
        mSchema = str(json_data["schema"])
        columnMap = str(json_data["columnMap"])
        selectArr = str(json_data["selectArr"])
        selectVArr = str(json_data["selectVArr"])

        try:
            mysqldb.begin(config.WOWRKSHEET01, cursor=pymysql.cursors.Cursor)
            if "id" in dict(json_data).keys():
                print("进入有id")
                id = json_data["id"]
                mysqldb.update(
                    "update test_tubiao_goucheng  set uid=%s,jsonstr=%s,thumbnail=%s,theme=%s,main_title=%s,subtitle=%s,`type`=%s ,other_opt=%s,chartDataSourceId=%s,mSchema=%s,columnMap=%s,selectArr=%s,selectVArr=%s,editDate=%s where id=%s",
                    [uid, jsonstr, path, theme, main_title, subtitle, stype, other_opt, chartDataSourceId, mSchema,
                     columnMap, selectArr, selectVArr, time_02, id])

                mysqldb.end()
                return jsonify({
                    "code": 1,
                    "data": "保存成功"
                })

            else:
                print("进入没有id")
                id = time_01
                try:
                    mysqldb.insertOne(
                        'insert into test_tubiao_goucheng(id,uid,jsonstr,thumbnail,theme,main_title,subtitle,`type` ,other_opt,chartDataSourceId,mSchema,columnMap,selectArr,selectVArr,createDate,editDate) VALUES (%s,%s,%s, %s, %s,%s,%s,%s,%s,%s, %s, %s,%s,%s,%s,%s)',
                        [id, uid, jsonstr, path, theme, main_title, subtitle, stype, other_opt, chartDataSourceId,
                         mSchema,
                         columnMap, selectArr, selectVArr, time_02, time_02])
                except Exception as e:
                    print("e", e)
                data_id = mysqldb.getOne("select id from test_tubiao_goucheng where jsonstr=%s and thumbnail=%s",
                                         [jsonstr, path])

                mysqldb.end()
                return jsonify({
                    "code": 1,
                    "msg": data_id[0]
                })

        except Exception as e:
            mysqldb.end("rollback")
            raise e


@operation_worksheet.route("/return_component_con/", methods=["POST"])
def return_component_con():
    """返回组件中的内容"""
    if request.method == "POST":
        component_id = request.get_json()["id"]
        try:
            mysqldb.begin(config.WOWRKSHEET01, cursor=pymysql.cursors.Cursor)
            component_con = mysqldb.getOne(
                "select other_opt, selectArr, selectVArr from test_tubiao_goucheng where id=%s",
                [component_id])

            mysqldb.end()
            return jsonify({
                "code": 1,
                "data": [{"other_opt": str(component_con[0]).replace("'", '"')},
                         {"selectArr": str(component_con[1]).replace("'", '"')},
                         {"selectVArr": str(component_con[2]).replace("'", '"')}]
            })

        except Exception as e:
            mysqldb.end("rollback")
            raise e
