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
import random


# 创建增加算法的蓝图
add_algorithm = Blueprint("algorithm", __name__)




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


@add_algorithm.route("/upload_file/<id>", methods=["POST", "GET"])
def upload_files(id):
    """获取文件"""
    user_id = g.token["id"]
    f = request.files.getlist("file")
    file_path = r"/algolib_{}".format(user_id)
    BASE_DIR = config.FILE_PATH + file_path

    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
    for i in f:
        upload_path = os.path.join(BASE_DIR, i.filename)
        i.save(upload_path)
        params = {"errors": "ignore"}
        if i.mimetype != "text/plain":
            params["encoding"] = "utf-8"
        # 通过 mimetype 类型判断 是否要加encoding  (文件类型暂时两种 txt / py)
        with open(upload_path, "r", **params) as f:
            file_content = f.read()

    return jsonify({
        'code': 1,
        'data': file_content
    })

# http://120.31.140.112:8080/componentManagement//algorithmic/getAnalysisModelList
@add_algorithm.route("/algorithm_model_list/", methods=["POST"])
def algorithm_model_list():
    """算法模型列表"""
    json_data = request.get_json()
    page = json_data["page"]
    page_size = json_data["pageSize"]
    uid = g.token.get("id")

    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        return_list = conn.query_all(
            'select c.*,d.categoryName from (select a.algorithmicName,b.* from {TABLE1} as a,{TABLE2} as b where a.id=b.algorithmic_analysis_id and b.uid = {UID} and b.flag = 1 limit {LU},{LL}) c left join {TABLE3} d on c.theme=d.id'.format(
                TABLE1=config.TABLENAME1, TABLE2=config.TABLENAME42, TABLE3=config.TABLENAME23, UID=uid,
                LU=(page - 1) * page_size, LL=page_size))
        if return_list:
            count = len(return_list)
            data = {"total": count, "page": page, "rows": return_list}
            return Response(json.dumps({"code": 1, "data": data}, cls=DateEncoder), mimetype='application/json')
        else:
            return jsonify({
                "code": 1,
                "data": {
                    "page": 1,
                    "total": 0,
                    "rows": []
                }
            })

@add_algorithm.route("/del_model_list/", methods=["POST"])
def del_model_list():
    """算法模型列表删除操作"""
    json_data = request.get_json()
    dellist = json_data.get('ids')

    uid = g.token.get("id")
    try:
        if dellist:
            conn = mysqlpool.get_conn()
            print("sql====>","update {TABLE2} set flag = 0 where id in {DELLIST} and uid = '{UID}'".format(
                    TABLE2=config.TABLENAME42,
                    DELLIST=tuple(dellist) if len(dellist) > 1 else '(\''+dellist[0]+'\')', UID=uid))
            with conn.swich_db(config.WOWRKSHEET01) as cursor:
                conn.update("update {TABLE2} set flag = 0 where id in {DELLIST} and uid = '{UID}'".format(
                    TABLE2=config.TABLENAME42,
                    DELLIST=tuple(dellist) if len(dellist) > 1 else '(\''+dellist[0]+'\')', UID=uid))
        return jsonify({"code": 1, "msg": "删除成功"})
    except Exception:
        return jsonify({"code": -1, "msg": "删除失败"})




@add_algorithm.route("/algorithm_list_all/", methods=["POST"])
def algorithm_list_all():
    """获取算法列表"""
    uid = g.token.get("id")
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        res = conn.query_all(
            'select a.*,b.type_name from {TABLE} a left join {TABLE1} b on a.category=b.id where user_id = {UID} and flag=%s'.format(TABLE=config.TABLENAME1,TABLE1=config.TABLENAME2, UID=uid), [1])
    return jsonify({"code": 1, "data": res})


#  前端代码修改后 后端代码  多加了 page  pageSize 两参数
# @add_algorithm.route("/algorithm_list_all/", methods=["POST"])
# def algorithm_list_all():
#     """获取算法列表"""
#     # page: 1, pageSize: 10 缺少参数 修改前端接口  返回page: 1  rows: [] total: 0
#     json_data = request.get_json()
#     page = json_data["page"]
#     page_size = json_data["pageSize"]
#     uid = g.token.get("id")
#
#     try:
#         conn = mysqlpool.get_conn()
#         with conn.swich_db(config.WOWRKSHEET01) as cursor:
#             if conn.query_all('select * from {TABLE} where user_id = {UID} and flag=%s'.format(TABLE=config.TABLENAME1, UID=uid),[1]):
#                 return_list = conn.query_all('select * from {TABLE} where user_id = {UID} and flag=%s'.format(TABLE=config.TABLENAME1, UID=uid),[1])
#                 count = len(return_list)
#                 pages = count // page_size if count % page_size == 0 else count // page_size + 1
#                 if page_size <= count and page == 1:
#                     return_list=conn.query_all('select * from {TABLE} where user_id = {UID} and flag=%s limit %s'.format(TABLE=config.TABLENAME1, UID=uid),[1,page_size])
#                 elif page_size > count and page == 1:
#                     return_list = return_list
#                 elif count > page_size and 1 < page <= pages:
#                     return_list=conn.query_all('select * from {TABLE} where user_id = {UID} and flag=%s limit %s,%s'.format(TABLE=config.TABLENAME1, UID=uid),[1,(page - 1) * page_size, page_size])
#
#                 data = {"total": count, "page": page, "rows": return_list}
#                 return Response(json.dumps({"code": 1, "data": data}, cls=DateEncoder), mimetype='application/json')
#             else:
#                 return jsonify({
#                     "code": 1,
#                     "data": {
#                         "page": 1,
#                         "total": 0,
#                         "rows": []
#                     }
#                 })
#     except Exception as e:
#         raise

