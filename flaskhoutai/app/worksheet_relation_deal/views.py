#! usr/bin/python


from flask import Blueprint, request, jsonify,g
import pymysql
import json
from instance import config
import datetime
import os, base64
from utils.dbutils import mysqlpool
from utils.dbutils import redis
import hashlib

# 创建关联工作表之后内容的相关操作蓝图
operation_worksheet = Blueprint("operation_worksheet", __name__)

@operation_worksheet.route("/return_all_worksheets/", methods=["POST"])
def return_all_worksheets():
    """返回工作表"""
    group_id = request.get_json()["id"]
    uid= g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db("%s_db"%uid) as cursor:
            if group_id == 0:
                obj_list = conn.query_all(
                    "select id, worksheet_name, worksheet_name_cn from {}".format(config.ME2_TABLENAME2))
                return jsonify({
                    "code": 1,
                    "data": obj_list
                })
            else:
                obj_list = conn.query_all(
                    "select id, worksheet_name, worksheet_name_cn from {} where groupid={}".format(
                        config.ME2_TABLENAME2, group_id))
                return jsonify({
                    "code": 1,
                    "data": obj_list
                })
    except Exception as e:
        return jsonify({
            "code": -1,
            "msg": str(e)
        })


@operation_worksheet.route("/return_relation_worksheets/", methods=["POST"])
def return_relation_worksheets():
    """返回表，关联表，字段"""
    json_data = request.get_json()
    file_name = json_data["worksheet_name"]
    uid= g.token["id"]
    try:
        content_list = []
        conn = mysqlpool.get_conn()
        with conn.swich_db("%s_db"%uid) as cursor:
            if file_name == "":
                return jsonify({
                    "code": 1,
                    "data": content_list

                })
            if conn.query_one("select * from association_table_relation where begin_table ='{}' or end_table='{}'".
                                      format(file_name, file_name)):
                if conn.query_one(
                        "select end_table from association_table_relation where begin_table='{}'".format(file_name)):
                    obj_en = conn.query_all(
                        "select end_table from association_table_relation where begin_table='{}'".format(file_name))
                else:
                    obj_en = []
                if conn.query_all(
                        "select begin_table from association_table_relation where end_table='{}'".format(file_name)):
                    obj_be = conn.query_all(
                        "select begin_table from association_table_relation where end_table='{}'".format(file_name))
                else:
                    obj_be = []
                for i in obj_be:
                    obj_en.append(i)
                obj_en.insert(0, {"worksheet_name": file_name})
                for j in obj_en:
                    value = list(j.values())[0]
                    cn_name__ = conn.query_all(
                        "select file_name_cn from association_table where file_name={}".format(repr(value)))
                    cn_name = cn_name__[0]
                    d = {list(j.values())[0]: list(cn_name.values())[0]}
                    table_name = value + "_" + "cn"
                    obj = conn.query_all("select * from {}".format(table_name))
                    obj.append(d)
                    content_list.append(obj)
                return jsonify({
                    "code": 1,
                    "data": content_list

                })
            else:
                cn_name__ = conn.query_all(
                    "select worksheet_name_cn from worksheet_relation where worksheet_name={}".format(repr(file_name)))
                cn_name = cn_name__[0]
                d = {'{}'.format(file_name): list(cn_name.values())[0]}
                table_name = file_name + "_" + "cn"
                obj = conn.query_all("select * from {}".format(table_name))
                obj.append(d)
                content_list.append(obj)
                return jsonify({
                    "code": 1,
                    "data": content_list
                })
    except Exception as e:
        return jsonify({
            "code": -1,
            "msg": repr(e)
        })


