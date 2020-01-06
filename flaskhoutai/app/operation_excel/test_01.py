#! usr/bin/python3.6


from flask import Blueprint, request, jsonify
import pymysql
import xlrd
import os
import pymongo
import json
from copy import deepcopy
from instance import config
import time
from app.connection_db import mycursor, mydb



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


@operation_table.route("/get_excel/", methods=["POST", "GET"])
def operation_tab():
    """
    上传excel表

    """
    if request.method == "POST":

        f = request.files["file"]

        file_path = r"/tables_info"

        # BASE_DIR = config.FILE_PATH + file_path
        BASE_DIR = r"E:\sjj\jczcxt\uploads" + file_path

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
        table_name_list = []
        for sheet1 in sheet_names:
            table_name_list.append(sheet1)
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
            # return read_data
            dict_data.append(read_data)
        all_info = []

        mycursor.execute('use {DATABASE}'.format(DATABASE=config.DBNAME2))
        for i in table_name_list:
            mycursor.execute("INSERT IGNORE INTO {}(excel_list_name) values('{}')".format(config.ME2_TABLENAME3, i))

        for data in dict_data:
            list01 = []
            data_info = data[1]

            for i in range(1, len(data)):
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

        # contents = collection.find()
        # # print(contents)
        # for k in all_info:
        #     # print(k)
        #     for n in contents:
        #         # global n
        #         cp = deepcopy(n)
        #         print(cp["data"])
        #     cp["data"].append(k)
        #     print(cp["data"])
        #     print("---" * 50)
        # excel_data = {
        #     "code": 1,
        #     "data": cp["data"]
        # }
        #
        # collection.drop()
        # collection.insert(dict(excel_data))

        for i in all_info:
            print(all_info)
            print("---"*50)
            i.pop()
            table_name = i[0]["table_name"]
            # print(table_name)
            del i[0]
            for j in i:
                del j["table_name"]
                COLstr = ''  # 列的字段
                ROWstr = ''  # 行字段
                ColumnStyle = ' VARCHAR(255)'

                for key in j.keys():

                    COLstr = COLstr + ' ' + key + ColumnStyle + ','
                    ROWstr = (ROWstr + '"%s"' + ',') % (j[key])

                # mycursor.execute('use {DATABASE}'.format(DATABASE=config.DBNAME2))
                mycursor.execute("CREATE TABLE if NOT EXISTS {table_name}({values})".format(
                    table_name=table_name, values=COLstr[:-1]))

                mycursor.execute("INSERT INTO {} VALUES ({})".format(table_name, ROWstr[:-1]))

                mydb.commit()

        return jsonify({
            'code': 1,
            'data': all_info
        })

    else:
        return jsonify({
            'code': -1,
            'data': '请求方式错误'
        })


@operation_table.route("/get_excel_sheets/", methods=["POST", "GET"])
def operation_sheet():
    """
    获取excel文件中的sheet
    """
    if request.method == "POST":
        mycursor.execute('use {DATABASE}'.format(DATABASE=config.DBNAME2))
        # mycursor.execute("SELECT table_name FROM INFORMATION_SCHEMA.TABLES where table_schema = '{}'".format(config.ME2_TABLENAME2))
        mycursor.execute('show tables')
        table_name = mycursor.fetchall()
        table_list = []
        for i in table_name:
            tb_name = {
                "table_name": i[0]
            }
            table_list.append(tb_name)
        # print(table_list)
        # print("---"*50)
        sheet_names = {
                "code": 1,
                # "sheet_id": sheet_id,
                "data": table_list
            }

        return jsonify(sheet_names)
    else:
        return jsonify({
            "code": -1,
            "data": "请求格式错误"
        })


@operation_table.route("/get_excel_contents/", methods=["POST", "GET"])
def operation_tab_info():
    """
    获取excel文件中sheet内容

    """
    if request.method == "POST":
        table_name = request.get_json()["table_name"]
        mycursor.execute('use {DATABASE}'.format(DATABASE=config.DBNAME2))
        mycursor.execute("select * from %s" % table_name)
        obj = mycursor.fetchall()
        return jsonify({"code": 1, "data": obj})

    else:
        return jsonify({
            "code": -1,
            "data": "查询方式错误"
        })


@operation_table.route("/del_excel/", methods=["POST", "GET"])
def deal_excel():
    """删除表"""
    if request.method == "POST":
        table_name = request.get_json()["table_name"]
        mycursor.execute('use {DATABASE}'.format(DATABASE=config.DBNAME2))
        mycursor.execute("drop table %s" % table_name)

        mydb.commit()

        return jsonify({
                "code": 1,
                "data": "删除表成功"
            })
    else:
        return jsonify({
            "code": 1,
            "data": "删除表失败"
        })


@operation_table.route("/update_excel/", methods=["POST", "GET"])
def update_excel():
    """修改表内容"""
    if request.method == "POST":
        table_name = request.get_json()["table_name"]
        table_data = request.get_json()["data"]
        mycursor.execute('use {DATABASE}'.format(DATABASE=config.DBNAME2))
        mycursor.execute("update {} set {}".format(table_name, table_data))

        mydb.commit()
        return jsonify({
                "code": 1,
                "data": "修改成功"
            })
    else:
        return jsonify({
            "code": 1,
            "data": "修改失败"
        })


@operation_table.route("/get_excel_types/", methods=["POST", "GET"])
def get_excel_types():
    """ 获取表的字段状态  排序状态  格式  类型"""
    if request.method == "POST":
        contents = collection.find()
        for x in contents:
            json_data = request.get_json()
            table_id = {"table_id": int(json_data["id"])}
            for each in x["data"]:
                if each[-1] == table_id:
                    print(each)
                    # collection.find({"data" :{$type: "table_id"}})

                    print("---"*50)

    else:
        return jsonify({
            "code": 1,
            "data": "获取数据失败"
        })





