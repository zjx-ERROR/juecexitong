#! usr/bin/python
from flask import Blueprint, request, jsonify
import pymysql
import xlrd
import os
import pymongo
from copy import deepcopy
from instance import config
import time
from utils.dbutils import mysqlpool
from flask import g
from datetime import datetime
from utils.token_utils import TokenMaker

"""
连接mongodb数据库
"""
client = pymongo.MongoClient(
    host=config.M_HOST,
    port=config.M_PORT
)

db_auth = client[config.M_DB]
db_auth.authenticate(config.M_USER, config.M_PASSWORD)
db = client[config.M_DBNAME]
collection = db[config.M_TABLENAME]

# 创建读取excel内容，存在mongodb数据库中相关操作的蓝图
operation_table = Blueprint("operation_table", __name__)


@operation_table.route("/get_excel/", methods=["POST"])
def operation_tab():
    """
    上传excel表
    """
    if request.method == "POST":
        f = request.files["file"]
        file_path = r"/tables_info"
        BASE_DIR = config.FILE_PATH + file_path

        if not os.path.exists(BASE_DIR):
            os.makedirs(BASE_DIR)
        upload_path = os.path.join(BASE_DIR, f.filename)
        f.save(upload_path)
        ALLOWED_EXTENSIONS = set(['xls', 'csv', 'xlsx'])

        if upload_path.rsplit(".", 1)[1] not in ALLOWED_EXTENSIONS:
            return jsonify({'code': -1, 'data': '文件格式不允许'})
        data = xlrd.open_workbook(upload_path)
        if upload_path.split('.')[1] != 'xlsx':
            data = xlrd.open_workbook(upload_path, formatting_info=True)

        sheet_names = data.sheet_names()
        dict_data = []
        for sheet1 in sheet_names:
            sheet = data.sheet_by_name(sheet1)
            sheets = ["sheet_name", sheet1]
            # 获取列数
            r_num = sheet.nrows
            # 获取行数
            c_num = sheet.ncols
            merge = sheet.merged_cells
            read_data = [sheets]
            for r in range(r_num):
                li = []
                for c in range(c_num):
                    # 读取每个单元格里的数据，合并单元格只有单元格内的第一行第一列有数据，其余空间都为空
                    cell_value = sheet.row_values(r)[c]
                    # 判断空数据是否在合并单元格的坐标中，如果在就把数据填充进去
                    if cell_value is None or cell_value == '':
                        for (rlow, rhigh, clow, chigh) in merge:
                            if rlow <= r < rhigh:
                                if clow <= c < chigh:
                                    cell_value = sheet.cell_value(rlow, clow)
                    li.append(cell_value)
                read_data.append(li)
            dict_data.append(read_data)

        all_info = []
        for data in dict_data:
            if len(data) > 1:
                list01 = []
                data_info = data[1]
            for i in range(2, len(data)):
                list_01 = {}
                for j in range(0, len(data[1])):
                    dict_info = {
                        "table_name": data[0][1],
                        "{}".format(data_info[j]): data[i][j]
                    }
                    list_01.update(dict_info)
                list01.append(list_01)
            all_info.append(list01)

        k = []
        for j in range(1, len(sheet_names) + 1):
            table_id = {"table_id": j + int(time.time())}
            k.append(table_id)
        for n, m in enumerate(all_info):
            m.append(k[n])
        uid = g.token.get("id")
        ident = TokenMaker().generate_token(uid, uid)
        excel_data = {
            "code": 1,
            "data": all_info,
            "ident": ident,
            "time2": datetime.utcnow()
        }
        collection.delete_one({"ident": ident})
        collection.insert(dict(excel_data))
        return jsonify({
            'code': 1,
            'data': '上传成功'
        })
    else:
        return jsonify({
            'code': -1,
            'msg': '请求方式错误'
        })


@operation_table.route("/get_excel_sheets/", methods=["POST"])
def operation_sheet():
    """
    获取excel文件中的sheet
    """
    if request.method == "POST":
        uid = g.token.get("id")
        ident = TokenMaker().generate_token(uid, uid)
        for x in collection.find({"ident": ident}):
            sheet_list = []
            for y in x["data"]:
                sheet_name = {
                    "table_id": int(y[-1]["table_id"]),
                    "table_name": y[0]["table_name"]
                }
                sheet_list.append(sheet_name)
            return jsonify({"code": 1, "data": sheet_list})
    return jsonify({
        "code": 1,
        "msg": []
    })