@operation_worksheet.route("/return_relation_contents/", methods=["POST"])
def return_relation_contents():
    """关联表之间的字段内容"""
    uid= g.token["id"]
    try:
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
        conn = mysqlpool.get_conn()
        with conn.swich_db("%s_db"%uid) as cursor:
            # 查询关联表 是否存在关联 多张表
            if conn.query_one("select * from association_table_relation where begin_table ='{}' or end_table='{}'".
                                      format(schema, schema)) and len(list(dict_name.keys())) > 1:
                if list(dict_name.keys())[0] == schema:
                    # 分别提取所有维度值和度量值
                    relation_x_columnName = []
                    relation_y_columnName = []
                    return_dict = {}
                    for z in list(dict_name):
                        for z1 in dict_name[z]:
                            new_columnName = z + "-" + z1["columnName"]
                            return_dict[z1["columnName"]] = new_columnName
                            if z1["isX"] == True:
                                zz = z + "." + z1["columnName"]
                                relation_x_columnName.append(zz)
                            else:
                                zz = z + "." + z1["columnName"]
                                relation_y_columnName.append(zz)
                            all_relation_table = conn.query_all(
                                "select * from association_table_relation where begin_table='{}' and end_table='{}' or begin_table='{}' and end_table='{}'".format(
                                    schema, z, z, schema))
                            if not all_relation_table:
                                continue

                            #  确定相关联的所有表
                            for k in all_relation_table:
                                begin_table = k["begin_table"]
                                end_table = k["end_table"]
                                begin_table_cn = begin_table + "_" + "cn"
                                end_table_cn = end_table + "_" + "cn"
                                line = k["line"]
                                associated_field_01 = k["associated_field_01"]
                                associated_field_02 = k["associated_field_02"]
                                table_name_list01 = conn.query_all(
                                    "select prime_name, cn_name from {} where prime_name='{}' or cn_name='{}'".format(
                                        begin_table_cn,
                                        associated_field_01,
                                        associated_field_01))
                                table_name = table_name_list01[0]
                                prime_name = table_name["prime_name"]
                                cn_name = table_name["cn_name"]
                                if conn.query_one(
                                        "select count(*) from information_schema.columns where table_name = '{}' and column_name = '{}'".format(
                                            begin_table, prime_name)):
                                    associated_field_01 = cn_name
                                else:
                                    associated_field_01 = prime_name

                                table_name_list02 = conn.query_all(
                                    "select prime_name, cn_name from {} where prime_name='{}' or cn_name='{}'".format(
                                        end_table_cn,
                                        associated_field_02,
                                        associated_field_02))
                                table_name_02 = table_name_list02[0]
                                prime_name_02 = table_name_02["prime_name"]
                                cn_name_02 = table_name_02["cn_name"]
                                if conn.query_one(
                                        "select count(*) from information_schema.columns where table_name = '{}' and column_name = '{}'".format(
                                            end_table, prime_name_02)):
                                    associated_field_02 = cn_name_02
                                else:
                                    associated_field_02 = prime_name_02

                                if begin_table == schema:
                                    data_table = end_table
                                else:
                                    data_table = begin_table

                    sql_x_columnName = ""
                    # 遍历维度 组成一个字符串  默认字段总和计算方式
                    for x in relation_x_columnName:
                        if relation_x_columnName.index(x) == len(relation_x_columnName) - 1:
                            sql_x_columnName = sql_x_columnName + x
                        else:
                            sql_x_columnName = sql_x_columnName + x + ","

                    relation_all = []
                    relation_all_list = []
                    for y in relation_y_columnName:
                        caculation_dict = {}  # 存各个字段的计算方式
                        # 判断是否有传 字段计算方式 拼接到SQL语句  默认是sum
                        if "caculation" in dict(json_data).keys():
                            caculation = json_data["caculation"]
                            for i in caculation:
                                d_columnName = i["columnName"]
                                d_formula = i["formula"]
                                if d_formula == "":
                                    caculation_dict[d_columnName] = "sum"
                                else:
                                    caculation_dict[d_columnName] = d_formula

                        # 判断是否传筛选条件
                        if "chartObj" in dict(json_data).keys():
                            chartObj = json_data["chartObj"]
                            sql_charObjStr = ""
                            if chartObj == "chartObjStr":
                                fieldValue = ""
                                sql_charObjStr = " "
                            else:
                                fieldName = chartObj["fieldName"]
                                fieldValue = chartObj["fieldValue"]
                                table_name_obj = chartObj["tableName"]
                                sql_charObjStr = ", " + fieldName + " HAVING " + table_name_obj + "." + fieldName + " =" + "\"" + fieldValue + "\""
                        else:
                            sql_charObjStr = ""
                        # 判断前端是否传 维度、度量
                        if "dimension" in dict(json_data).keys() or "measure" in dict(json_data).keys():
                            sql_is_where = " where "
                        else:
                            sql_is_where = ""

                        # 前端传 维度值默认也传度量值
                        if "measure" in dict(json_data).keys() and len(
                                json_data["measure"][0]["return_fields"]) >= 1 and \
                                json_data["measure"][0]["return_fields"][0]["condition"] != -1:
                            dimension_and_measure = " and "
                        else:
                            dimension_and_measure = ""

                        # 判断前端是否传 维度筛选条件
                        if "dimension" in dict(json_data).keys():
                            dimension_where = ""
                            for i in json_data["dimension"]:
                                where_sql = "("
                                dimension_field = i["field"]
                                dimension_return_fields = i["return_fields"]
                                dimension_tablename = i["tablename"]
                                dimension_haveNull = i["haveNull"]
                                if len(dimension_return_fields) >= 1:
                                    for x in dimension_return_fields:
                                        if dimension_return_fields.index(x) == len(dimension_return_fields) - 1:
                                            where_sql = where_sql + dimension_tablename + "." + dimension_field + " = " + "\"" + str(
                                                x) + "\"" + " )"
                                        else:
                                            where_sql = where_sql + dimension_tablename + "." + dimension_field + " = " + "\"" + str(
                                                x) + "\"" + " or "
                                else:
                                    if dimension_where.endswith(" and "):
                                        dimension_where = dimension_where[:-5]
                                    where_sql = ""
                                if dimension_haveNull == 0:
                                    where_sql = where_sql + " and "
                                elif dimension_haveNull == 1 and len(dimension_return_fields) == 0:
                                    if json_data["dimension"].index(i) == len(json_data["dimension"]) - 1:
                                        where_sql = where_sql + "  {dimension_tablename}.{dimension_field} is not null ".format(
                                            dimension_tablename=dimension_tablename, dimension_field=dimension_field)
                                    else:
                                        where_sql = where_sql + "  {dimension_tablename}.{dimension_field} is not null ".format(
                                            dimension_tablename=dimension_tablename,
                                            dimension_field=dimension_field) + " and "
                                else:
                                    if json_data["dimension"].index(i) == len(json_data["dimension"]) - 1:
                                        where_sql = where_sql + " and {dimension_tablename}.{dimension_field} is not null ".format(
                                            dimension_tablename=dimension_tablename, dimension_field=dimension_field)
                                    else:
                                        where_sql = where_sql + " and {dimension_tablename}.{dimension_field} is not null ".format(
                                            dimension_tablename=dimension_tablename,
                                            dimension_field=dimension_field) + " and "
                                dimension_where = dimension_where + where_sql
                        else:
                            dimension_where = ""
                        if dimension_where.endswith(" and "):
                            dimension_where = dimension_where[:-5]

                        # 判断前端是否传 度量筛选条件
                        if "measure" in dict(json_data).keys():
                            #  key:1 大于   key:2 大于等于   key3: 小于   key4: 小于等于    key5: 等于    key6: 不等于
                            sign_of_operation = {"1": ">", "2": ">=", "3": "<", "4": "<=", "5": "=", "6": "!="}
                            measure_where = ""
                            for j in json_data["measure"]:
                                where_sql = "("
                                measure_field = j["field"]
                                measure_return_fields = j["return_fields"]
                                measure_tablename = j["tablename"]
                                if len(measure_return_fields) >= 1:
                                    for a in measure_return_fields:
                                        if a["condition"] == -1:
                                            where_sql = ""
                                        else:
                                            measure_condition = a["condition"]
                                            measure_conditionValue = a["conditionValue"]
                                            if measure_return_fields.index(a) == len(measure_return_fields) - 1:
                                                where_sql = where_sql + measure_tablename + "." + measure_field + \
                                                            sign_of_operation[str(measure_condition)] + str(
                                                    measure_conditionValue) + " )"
                                            else:
                                                where_sql = where_sql + measure_tablename + "." + measure_field + \
                                                            sign_of_operation[str(measure_condition)] + str(
                                                    measure_conditionValue) + " and "
                                else:
                                    where_sql = ""
                                    measure_where = measure_where[:-5]
                                if json_data["measure"].index(j) == len(json_data["measure"]) - 1:
                                    measure_where = measure_where + where_sql
                                else:
                                    measure_where = measure_where + where_sql + " and "
                            if measure_where.endswith(" and "):
                                measure_where = measure_where[:-5]
                        else:
                            measure_where = ""

                        sql_x_columnName1 = sql_x_columnName
                        sql_x_columnName2 = sql_x_columnName
                        # 遍历所有相关联的表 拼接SQL
                        for i in all_relation_table:
                            begin_table = i["begin_table"]
                            end_table = i["end_table"]
                            begin_table_cn = begin_table + "_" + "cn"
                            end_table_cn = end_table + "_" + "cn"
                            line = i["line"]
                            associated_field_01 = i["associated_field_01"]
                            associated_field_02 = i["associated_field_02"]
                            str_y = "\'" + y.split(".")[1] + "\'"
                            formula = caculation_dict[y.split(".")[1]]
                            if "HAVING " in sql_charObjStr:
                                is_group_by = " group by "
                                if formula == "":
                                    formula = "sum"
                                    sql_x_columnName2 = sql_x_columnName

                            if line == "全部联接":
                                content_list = conn.query_all(
                                    "select {sql_x_columnName1}, {formula}( DISTINCTROW {y}) as {str_y}  from {begin_table} LEFT JOIN {end_table}  on {begin_table}.{associated_field_01}={end_table}.{associated_field_02} {sql_is_where} {dimension_where}{dimension_and_measure} {measure_where} group by {sql_x_columnName2}{sql_charObjStr} UNION select {sql_x_columnName1}, {formula}( DISTINCTROW {y}) as {str_y} from {begin_table} RIGHT JOIN {end_table}  on {begin_table}.{associated_field_01}={end_table}.{associated_field_02} {sql_is_where} {dimension_where}{dimension_and_measure} {measure_where} group by {sql_x_columnName2}{sql_charObjStr}".format(
                                        sql_x_columnName=sql_x_columnName, y=y, schema=schema, formula=formula,
                                        begin_table=begin_table,
                                        sql_x_columnName1=sql_x_columnName1, end_table=end_table, str_y=str_y,
                                        sql_x_columnName2=sql_x_columnName2, associated_field_01=associated_field_01,
                                        associated_field_02=associated_field_02,
                                        sql_charObjStr=sql_charObjStr, dimension_where=dimension_where,
                                        measure_where=measure_where,
                                        sql_is_where=sql_is_where,
                                        dimension_and_measure=dimension_and_measure))

                            elif line == "左侧联接":
                                content_list = conn.query_all(
                                    "select {sql_x_columnName1}, {formula}( DISTINCTROW {y}) as {str_y}   from {begin_table} LEFT JOIN {end_table}  on {begin_table}.{associated_field_01}={end_table}.{associated_field_02} {sql_is_where} {dimension_where}{dimension_and_measure} {measure_where} group by {sql_x_columnName2}{sql_charObjStr}".format(
                                        sql_x_columnName=sql_x_columnName, y=y, schema=schema, formula=formula,
                                        begin_table=begin_table,
                                        sql_x_columnName1=sql_x_columnName1, end_table=end_table, str_y=str_y,
                                        sql_x_columnName2=sql_x_columnName2, associated_field_01=associated_field_01,
                                        associated_field_02=associated_field_02,
                                        sql_charObjStr=sql_charObjStr, dimension_where=dimension_where,
                                        measure_where=measure_where,
                                        sql_is_where=sql_is_where,
                                        dimension_and_measure=dimension_and_measure))

                            elif line == "右侧联接":
                                content_list = conn.query_all(
                                    "select {sql_x_columnName1}, {formula}( DISTINCTROW {y}) as {str_y}   from {begin_table} RIGHT JOIN {end_table}  on {begin_table}.{associated_field_01}={end_table}.{associated_field_02} {sql_is_where} {dimension_where}{dimension_and_measure} {measure_where} group by {sql_x_columnName2}{sql_charObjStr}".format(
                                        sql_x_columnName=sql_x_columnName, y=y, schema=schema, formula=formula,
                                        begin_table=begin_table,
                                        sql_x_columnName1=sql_x_columnName1, end_table=end_table, str_y=str_y,
                                        sql_x_columnName2=sql_x_columnName2, associated_field_01=associated_field_01,
                                        associated_field_02=associated_field_02,
                                        sql_charObjStr=sql_charObjStr, dimension_where=dimension_where,
                                        measure_where=measure_where,
                                        sql_is_where=sql_is_where,
                                        dimension_and_measure=dimension_and_measure))

                            elif line == "内部联接":
                                content_list = conn.query_all(
                                    "select {sql_x_columnName1}, {formula}( DISTINCTROW {y}) as {str_y}   from {begin_table} INNER JOIN {end_table}  on {begin_table}.{associated_field_01}={end_table}.{associated_field_02} {sql_is_where} {dimension_where}{dimension_and_measure} {measure_where} group by {sql_x_columnName2}{sql_charObjStr}".format(
                                        sql_x_columnName=sql_x_columnName, y=y, schema=schema, formula=formula,
                                        begin_table=begin_table,
                                        sql_x_columnName1=sql_x_columnName1, end_table=end_table, str_y=str_y,
                                        sql_x_columnName2=sql_x_columnName2, associated_field_01=associated_field_01,
                                        associated_field_02=associated_field_02,
                                        sql_charObjStr=sql_charObjStr, dimension_where=dimension_where,
                                        measure_where=measure_where,
                                        sql_is_where=sql_is_where,
                                        dimension_and_measure=dimension_and_measure))

                            if content_list:
                                for i in content_list:
                                    dic = {}
                                    for key, value in i.items():
                                        new_key = return_dict[key]
                                        dic[new_key] = value
                                    relation_all_list.append(dic)
                            else:
                                return jsonify({
                                    "code": -1,
                                    "msg": "无数据"
                                })

                    y_columnName_len = len(relation_y_columnName)
                    relation_all = []
                    if y_columnName_len == 1:
                        relation_all = relation_all_list
                    else:
                        for z in relation_x_columnName:
                            t = z.replace(".", "-")
                        tl = [i[t] for i in relation_all_list]
                        pre_data = list(set(tl))
                        pre_data.sort(key=tl.index)
                        for i in pre_data:
                            pre_dict = {}
                            for j in filter(lambda x: x[t] == i, relation_all_list):
                                pre_dict.update(j)
                            relation_all.append(pre_dict)
                    if "sort" in dict(json_data).keys():
                        sort_c = json_data["sort"]
                        sort_columnName = return_dict[sort_c[0]["columnName"]]
                        sort_sortMode = sort_c[0]["sortMode"]
                        # 判断是否为降序
                        if sort_sortMode == "desOrder":
                            sort_sortMode = "DESC"  # 降序
                            i = 0
                            while i < len(relation_all):
                                if relation_all[i][sort_columnName] == None or relation_all[i][sort_columnName] == "":
                                    relation_all.pop(i)
                                elif isinstance(relation_all[i][sort_columnName], str) and relation_all[i][
                                    sort_columnName].isdigit():
                                    relation_all[i][sort_columnName] = float(relation_all[i][sort_columnName])
                                elif isinstance(relation_all[i][sort_columnName], str) and relation_all[i][
                                    sort_columnName].count(".") == 1 and relation_all[i][sort_columnName].split(".")[
                                    0].isdigit() and relation_all[i][sort_columnName].split(".")[1].isdigit():
                                    relation_all[i][sort_columnName] = float(relation_all[i][sort_columnName])
                                else:
                                    i += 1
                            relation_all.sort(key=lambda x: x[sort_columnName], reverse=True)

                        elif sort_sortMode == "asOrder":
                            sort_sortMode = "ASC"  # 升序
                            i = 0
                            while i < len(relation_all):
                                if relation_all[i][sort_columnName] == None or relation_all[i][sort_columnName] == "":
                                    relation_all.pop(i)
                                elif isinstance(relation_all[i][sort_columnName], str) and relation_all[i][
                                    sort_columnName].isdigit():
                                    relation_all[i][sort_columnName] = float(relation_all[i][sort_columnName])
                                elif isinstance(relation_all[i][sort_columnName], str) and relation_all[i][
                                    sort_columnName].count(".") == 1 and relation_all[i][sort_columnName].split(".")[
                                    0].isdigit() and relation_all[i][sort_columnName].split(".")[1].isdigit():
                                    relation_all[i][sort_columnName] = float(relation_all[i][sort_columnName])
                                else:
                                    i += 1
                            relation_all.sort(key=lambda x: x[sort_columnName], reverse=False)
                        else:
                            relation_all = relation_all
                    return jsonify({
                        "code": 1,
                        "data": relation_all
                    })

            else:
                # -------------------进入无关联数据---------------------
                x_columnName = []
                y_columnName = []
                relation_all_list = []
                for x in dict_name[schema]:
                    if x["isX"]:
                        x_columnName.append(x["columnName"])
                    else:
                        y_columnName.append(x["columnName"])
                sql_x_columnName = ""
                # 遍历维度 组成一个字符串  默认字段总和计算方式
                for x in x_columnName:
                    if x_columnName.index(x) == len(x_columnName) - 1:
                        sql_x_columnName = sql_x_columnName + x
                    else:
                        sql_x_columnName = sql_x_columnName + x + ","
                for y in y_columnName:
                    caculation_dict = {}  # 存各个字段的计算方式
                    # 判断是否有传 字段计算方式 拼接到SQL语句  默认是sum
                    if "caculation" in dict(json_data).keys():
                        caculation = json_data["caculation"]
                        for i in caculation:
                            d_columnName = i["columnName"]
                            d_formula = i["formula"]
                            if d_formula == "":
                                caculation_dict[d_columnName] = "sum"
                            else:
                                caculation_dict[d_columnName] = d_formula
                    if y in caculation_dict.keys():
                        formula = caculation_dict[y]
                    else:
                        formula = "sum"
                    # 判断是否传筛选条件
                    if "chartObj" in dict(json_data).keys():
                        chartObj = json_data["chartObj"]
                        sql_charObjStr = ""
                        if chartObj == "chartObjStr":
                            fieldValue = ""
                            sql_charObjStr = " "
                        else:
                            fieldName = chartObj["fieldName"]
                            fieldValue = chartObj["fieldValue"]
                            table_name_obj = chartObj["tableName"]
                            sql_charObjStr = ", " + fieldName + " HAVING " + table_name_obj + "." + fieldName + " =" + "\"" + fieldValue + "\""
                    else:
                        sql_charObjStr = ""
                    # 判断前端是否传 维度、度量
                    if "dimension" in dict(json_data).keys() or "measure" in dict(json_data).keys():
                        sql_is_where = " where "
                    else:
                        sql_is_where = ""

                    # 前端传 维度值默认也传度量值
                    if "measure" in dict(json_data).keys() and len(json_data["measure"][0]["return_fields"]) >= 1 and \
                            json_data["measure"][0]["return_fields"][0]["condition"] != -1:
                        dimension_and_measure = " and "
                    else:
                        dimension_and_measure = ""

                    # 判断前端是否传 维度筛选条件
                    if "dimension" in dict(json_data).keys():
                        #    haveNull: 0    有非空值    haveNull: 1  非空值
                        # 遍历 筛选条件  拼接 where SQL语句
                        dimension_where = ""
                        for i in json_data["dimension"]:
                            where_sql = "("
                            dimension_field = i["field"]
                            dimension_return_fields = i["return_fields"]
                            dimension_tablename = i["tablename"]
                            dimension_haveNull = i["haveNull"]

                            if len(dimension_return_fields) >= 1:
                                for x in dimension_return_fields:
                                    if dimension_return_fields.index(x) == len(dimension_return_fields) - 1:
                                        where_sql = where_sql + dimension_tablename + "." + dimension_field + " = " + "\"" + str(
                                            x) + "\"" + " )"
                                    else:
                                        where_sql = where_sql + dimension_tablename + "." + dimension_field + " = " + "\"" + str(
                                            x) + "\"" + " or "
                            else:
                                if dimension_where.endswith(" and "):
                                    dimension_where = dimension_where[:-5]
                                where_sql = ""

                            if dimension_haveNull == 0:
                                where_sql = where_sql + " and "
                            elif dimension_haveNull == 1 and len(dimension_return_fields) == 0:
                                if json_data["dimension"].index(i) == len(json_data["dimension"]) - 1:
                                    where_sql = where_sql + "  {dimension_tablename}.{dimension_field} is not null ".format(
                                        dimension_tablename=dimension_tablename, dimension_field=dimension_field)
                                else:
                                    where_sql = where_sql + "  {dimension_tablename}.{dimension_field} is not null ".format(
                                        dimension_tablename=dimension_tablename,
                                        dimension_field=dimension_field) + " and "
                            else:
                                if json_data["dimension"].index(i) == len(json_data["dimension"]) - 1:
                                    where_sql = where_sql + " and {dimension_tablename}.{dimension_field} is not null ".format(
                                        dimension_tablename=dimension_tablename, dimension_field=dimension_field)
                                else:
                                    where_sql = where_sql + " and {dimension_tablename}.{dimension_field} is not null ".format(
                                        dimension_tablename=dimension_tablename,
                                        dimension_field=dimension_field) + " and "
                            dimension_where = dimension_where + where_sql
                    else:
                        dimension_where = ""
                    if dimension_where.endswith(" and "):
                        dimension_where = dimension_where[:-5]
                    # 判断前端是否传 度量筛选条件
                    if "measure" in dict(json_data).keys():
                        #  key:1 大于   key:2 大于等于   key3: 小于   key4: 小于等于    key5: 等于    key6: 不等于
                        sign_of_operation = {"1": ">", "2": ">=", "3": "<", "4": "<=", "5": "=", "6": "!="}
                        measure_where = ""
                        for j in json_data["measure"]:
                            where_sql = "("
                            measure_field = j["field"]
                            measure_return_fields = j["return_fields"]
                            measure_tablename = j["tablename"]
                            if len(measure_return_fields) >= 1:
                                for a in measure_return_fields:
                                    if a["condition"] == -1:
                                        where_sql = ""
                                    else:
                                        measure_condition = a["condition"]
                                        measure_conditionValue = a["conditionValue"]
                                        if measure_return_fields.index(a) == len(measure_return_fields) - 1:
                                            where_sql = where_sql + measure_tablename + "." + measure_field + \
                                                        sign_of_operation[str(measure_condition)] + str(
                                                measure_conditionValue) + " )"
                                        else:
                                            where_sql = where_sql + measure_tablename + "." + measure_field + \
                                                        sign_of_operation[str(measure_condition)] + str(
                                                measure_conditionValue) + " and "
                            else:
                                where_sql = ""
                                measure_where = measure_where[:-5]
                            if json_data["measure"].index(j) == len(json_data["measure"]) - 1:
                                measure_where = measure_where + where_sql
                            else:
                                measure_where = measure_where + where_sql + " and "
                        if measure_where.endswith(" and "):
                            measure_where = measure_where[:-5]
                    else:
                        measure_where = ""

                    sql_x_columnName1 = sql_x_columnName
                    sql_x_columnName2 = sql_x_columnName

                    # 判断查询表 是否有 维度字段上是否有重复数据
                    is_group_by = " group by "
                    is_data = conn.query_all(
                        "select {sql_x_columnName1}  from {schema} {sql_is_where} {dimension_where}{dimension_and_measure} {measure_where} group by {sql_x_columnName2} having count(*)>1".format(
                            sql_x_columnName=sql_x_columnName, y=y, schema=schema, formula=formula,
                            sql_x_columnName1=sql_x_columnName1, sql_x_columnName2=sql_x_columnName2,
                            sql_charObjStr=sql_charObjStr, dimension_where=dimension_where,
                            measure_where=measure_where,
                            sql_is_where=sql_is_where,
                            dimension_and_measure=dimension_and_measure))

                    if is_data:
                        is_group_by = is_group_by
                        formula = formula
                    else:
                        sql_x_columnName2 = ""
                        is_group_by = ""
                        formula = ""
                    if not formula:
                        y1 = "`" + y + "`"
                    else:
                        y1 = "(" + "`" + y + "`" + ")"
                    if "HAVING " in sql_charObjStr:
                        is_group_by = " group by "
                        if formula == "":
                            formula = "sum"
                            sql_x_columnName2 = sql_x_columnName

                    relation_list = conn.query_all(
                        "select {sql_x_columnName1}, {formula}({y1})  from {schema} {sql_is_where} {dimension_where}{dimension_and_measure} {measure_where} {is_group_by} {sql_x_columnName2}{sql_charObjStr}".format(
                            sql_x_columnName=sql_x_columnName, y1=y1, schema=schema, formula=formula,
                            is_group_by=is_group_by, sql_x_columnName1=sql_x_columnName1,
                            sql_x_columnName2=sql_x_columnName2,
                            sql_charObjStr=sql_charObjStr, dimension_where=dimension_where, measure_where=measure_where,
                            sql_is_where=sql_is_where,
                            dimension_and_measure=dimension_and_measure))

                    if relation_list:
                        for i in relation_list:
                            dic = {}
                            for key, value in i.items():
                                if key in x_columnName:
                                    new_key = schema + "-" + key
                                    dic[new_key] = value
                                else:
                                    new_key = schema + "-" + y
                                    dic[new_key] = value
                            relation_all_list.append(dic)

                y_columnName_len = len(y_columnName)
                relation_all = []
                if y_columnName_len == 1:
                    relation_all = relation_all_list
                else:
                    for z in x_columnName:
                        t = schema + "-" + z
                    tl = [i[t] for i in relation_all_list]
                    pre_data = list(set(tl))
                    pre_data.sort(key=tl.index)
                    for i in pre_data:
                        pre_dict = {}
                        for j in filter(lambda x: x[t] == i, relation_all_list):
                            pre_dict.update(j)
                        relation_all.append(pre_dict)
                if "sort" in dict(json_data).keys():
                    sort_c = json_data["sort"]
                    sort_columnName = schema + "-" + sort_c[0]["columnName"]
                    sort_sortMode = sort_c[0]["sortMode"]
                    # 判断是否为降序
                    if sort_sortMode == "desOrder":
                        sort_sortMode = "DESC"
                        i = 0
                        while i < len(relation_all):
                            if relation_all[i][sort_columnName] == None or relation_all[i][sort_columnName] == "":
                                relation_all.pop(i)
                            elif isinstance(relation_all[i][sort_columnName], str) and relation_all[i][
                                sort_columnName].isdigit():
                                relation_all[i][sort_columnName] = float(relation_all[i][sort_columnName])
                            elif isinstance(relation_all[i][sort_columnName], str) and relation_all[i][
                                sort_columnName].count(".") == 1 and relation_all[i][sort_columnName].split(".")[
                                0].isdigit() and relation_all[i][sort_columnName].split(".")[1].isdigit():
                                relation_all[i][sort_columnName] = float(relation_all[i][sort_columnName])
                            else:
                                i += 1
                        relation_all.sort(key=lambda x: x[sort_columnName], reverse=True)

                    elif sort_sortMode == "asOrder":
                        sort_sortMode = "ASC"
                        i = 0
                        while i < len(relation_all):
                            if relation_all[i][sort_columnName] == None or relation_all[i][sort_columnName] == "":
                                relation_all.pop(i)
                            elif isinstance(relation_all[i][sort_columnName], str) and relation_all[i][
                                sort_columnName].isdigit():
                                relation_all[i][sort_columnName] = float(relation_all[i][sort_columnName])
                            elif isinstance(relation_all[i][sort_columnName], str) and relation_all[i][
                                sort_columnName].count(".") == 1 and relation_all[i][sort_columnName].split(".")[
                                0].isdigit() and relation_all[i][sort_columnName].split(".")[1].isdigit():
                                relation_all[i][sort_columnName] = float(relation_all[i][sort_columnName])
                            else:
                                i += 1
                        relation_all.sort(key=lambda x: x[sort_columnName], reverse=False)
                    else:
                        # 默认排序 不用排序 sort_sortMode= defaultOrder
                        relation_all = relation_all
                return jsonify({
                    "code": 1,
                    "data": relation_all,

                })
    except Exception as e:
        raise e


