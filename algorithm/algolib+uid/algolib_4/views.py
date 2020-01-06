#! usr/bin/python3.6

from flask import Blueprint, request, jsonify, g, Response
import json
import os
from instance import config
from utils.dbutils import mysqlpool
from utils.json_helper import DateEncoder
import uuid
import datetime
import pymysql
import pymongo
import subprocess
import time

# 创建增加算法的蓝图
add_algorithm = Blueprint("algorithm", __name__)


# @add_algorithm.route("/add_algorithm/", methods=["POST"])
# def add_alg():
#     """选择算法类型"""
#     conn = mysqlpool.get_conn()
#     with conn.swich_db(config.WOWRKSHEET01) as cursor:
#         all_data = conn.query_all("select * from {}".format(config.TABLENAME2))
#     data_list = []
#
#     for i in all_data:
#         data_info = {
#             "id": i[0],
#             "type_name": i[1]
#         }
#
#         data_list.append(data_info)
#
#     if data_list != []:
#         algorithm_styles = {
#             "code": 1,
#             "data": data_list
#         }
#
#     else:
#         algorithm_styles = {
#             "code": -1,
#             "data": "数据未找到，返回数据失败"
#         }
#     json_data = json.dumps(algorithm_styles)
#     return json_data
@add_algorithm.route("/add_algorithm/", methods=["POST"])
def add_alg():
    """选择算法类型"""
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        if conn.query_all("select * from {}".format(config.TABLENAME2)):
            all_data = conn.query_all("select * from {}".format(config.TABLENAME2))

            return jsonify({
                "code":1,
                "data":all_data
            })
        else:
            return jsonify({
                "code": -1,
                "data": "数据未找到，返回数据失败"
            })


#
# @add_algorithm.route("/upload_file/<id>", methods=["POST", "GET"])
# def upload_files(id):
#     """获取文件"""
#     user_id = str(id)
#
#     f = request.files.getlist("file")
#
#     file_path = r"/algolib_{}".format(user_id)
#
#     BASE_DIR = config.FILE_PATH + file_path
#     # BASE_DIR = r"E:\sjj\jczcxt\uploads" + file_path
#
#     if not os.path.exists(BASE_DIR):
#         os.makedirs(BASE_DIR)
#
#     newdata = ''
#     for i in f:
#         upload_path = os.path.join(BASE_DIR, i.filename)
#         i.save(upload_path)
#
#         with open(upload_path, "r", encoding="utf-8", errors='ignore') as f:
#             file_content = f.read()
#
#         newdata = file_content
#
#     # 返回给前端结果
#     return jsonify({
#         'code': 1,
#         'data': str(newdata)
#     })

@add_algorithm.route("/upload_file/<id>", methods=["POST", "GET"])
def upload_files(id):
    """获取文件"""
    user_id = str(id)
    f = request.files.getlist("file")
    file_path = r"/algolib_{}".format(user_id)
    BASE_DIR = config.FILE_PATH + file_path
    # BASE_DIR = r"E:\sjj\jczcxt\uploads" + file_path
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

    for i in f:
        upload_path = os.path.join(BASE_DIR, i.filename)
        i.save(upload_path)

        if os.path.splitext(upload_path)[-1] == ".py":
            with open(upload_path, "r+", encoding="utf-8") as ff:
                file_content = ff.read()  # py文件
        elif os.path.splitext(upload_path)[-1] == ".txt":
            with open(upload_path, "r+") as ff:
                file_content = ff.read()  # txt文件

    # 返回给前端结果
    return jsonify({
        'code': 1,
        'data': file_content
    })