@operation_table.route("/get_excel_contents/", methods=["POST"])
def operation_tab_info():
    """
    获取excel文件中sheet内容
    """
    if request.method == "POST":
        uid = g.token.get("id")
        ident = TokenMaker().generate_token(uid, uid)
        json_data = request.get_json()
        current_page_contents = json_data.get("current_page_contents")
        if current_page_contents == None:
            current_page_contents = 0
        del_row = json_data.get("del_row")
        table_id = json_data.get("id")
        contents = collection.find({"ident": ident})
        for i in contents:
            contents = i

        # 删除某行data
        if del_row != None:
            p_control = 0
            for dr in del_row:
                dr -= p_control
                for j in contents["data"]:
                    if j[-1]["table_id"] == table_id:
                        j.pop(dr)
                p_control += 1
            collection.update({"ident": ident}, contents)
        for c in contents["data"]:
            for j in c:
                if "table_id" in j:
                    if j["table_id"] == table_id:
                        pre_data = c[:-1]

        if "status" in pre_data[-1]:
            pre_data.pop()
        data = pre_data[0 + 20 * current_page_contents: 20 + 20 * current_page_contents]
        return jsonify({
            "code": 1,
            "data": data,
            "total": len(pre_data),
            "page": current_page_contents
        })
    else:
        return jsonify({
            "code": -1,
            "msg": "查询方式错误"
        })


@operation_table.route("/del_excel/", methods=["POST"])
def deal_excel():
    """删除表"""
    if request.method == "POST":
        uid = g.token.get("id")
        ident = TokenMaker().generate_token(uid, uid)
        contents = collection.find({"ident": ident})
        for x in contents:
            cp = deepcopy(x)
            json_data = request.get_json()
            deal_data = {"table_id": json_data["id"]}
            for each in cp["data"]:
                if each[-1] == deal_data:
                    each.clear()
                    cp["data"].remove([])
            collection.update(x, {"$set": cp}, upsert=True)
            return jsonify({
                "code": 1,
                "data": "删除表成功"
            })
    else:
        return jsonify({
            "code": 1,
            "msg": "删除表失败"
        })


@operation_table.route("/update_excel/", methods=["POST"])
def update_excel():
    """修改表"""
    if request.method == "POST":
        uid = g.token.get("id")
        ident = TokenMaker().generate_token(uid, uid)
        contents = collection.find({"ident": ident})
        json_data = request.get_json()
        table_id = int(json_data.get("id"))
        table_data = json_data.get("data")
        page = json_data.get("page")
        for x in contents:
            cp = deepcopy(x)
            for each in cp["data"]:
                if each[-1]["table_id"] == table_id:
                    sile = -2 if "status" in each[-2] else -1
                    change_data = each[:sile]
                    last_data = each[sile:]
                    change_data[0 + 20 * page:20 + 20 * page] = table_data
                    for ld in last_data:
                        change_data.append(ld)
                    cp["data"].remove(each)
                    cp["data"].append(change_data)
            cp["time2"] = datetime.utcnow()

            collection.update(x, {"$set": cp}, upsert=True)
            return jsonify({
                "code": 1,
                "data": "修改成功"
            })
    else:
        return jsonify({
            "code": 1,
            "msg": "修改失败"
        })