@operation_worksheet.route("/save_component_db/", methods=["POST"])
def save_component_db():
    """保存修改组件到数据库"""
    json_data = request.get_json()
    token = json_data["token"]
    uid= g.token["id"]
    jsonstr = json_data["jsonstr"]
    thumbnail = json_data["thumbnail"].split(",")[-1]
    imgdata = base64.b64decode(thumbnail)
    now_time = datetime.datetime.now()
    time_01 = now_time.strftime("%Y%m%d%H%M%S")
    time_02 = now_time.strftime("%Y-%m-%d %H:%M:%S")
    path01 = config.SERVERCHART01 + time_01 + ".jpg"
    path = config.SERVERCHARTPATH + time_01 + ".jpg"
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
    precentValueArr = str(json_data["precentValueArr"])
    # 预警Arr
    yujingArr = str(json_data["yujingArr"])
    cacula = str(json_data["cacula"])
    selectedPartStatus = str(json_data["selectedPartStatus"])
    showData = str(json_data["showData"])
    # 组件绑定预案参数
    reserve_param = str(json_data["reserve_param"])

    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01, cursor=pymysql.cursors.Cursor) as cursor:
            if "id" in dict(json_data).keys():
                id = json_data["id"]
                conn.update(
                    "update test_tubiao_goucheng  set uid=%s,jsonstr=%s,thumbnail=%s,theme=%s,main_title=%s,subtitle=%s,`type`=%s ,other_opt=%s,chartDataSourceId=%s,mSchema=%s,columnMap=%s,selectArr=%s,selectVArr=%s,editDate=%s,precentValueArr=%s, yujingArr=%s, cacula=%s,selectedPartStatus=%s, showData=%s,reserve_param=%s where id=%s",
                    [uid, jsonstr, path, theme, main_title, subtitle, stype, other_opt, chartDataSourceId, mSchema,
                     columnMap, selectArr, selectVArr, time_02, precentValueArr, yujingArr, cacula, selectedPartStatus,
                     showData, reserve_param, id])
                return jsonify({
                    "code": 1,
                    "data": "保存成功"
                })
            else:
                h1 = hashlib.md5()
                h1.update(str(time_01).encode(encoding="utf-8"))
                data_id = h1.hexdigest()
                result = conn.insert_one(
                    'insert into test_tubiao_goucheng(id,uid,jsonstr,thumbnail,theme,main_title,subtitle,`type` ,other_opt,chartDataSourceId,mSchema,columnMap,selectArr,selectVArr,precentValueArr, yujingArr, cacula,selectedPartStatus,showData,reserve_param,createDate,editDate) VALUES (%s,%s,%s,%s, %s,%s,%s, %s,%s,%s,%s,%s,%s, %s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (data_id, uid, jsonstr, path, theme, main_title, subtitle, stype, other_opt, chartDataSourceId,
                     mSchema, columnMap, selectArr, selectVArr, precentValueArr, yujingArr, cacula, selectedPartStatus,
                     showData, reserve_param, time_02, time_02))
        return jsonify({
            "code": 1,
            "msg": data_id
        })
    except Exception as e:
        raise e