# http://120.31.140.112:8080/componentManagement//algorithmic/getAnalysisModelList
@add_algorithm.route("/algorithm_model_list/", methods=["POST"])
def algorithm_model_list():
    """算法模型列表"""
    json_data = request.get_json()
    page = int(json_data.get('page')) - 1
    page_size = int(json_data.get('pageSize'))
    uid = g.token.get("id")
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        if conn.query_all( 'select a.algorithmicName,b.* from {TABLE1} as a,{TABLE2} as b where a.id=b.algorithmic_analysis_id and b.uid = {UID} and b.flag = 1 limit {P1},{P2};'.format(
                TABLE1=config.TABLENAME1, TABLE2=config.TABLENAME42, UID=uid, P1=0 + page * page_size,
                P2=20 + page * page_size)):
            res = conn.query_all(
                'select a.algorithmicName,b.* from {TABLE1} as a,{TABLE2} as b where a.id=b.algorithmic_analysis_id and b.uid = {UID} and b.flag = 1 limit {P1},{P2};'.format(
                    TABLE1=config.TABLENAME1, TABLE2=config.TABLENAME42, UID=uid, P1=0 + page * page_size,
                    P2=20 + page * page_size))
            data = {"total": len(res), "page": page + 1, "rows": res}
        else:
            data= {"total": 0, "page": page + 1, "rows": []}
    return Response(json.dumps({"code": 1, "data": data}, cls=DateEncoder), mimetype='application/json')

@add_algorithm.route("/del_model_list/", methods=["POST"])
def del_model_list():
    """算法模型列表删除操作"""
    json_data = request.get_json()
    dellist = json_data.get('ids')
    uid = g.token.get("id")
    try:
        if dellist:
            conn = mysqlpool.get_conn()
            with conn.swich_db(config.WOWRKSHEET01) as cursor:
                conn.update("update {TABLE2} set flag = 0 where id in {DELLIST} and uid = {UID}".format(
                    TABLE2=config.TABLENAME42,
                    DELLIST=dellist, UID=uid))
        return jsonify({"code": 1, "msg": "删除成功"})
    except Exception:
        return jsonify({"code": -1, "msg": "删除失败"})


@add_algorithm.route("/algorithm_list_all/", methods=["POST"])
def algorithm_list_all():
    """获取算法列表"""
    uid = g.token.get("id")
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        res = conn.query_all('select * from {TABLE} where user_id = {UID} and flag=%s'.format(TABLE=config.TABLENAME1, UID=uid),[1])
    return jsonify({"code": 1, "data": res})


@add_algorithm.route("/get_assessment/", methods=["POST"])
def get_assessment():
    """获取评估方法"""
    uid = g.token.get("id")
    json_data = request.get_json()
    algorithm_id = json_data.get('algorithmId')
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        res = conn.query_all(
            'select id,`name`,definition from {TABLE} where uid = {UID} and categorie_id = {CID}'.format(
                TABLE=config.TABLENAME43, UID=uid, CID=algorithm_id))

    return jsonify({"code": 1, "data": res})


@add_algorithm.route("/save_analysis_model/", methods=["POST"])
def save_analysis_model():
    """保存算法模型"""
    uid = g.token.get("id")
    json_data = request.get_json()
    algorithm_id = json_data.get('algorithmId')
    model_name = json_data.get('modelName')
    theme = json_data.get('theme')
    purpose_column = json_data.get('purposeColumn')
    drag_data = json_data.get('dragData')
    source = json_data.get('source')
    create_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = mysqlpool.get_conn()
    the_uuid = uuid.uuid1()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        res = conn.insert_one(
            'insert into {TABLE} values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'.format(TABLE=config.TABLENAME42),
            [the_uuid, uid, algorithm_id, model_name, theme, purpose_column, drag_data, source, create_date,
             create_date, 1])
    if res:
        return jsonify({"code": 1, "data": the_uuid})
    else:
        return jsonify({"code": -1, "data": "操作失败"})


@add_algorithm.route("/get_analysis_result/", methods=["POST"])
def get_analysis_result():
    """查看分析结果"""
    json_data = request.get_json()
    analysis_id = json_data.get('id')
    uid = g.token.get("id")
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        res = conn.query_all(
            'select * from {TABLE} where id = {ID} and uid = {UID} and flag = 1'.format(TABLE=config.TABLENAME42,
                                                                                        ID=analysis_id, UID=uid))
    return jsonify({'code': 1, "data": res})