@operation_table.route("/get_status/", methods=["POST"])
def get_status():
    """ 获取表原始状态"""
    if request.method == "POST":
        uid = g.token.get("id")
        ident = TokenMaker().generate_token(uid, uid)
        contents = collection.find({"ident": ident})
        json_data = request.get_json()
        table_id = {"table_id": int(json_data["id"])}
        table_dict = {"flag": 0, "status": "yes"}

        for x in contents:
            y = deepcopy(x)
            for each in y["data"]:
                if each[-1] == table_id:
                    list_key = []
                    for key in each[0].keys():
                        list_key.append(key)
                    del list_key[0]
                    for i in range(0, len(list_key) - 1):
                        k = []
                        for j in list_key:
                            data_status = {
                                "prime_name": j,
                                "cn_name": j
                            }
                            k.append(data_status)

                        table_list = []
                        for n in k:
                            n.update(table_dict)
                            table_list.append(n)

                        excel_data = {
                            "status": table_list
                        }

                        if list(each[-2].keys())[0] == "status":
                            return jsonify({
                                "code": 1,
                                "data": each[-2]["status"]
                            })
                        else:
                            each.insert(-1, excel_data)

                            collection.update(x, {"$set": y}, upsert=True)
                            return jsonify({
                                "code": 1,
                                "data": table_list
                            })
        return jsonify({"code": 1, "data": None})
    else:
        return jsonify({
            "code": -1,
            "msg": "查询方式错误"
        })


@operation_table.route("/update_status/", methods=["POST"])
def update_status():
    """修改表的状态保存到mysql"""
    uid = g.token.get("id")
    ident = TokenMaker().generate_token(uid, uid)
    json_data = request.get_json()
    table_id = {"table_id": json_data["id"]}
    table_name = json_data["table_name"] + "_" + "cn"
    contents = collection.find({"ident": ident})
    for x in contents:
        y = deepcopy(x)
        json_data = request.get_json()
        status_data = {"status": json_data["data"]}
        table_id = {"table_id": int(json_data["id"])}
        for each in y["data"]:
            if each[-1] == table_id:
                if list(each[-2].keys())[0] == "status":
                    del each[-2]
                    each.insert(-1, status_data)

                collection.update(x, {"$set": y}, upsert=True)
    conn = mysqlpool.get_conn()
    with conn.swich_db("%s_db" % uid) as cursor:
        conn.drop("drop table if EXISTS {}".format(table_name))
        for i in json_data["data"]:
            COLstr = ''  # 列的字段
            ROWstr = ''  # 行字段
            ColumnStyle = ' VARCHAR(255)'
            for key in i.keys():
                COLstr = COLstr + ' ' + key + ColumnStyle + ','
                ROWstr = (ROWstr + '"%s"' + ',') % (i[key])
            try:
                conn.create("CREATE TABLE %s (%s)" % (table_name, COLstr[:-1]))
                conn.show("INSERT INTO %s VALUES (%s)" % (table_name, ROWstr[:-1]))
            except Exception as e:
                conn.query_one("SELECT * FROM  %s" % table_name)
                conn.show("INSERT INTO %s VALUES (%s)" % (table_name, ROWstr[:-1]))
    return jsonify({
        "code": 1,
        "data": "修改成功"
    })


@operation_table.route("/get_excel_to_db/", methods=["POST", "GET"])
def get_excel_to_db():
    """ 保存工作表到MySQL"""
    uid = g.token.get("id")
    ident = TokenMaker().generate_token(uid, uid)
    contents = collection.find({"ident": ident})
    json_data = request.get_json()
    data = json_data.get("data")
    conn = mysqlpool.get_conn()
    with conn.swich_db("%s_db" % uid, cursor=pymysql.cursors.Cursor) as cursor:
        for c in contents:
            for i, n in zip(c["data"], data):
                table_name = i[0]["table_name"]
                worksheet_name = n["worksheet_name"]
                groupid = n["group_id"]
                types = n["types"]
                worksheet_name_cn = n["worksheet_name_cn"]
                origin_type_id = n["origin_type_id"]
                conn.delete(
                    "delete from {} where worksheet_name= {}".format(config.ME2_TABLENAME2, repr(worksheet_name)))
                conn.show(
                    "INSERT INTO {}(worksheet_name,types,groupid,worksheet_name_cn,origin_type_id) VALUES ('{}','{}','{}','{}','{}')".
                        format(config.ME2_TABLENAME2, worksheet_name, types, groupid, worksheet_name_cn,
                               origin_type_id))
                if "table_id" in i[-1]:
                    del i[-1]
                if "status" in i[-1]:
                    del i[-1]
                conn.drop("drop table if EXISTS {}".format(table_name))
                for j in i:
                    del j["table_name"]
                    COLstr = ''  # 列的字段
                    ROWstr = ''  # 行字段
                    ColumnStyle = ' VARCHAR(255)'
                    for key in j.keys():
                        nkey = key.replace(' ', '')
                        COLstr = COLstr + ' ' + nkey + ColumnStyle + ','
                        ROWstr = (ROWstr + '"%s"' + ',') % (j[key])
                    if not conn.show('show tables like %s', table_name):
                        conn.create("CREATE TABLE %s (%s)" % (table_name, COLstr[:-1]))
                    conn.show("INSERT INTO %s VALUES (%s)" % (table_name, ROWstr[:-1]))

    return jsonify({
        "code": 1,
        "data": "保存成功"
    })