@add_algorithm.route("/get_assessment/", methods=["POST"])
def get_assessment():
    """获取评估方法"""
    uid = g.token.get("id")
    json_data = request.get_json()
    algorithm_id = json_data.get('algorithmId')
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        res = conn.query_all(
            'select a.id,a.`name`,a.definition from {TABLE} a join (select category from {TABLE1} where id = {ALGORITHMID}) b on a.categorie_id=b.category where uid = {UID}'.format(
                TABLE=config.TABLENAME45, UID=uid, ALGORITHMID=algorithm_id, TABLE1=config.TABLENAME1))

    return jsonify({"code": 1, "data": res})



# @add_algorithm.route("/save_analysis_model/", methods=["POST"])
# def save_analysis_model():
#     """保存算法模型"""
#     uid = g.token.get("id")
#     json_data = request.get_json()
#     algorithm_id = json_data.get('algorithmId')
#     model_name = json_data.get('modelName')
#     theme = json_data.get('theme')
#     purpose_column = json_data.get('purposeColumn')
#     drag_data = json_data.get('dragData')
#     source = json_data.get('source')
#     create_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#     conn = mysqlpool.get_conn()
#     the_uuid = str(uuid.uuid4())
#     with conn.swich_db(config.WOWRKSHEET01) as cursor:
#         res = conn.insert_one(
#             'insert into {TABLE} values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'.format(TABLE=config.TABLENAME42),
#             [the_uuid, uid, algorithm_id, model_name, theme, purpose_column, drag_data, source, create_date,
#              create_date, 1])
#     print("the_uuid",the_uuid)
#     print("res",res)
#     if res:
#         return jsonify({"code": 1, "data": the_uuid})
#     else:
#         return jsonify({"code": -1, "data": "操作失败"})

# /algorithm/save_analysis_model/
@add_algorithm.route("/save_analysis_model/", methods=["POST"])
def save_analysis_model():
    """保存算法模型"""
    uid = g.token.get("id")
    json_data = request.get_json()
    algorithm_id = json_data.get('algorithmId')
    # model_name = json_data.get('modelName')#  mainTitle
    model_name = json_data.get('mainTitle')
    theme = json_data.get('theme')
    purpose_column = json_data.get('purposeColumn')#
    # drag_data = json_data.get('dragData')# thumbnail
    # source = json_data.get('source')#
    drag_data = json_data.get('jsonstr')
    source = uid + "_db"+"_"+ json_data["mTable"]
    create_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = mysqlpool.get_conn()
    the_uuid = str(uuid.uuid4())
    try:
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
           
            res = conn.insert_one('insert into {TABLE} values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'.format(TABLE=config.TABLENAME42),
                [the_uuid, uid, algorithm_id, model_name, theme, purpose_column, drag_data, source, create_date, create_date, 1])
        
            return jsonify({"code": 1, "data": the_uuid})
    except Exception as e:
        raise e


@add_algorithm.route("/get_analysis_result/", methods=["POST"])
def get_analysis_result():
    """查看分析结果"""
    json_data = request.get_json()
    analysis_id = json_data.get('id')
    uid = g.token.get("id")
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        if conn.query_all(
            'select * from {TABLE} where id = "{ID}" and uid = {UID} and flag = 1'.format(TABLE=config.TABLENAME42,
                                                                                        ID=analysis_id, UID=uid)):
            res = conn.query_all(
                'select * from {TABLE} where id = "{ID}" and uid = {UID} and flag = 1'.format(TABLE=config.TABLENAME42,
                                                                                        ID=analysis_id, UID=uid))
        else:
            res= []
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
    temporaryid = str(uuid.uuid4())
    model_id = str(uuid.uuid1())
    uid = g.token.get("id")

    cl = table_and_field[targetdb]
    cl.remove(takgetfield)
    table_and_field[targetdb] = cl

    data = {}
    conn = mysqlpool.get_conn()
    with conn.swich_db("%s_db" % uid, cursor=pymysql.cursors.Cursor) as cursor:
        for k, v in table_and_field.items():
            res1 = conn.query_all("select {FIELD} from {TABLE}".format(FIELD=",".join(v), TABLE=k))
            for i, j in enumerate(v):
                data[j] = [k[i] for k in res1]
        res2 = conn.query_all("select {FIELD} from {TABLE}".format(FIELD=takgetfield, TABLE=targetdb))

        data[takgetfield] = [k[0] for k in res2]

    client = pymongo.MongoClient(host=config.M_HOST, port=config.M_PORT, username=config.M_USER,
                                 password=config.M_PASSWORD)
    collection = client[config.M_DBNAME1][config.M_COLLECTION1]

    c = collection.insert_one({"id": temporaryid,
                           "data": {"data": data, "mark": "%s+train" % model_id, "evaluate": assessment_ids,
                                    "param": ""}})
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.DBNAME1, cursor=pymysql.cursors.Cursor) as cursor:
        res = conn.query_one("select pythonPath from {} where id = {}".format(config.TABLENAME1, algorithm_id))

    ec = "%s/%s" % (config.ALGORITHM_PATH, res[0])
    cmd = "{PYTHON_PATH} {EC} {ARGS}".format(PYTHON_PATH=config.PYTHON_PATH, EC=ec, ARGS=temporaryid)
    cmdres = subprocess.run(cmd,shell='/usr/local/bash').returncode
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
            conn.insert_one("insert into {} (user_id,algorithmicName,definition,category,data_type,dimensions,pythonPath,resource_name,version_num,flag) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(
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