@add_algorithm.route("/build_algorithm/", methods=["POST"])
def build_algorithm():
    """运行算法模型"""
    json_data = request.get_json()
    # 算法id
    algorithm_id = json_data.get('algorithmId')
    # 评估方法
    assessment_ids = json_data.get('assessmentIds')
    # 表名字段名
    table_and_field = json_data.get('tableName')
    # 目标字段
    targetdb, takgetfield = json_data.get('purposeColumn').split('-', 1)
    temporaryid = uuid.uuid4()
    model_id = uuid.uuid1()
    uid = g.token.get("id")

    cl = table_and_field[targetdb]
    cl.remove(takgetfield)
    table_and_field[targetdb] = cl

    data = {}
    conn = mysqlpool.get_conn()
    with conn.swich_db("%s_db" % uid, cursor=pymysql.cursors.Cursor) as cursor:
        for k, v in table_and_field:
            res1 = conn.query_all("select {FIELD} from {TABLE}".format(FIELD=",".join(v), TABLE=k))
            for i, j in enumerate(v):
                data[j] = [k[i] for k in res1]
        res2 = conn.query_all("select {FIELD} from {TABLE}".format(FIELD=takgetfield, TABLE=targetdb))

        data[takgetfield] = [k[0] for k in res2]

    client = pymongo.MongoClient(host=config.M_HOST, port=config.M_PORT, username=config.M_USER,
                                 password=config.M_PASSWORD)
    collection = client[config.M_DBNAME1][config.M_COLLECTION1]
    collection.insert_one({"id": temporaryid,
                           "data": {"data": data, "mark": "%s+train" % model_id, "evaluate": assessment_ids,
                                    "param": ""}})

    conn = mysqlpool.get_conn()
    with conn.swich_db(config.DBNAME1, cursor=pymysql.cursors.Cursor) as cursor:
        res = conn.query_one("select pythonPath from {} where id = {}".format(config.TABLENAME1, algorithm_id))

    ec = "%s/%s" % (config.ALGORITHM_PATH, res[0])

    cmd = "{PYTHON_PATH} {EC} {ARGS}".format(PYTHON_PATH=config.PYTHON_PATH, EC=ec, ARGS=model_id)
    cmdres = subprocess.run(cmd)
    if cmdres == 0:
        collection_e = client[config.M_DBNAME1][config.M_COLLECTION2]
        res1 = collection_e.find_one({"mark": "%s+train" % model_id})
        return jsonify(
            {"code": 1, "algorithmicModelId": res1['mark'], "data": res1['data'], "evaluate": res1['evaluate']})
    else:
        return jsonify({'code': 1, "data": "请重试"})


# @add_algorithm.route("/get_analysis_result_by_modelid/", methods=["POST"])
# def get_analysis_result_by_modelid():
#     """根据模型id查看分析结果"""
#     uid = g.token.get("id")
#     json_data = request.get_json()
#     model_id = json_data.get('algorithmicModelId')
#     algorithm_id = json_data.get('algorithmId')
#     conn = mysqlpool.get_conn()
#     with conn.swich_db(config.WOWRKSHEET01) as cursor:
#         conn.query_all('select * from {TABLE}') e



@add_algorithm.route("/addAlgorithmicManagement/", methods=["POST"])
def addAlgorithmicManagement():
    """算法管理--添加算法"""
    json_data = request.get_json()
    algorithmType= json_data["type"]
    #  算法文件
    algorithmFile= json_data["algorithmFile"]
    algorithmName= json_data["name"]
    dateType = json_data["dataType"]
    # 允许字段数
    fieldCount= json_data["fieldCount"]
    # 算法用途简介
    description= json_data["description"]
    # 环境配置 资源名 resourceName 版本 version
    resourceName= json_data["resourceName"]
    version= json_data["version"]
    flag=1
    userid= g.token["id"]
    # 算法文件存储地址
    serverpath= "/usr/local/algorithm/algolib"
    data_type= "/".join(dateType)

    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            algorithmid= conn.insert_one("insert into {} (user_id,algorithmicName,definition,category,data_type,dimensions,pythonPath,resource_name,version_num,flag) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(
                config.TABLENAME1),[int(userid),algorithmName,description,algorithmType,data_type,fieldCount,algorithmFile,resourceName,version,flag])

        return jsonify({
            "code": 1,
            "data": "算法管理添加成功"
        })
    except Exception as e:
        raise e


@add_algorithm.route("/delAlgorithmicManagement/", methods=["POST"])
def delAlgorithmicManagement():
    """算法管理--删除算法"""
    json_data = request.get_json()
    ids= json_data["ids"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            for i in ids:
                conn.update("update {} set flag=%s where id=%s and flag=%s".format(config.TABLENAME1),[0,i,1])

        return jsonify({
            "code": 1,
            "data": "删除算法管理成功"
        })
    except Exception as e:
        raise e