@operation_table.route("/return_group_table/", methods=["POST", "GET"])
def return_group_table():
    """返回分类列表和分类中包含的所有表"""
    uid= g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db("%s_db"%uid) as cursor:
            table_list_ra = conn.query_all("select type_name from {}".format(config.ME2_TABLENAME1))
            obj_list = conn.query_all(
                "select wr.worksheet_name,wr.worksheet_name_cn,wc.type_name from {tableA} as wr left join {tableB} as wc on wr.groupid=wc.groupid".format(
                    tableA= config.ME2_TABLENAME2, tableB=config.ME2_TABLENAME1))
            table_list = []
            for i in table_list_ra:
                list_data = []
                for j in obj_list:
                    if j["type_name"] == i["type_name"]:
                        if conn.query_all(
                                "select * from association_table where file_name='{}'".format(j["worksheet_name"])):
                            status_dict = {"status": "true"}
                            j.update(status_dict)
                        else:
                            other_status = {"status": "false"}
                            j.update(other_status)
                        list_data.append(j)
                data = [i, {"table_name": list_data}]
                table_list.append(data)
    except Exception as e:
        raise  e
    else:
        return jsonify({
            "code": 1,
            "data": table_list
        })


@operation_table.route("/return_excel_field/", methods=["POST", "GET"])
def return_excel_field():
    """返回表的内容和状态"""
    table_name = request.get_json()["worksheet_name"]
    uid= g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db("%s_db"%uid) as cursor:
            table_list = []
            each_name = table_name + "_" + "cn"
            content_list = conn.query_all("select * from {}".format(table_name))
            table_contents = {"contents": content_list}
            obj_list = conn.query_all("select * from {}".format(each_name))
            bjs = conn.query_all(
                "select data_type from information_schema.columns where table_name={}".format(repr(table_name)))
            for n, m in enumerate(obj_list):
                m.update(bjs[n])
            status = {"status": obj_list}
            table_contents.update(status)
            table_list.append(table_contents)
        return jsonify({
            "code": 1,
            "data": table_list
        })

    except Exception as e:
        return jsonify({
            "code": -1,
            "msg": "数据库出错"
        })


@operation_table.route("/add_table_relation/", methods=["POST", "GET"])
def add_table_relation():
    """增加表到关联的列表中"""
    json_data = request.get_json()["data"]
    uid= g.token["id"]
    conn = mysqlpool.get_conn()
    with conn.swich_db("%s_db"%uid) as cursor:
        for each_name in json_data:
            tab_name = each_name["worksheet_name"]
            tab_name_cn = each_name["worksheet_name_cn"]
            if conn.query_one("select * from association_table where file_name ='{}'".format(tab_name)):
                conn.delete("delete from association_table_relation where file_name='{}'".format(tab_name))
            conn.show('INSERT INTO association_table(file_name, file_name_cn) VALUES ({},{})'.format(repr(tab_name),
                                                                                                     repr(tab_name_cn)))
    return jsonify({
        "code": 1,
        "data": "添加成功"
    })


@operation_table.route("/select_table_relation/", methods=["POST", "GET"])
def select_table_relation():
    """查询关联的列表"""
    json_data = request.get_json()
    table_relations = []
    uid= g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db("%s_db"%uid) as cursor:
            two_table_relation = conn.query_all("select * from association_table_relation")
            status_relation = []
            if two_table_relation:
                for i in two_table_relation:
                    status_relation.append(i)
            the_all = [{"status_relation": status_relation}]
            table_relations.append(the_all)
            content_list = conn.query_all("select * from association_table")
            table_relations.append(content_list)
        return jsonify({
            "code": 1,
            "data": table_relations
        })
    except Exception as e:

        return jsonify({
            "code": -1,
            "msg": "操作失败"
        })