@operation_worksheet.route("/return_component_con/", methods=["POST"])
def return_component_con():
    """返回组件中的内容"""
    component_id = request.get_json()["id"]
    if len(component_id) == 33:
        component_id = component_id[:-1]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01, cursor=pymysql.cursors.Cursor) as cursor:
            component_con = conn.query_one(
                "select other_opt, selectArr, selectVArr,`type`,precentValueArr, yujingArr,cacula, selectedPartStatus,reserve_param,showData,columnMap,jsonstr from test_tubiao_goucheng where id=%s",
                component_id)
        if component_con:
            if component_con[4]:
                return_precentValueArr = {"precentValueArr": str(component_con[4].replace("'", '"'))}
            else:
                return_precentValueArr = {"precentValueArr": []}
            if component_con[5]:
                return_yujingArr = {"yujingArr": str(component_con[5].replace("'", '"'))}
            else:
                return_yujingArr = {"yujingArr": []}
            if component_con[6]:
                return_cacula = {"cacula": str(component_con[6].replace("'", '"'))}
            else:
                return_cacula = {"cacula": []}
            if component_con[7]:
                return_selectedPartStatus = {"selectedPartStatus": str(component_con[7].replace("'", '"'))}
            else:
                return_selectedPartStatus = {"selectedPartStatus": []}
            if component_con[-3]:
                return_reserve_param = {"reserve_param": str(component_con[-3].replace("'", '"'))}
            else:
                return_reserve_param = {"reserve_param": []}
            return jsonify({
                "code": 1,
                "data": [{"other_opt": str(component_con[0]).replace("'", '"')},
                         {"selectArr": str(component_con[1]).replace("'", '"')},
                         {"selectVArr": str(component_con[2]).replace("'", '"')},
                         {"type": str(component_con[3]).replace("'", '"')},
                         return_precentValueArr,
                         return_yujingArr,
                         return_cacula,
                         return_selectedPartStatus,

                         {"columnMap": str(component_con[-2]).replace("'", '"')},
                         {"showData": str(component_con[-3]).replace("'", '"')},
                         {"reserve_param": str(component_con[-4]).replace("'", '"')},
                         return_reserve_param,
                         {"jsonstr": str(component_con[-1])}
                         ]
            })
        else:
            return jsonify({
                "code": 1,
                "data": [{"other_opt": None},
                         {"selectArr": None},
                         {"selectVArr": None},
                         {"type": None},
                         {"precentValueArr": None},
                         {"yujingArr": None},
                         {"cacula": None},
                         {"selectedPartStatus": None},
                         {"columnMap": None},
                         {"showData": None},
                         {"reserve_id": None},
                         {"reserve_param": None},
                         {"jsonstr": None}

                         ]
            })

    except Exception as e:
        raise e


@operation_worksheet.route("/tablefields_colation/", methods=["POST"])
def tablefields_colation():
    """表字段内容筛选"""
    json_data = request.get_json()
    uid= g.token["id"]
    tablefields = json_data["tablefields"]
    try:
        return_fields = []
        conn = mysqlpool.get_conn()
        with conn.swich_db("%s_db"%uid, cursor=pymysql.cursors.Cursor) as cursor:
            for i in tablefields:
                tablename = i["tablename"]
                field = i["field"]
                type = i["type"]
                tablefields_lists = conn.query_all(
                    "select {field} from {tablename} where {field} is not null".format(field=field,
                                                                                       tablename=tablename))
                tablefields_lists = list(set(tablefields_lists))
                fields_lists = []
                for j in tablefields_lists:
                    fields_lists.append(j[0])
                field_dict = {}
                field_dict["tablename"] = tablename
                field_dict["field"] = field
                field_dict["return_fields"] = fields_lists
                field_dict["type"] = type
                return_fields.append(field_dict)
        return jsonify({
            "code": 1,
            "data": return_fields

        })
    except Exception as e:
        raise e