@operation_table.route("/add_and_update_relation/", methods=["POST", "GET"])
def add_and_update_relation():
    """增加和修改两关联表关系到MySQL数据库"""
    table_data = request.get_json()["data"]
    begin_table = table_data["begin_table"]
    end_table = table_data["end_table"]
    line = table_data["line"]
    associated_field_01 = table_data["associated_field_01"]
    associated_field_02 = table_data["associated_field_02"]
    uid= g.token["id"]
    conn = mysqlpool.get_conn()
    with conn.swich_db("%s_db"%uid) as cursor:
        if conn.query_one(
                "select * from association_table_relation where begin_table='{}' and end_table='{}'".format(begin_table,
                                                                                                            end_table)):
            conn.update(
                "update association_table_relation set line='{}',associated_field_01='{}',associated_field_02='{}' where begin_table='{}' and end_table='{}'".
                    format(line, associated_field_01, associated_field_02, begin_table, end_table))

        else:
            conn.show(
                "insert into association_table_relation(begin_table, end_table, line, associated_field_01, associated_field_02) values('{}','{}','{}','{}','{}')".
                    format(begin_table, end_table, line, associated_field_01, associated_field_02))

    return jsonify({
        "code": 1,
        "data": "修改成功"
    })


@operation_table.route("/del_two_table_relation/", methods=["POST", "GET"])
def del_two_table_relation():
    """删除两关联表的关联关系"""
    try:
        table_data_id = request.get_json()["id"]
        uid= g.token["id"]
        conn = mysqlpool.get_conn()
        with conn.swich_db("%s_db"%uid) as cursor:
            conn.query_one("delete from association_table_relation where id='{}'".format(table_data_id))
        return jsonify({
            "code": 1,
            "data": "删除成功"
        })

    except Exception as e:
        return jsonify({
            "code": -1,
            "msg": "删除失败"
        })


@operation_table.route("/del_table_relation/", methods=["POST", "GET"])
def del_table_relation():
    """删除关联表的列表"""
    worksheet_name = request.get_json().get("worksheet_name")
    uid= g.token["id"]
    if worksheet_name:
        try:
            conn = mysqlpool.get_conn()
            with conn.swich_db("%s_db"%uid) as cursor:
                if conn.query_one(
                        "select * from association_table_relation where begin_table='{}' or end_table='{}'".format(
                            worksheet_name, worksheet_name)):
                    return jsonify({
                        "code": -1,
                        "msg": "表还有关联，删除失败"
                    })
                else:
                    conn.delete("DELETE from association_table where file_name={}".format(repr(worksheet_name)))
            return jsonify({
                "code": 1,
                "data": "删除成功"
            })

        except Exception as e:
            return jsonify({
                "code": -1,
                "msg": "操作失败"
            })


@operation_table.route("/return_two_field/", methods=["POST", "GET"])
def return_two_field():
    """返回两个表的字段和状态"""
    table_name = request.get_json()["data"]
    table_list = []
    uid= g.token["id"]
    conn = mysqlpool.get_conn()
    with conn.swich_db("%s_db"%uid) as cursor:
        for each in table_name:
            each_name = each["worksheet_name"] + "_" + "cn"
            obj_list = conn.query_all("select * from {}".format(each_name))
            table_list.append(obj_list)
    return jsonify({
        "code": 1,
        "data": table_list
    })


@operation_table.route("/return_two_field_contents/", methods=["POST", "GET"])
def return_two_field_contents():
    """返回关联后两个表的字段状态和内容"""
    if request.method == "POST":
        table_data = request.get_json()
        begin_table = table_data["begin_table"]
        end_table = table_data["end_table"]
        begin_table_cn = begin_table + "_" + "cn"
        end_table_cn = end_table + "_" + "cn"
        line = table_data["line"]
        id = table_data["id"]
        uid= g.token["id"]
        conn = mysqlpool.get_conn()
        with conn.swich_db("%s_db"%uid) as cursor:
            relation_data = conn.query_all(
                "select associated_field_01,associated_field_02 from association_table_relation where id={}".format(
                    id))[0]
            associated_field_01 = relation_data["associated_field_01"]
            associated_field_02 = relation_data["associated_field_02"]
            table_name = \
                conn.query_all(
                    "select prime_name, cn_name from {} where prime_name='{}' or cn_name='{}'".format(begin_table_cn,
                                                                                                      associated_field_01,
                                                                                                      associated_field_01))[0]

            prime_name = table_name["prime_name"]
            cn_name = table_name["cn_name"]
            if conn.query_one(
                    "select count(*) from information_schema.columns where table_name = '{}' and column_name = '{}'".format(
                        begin_table, prime_name)):
                associated_field_01 = cn_name
            else:
                associated_field_01 = prime_name
            table_name_02 = \
                conn.query_all(
                    "select prime_name, cn_name from {} where prime_name='{}' or cn_name='{}'".format(end_table_cn,
                                                                                                      associated_field_02,
                                                                                                      associated_field_02))[0]

            prime_name_02 = table_name_02["prime_name"]
            cn_name_02 = table_name_02["cn_name"]
            if conn.query_all(
                    "select count(*) from information_schema.columns where table_name = '{}' and column_name = '{}'".format(
                        end_table, prime_name_02)):
                associated_field_02 = cn_name_02
            else:
                associated_field_02 = prime_name_02
            if line == "全部联接":
                content_list = conn.query_all("SELECT * from {} as a LEFT JOIN {} as b on a.`{}`=b.`{}` UNION "
                                              "SELECT * from {} as a RIGHT JOIN {} as b on a.`{}`=b.`{}`".
                                              format(begin_table, end_table, associated_field_01, associated_field_02,
                                                     begin_table, end_table, associated_field_01, associated_field_02))
                table_contents = {"contents": content_list}
                obj_list_01 = conn.query_all("select * from {}".format(begin_table_cn))
                obj_list_02 = conn.query_all("select * from {}".format(end_table_cn))
                obj_list_01.extend(obj_list_02)
                status = {"status": obj_list_01}
                return jsonify({
                    "code": 1,
                    "data": [table_contents, status]
                })

            elif line == "左侧联接":
                content_list = conn.query_all(
                    "select * from {} as a LEFT JOIN {} as b on a.`{}`=b.`{}`".format(begin_table, end_table,
                                                                                      associated_field_01,
                                                                                      associated_field_02))
                table_contents = {"contents": content_list}
                obj_list_01 = conn.query_all("select * from {}".format(begin_table_cn))
                obj_list_02 = conn.query_all("select * from {}".format(end_table_cn))
                obj_list_01.extend(obj_list_02)
                status = {"status": obj_list_01}
                return jsonify({
                    "code": 1,
                    "data": [table_contents, status]
                })

            elif line == "右侧联接":
                content_list = conn.query_all("select * from {} as a RIGHT JOIN {} as b on a.`{}`=b.`{}`".format(
                    begin_table, end_table, associated_field_01, associated_field_02))
                table_contents = {"contents": content_list}
                obj_list_01 = conn.query_all("select * from {}".format(begin_table_cn))
                obj_list_02 = conn.query_all("select * from {}".format(end_table_cn))
                obj_list_01.extend(obj_list_02)
                status = {"status": obj_list_01}
                return jsonify({
                    "code": 1,
                    "data": [table_contents, status]
                })

            elif line == "内部联接":
                content_list = conn.query_all("select * from {} as a INNER JOIN {} as b on a.`{}`=b.`{}`".format(
                    begin_table, end_table, associated_field_01, associated_field_02))
                table_contents = {"contents": content_list}
                obj_list_01 = conn.query_all("select * from {}".format(begin_table_cn))
                obj_list_02 = conn.query_all("select * from {}".format(end_table_cn))
                obj_list_01.extend(obj_list_02)
                status = {"status": obj_list_01}
                return jsonify({
                    "code": 1,
                    "data": [table_contents, status]
                })

            else:
                return jsonify({
                    "code": -1,
                    "data": "联接错误"
                })

    else:
        return jsonify({
            "code": -1,
            "msg": "操作失败"
        })
