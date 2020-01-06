from flask import Blueprint, request, jsonify, g,Response
from utils.dbutils import mysqlpool
from instance import config
import datetime,json
import base64,time
import random, string
from utils.json_helper import DateEncoder

# 创建数据报表应用蓝图
databigscreen = Blueprint("databigscreen", __name__)

# http://120.31.140.112:8080/componentManagement/%20/comm/layout/queryAll 获取数据大屏列表
@databigscreen.route("/queryAll/", methods=["POST"])
def queryAll():
    """获取数据大屏列表"""
    uid = g.token["id"]
    flag = 1
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            bigscreenlist = conn.query_all(
                "select * from {} where uid=%s and flag=%s order by createDate DESC ".format(config.TABLENAME29),
                [uid, flag])
            return_list = []
            for i in bigscreenlist:
                i["createDate"] = i["createDate"].strftime("%Y-%m-%d %H:%M:%S")
                i["editDate"] = i["editDate"].strftime("%Y-%m-%d %H:%M:%S")
                return_list.append(i)
        return Response(json.dumps({"code": 1, "data": [return_list]}, cls=DateEncoder), mimetype='application/json')
        # return jsonify({
        #     "code": 1,
        #     "data": return_list
        # })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement/comm/Layout/delSelect 删除数据大屏列表
@databigscreen.route("/delSelect/", methods=["POST"])
def delSelect():
    """删除数据大屏列表"""
    json_data = request.get_json()
    bigscreenids= json_data["ids"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
        for i in bigscreenids:
          conn.update("update {} set flag={} where id=%s".format(config.TABLENAME29,0),[i])
      return jsonify({
          "code": 1,
          "msg": "删除数据大屏成功"
      })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//component/getAllChartCategoryComponent 获取组件类型及组件
@databigscreen.route("/getAllChartCategoryComponent/", methods=["POST"])
def getAllChartCategoryComponent():
    """获取组件类型及组件"""
    uid = g.token["id"]
    flag = 1
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            return_list=[]
            categorylist= conn.query_all("select id,categoryName from {}".format(config.TABLENAME23))
            for i in categorylist:
                categorydic={}
                categorydic["id"]= i["id"]
                categorydic["name"]= i["categoryName"]
                if conn.query_all("select id,jsonstr,main_title,theme,thumbnail,uid from {} where uid=%s and flag=%s and theme=%s order by createDate DESC".format(config.TABLENAME3),
                                                             [uid,flag,i["id"]])==0:
                    categorydic["componentList"]=[]
                else:
                    categorydic["componentList"]= conn.query_all("select id,jsonstr,main_title,theme,thumbnail,uid from {} where uid=%s and flag=%s and theme=%s order by createDate DESC".format(config.TABLENAME3),
                                                                 [uid,flag,i["id"]])
                return_list.append(categorydic)

        return jsonify({
            "code": 1,
            "data": return_list
        })
    except Exception as e:
        raise e


@databigscreen.route("/queryAllgroup/", methods=["POST"])
def queryAllgroup():
    """获取数据大屏分组信息"""
    flag = 1
    uid= g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if conn.query_all("select * from {} where flag=%s and uid=%s".format(config.TABLENAME33),[flag,uid]):
                bigscreenlist = conn.query_all("select * from {} where flag=%s and uid=%s".format(config.TABLENAME33),[flag,uid])
            else:
                bigscreenlist=[]

        return jsonify({
            "code": 1,
            "data": bigscreenlist
        })
    except Exception as e:
        raise e


@databigscreen.route("/addgroup/", methods=["POST"])
def addgroup():
    """新增大屏分组信息"""
    json_data = request.get_json()
    groupname = json_data["groupname"]
    uid = g.token["id"]
    flag= 1
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            conn.insert_one("insert into {} (uid,groupname,flag) values (%s,%s,%s)".format(config.TABLENAME33),[uid,groupname,flag])
        return jsonify({
            "code": 1,
            "data": "新增分组成功"
        })
    except Exception as e:
        raise e


@databigscreen.route("/updategroup/", methods=["POST"])
def updategroup():
    """修改大屏分组信息"""
    json_data = request.get_json()
    id= json_data["id"]
    groupname = json_data["groupname"]
    uid = g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            conn.update("update {} set groupname=%s where id=%s and uid=%s".format(config.TABLENAME33),[groupname,id,uid])
        return jsonify({
            "code": 1,
            "data": "修改分组信息成功"
        })
    except Exception as e:
        raise e


@databigscreen.route("/delgroup/", methods=["POST"])
def delgroup():
    """删除大屏分组信息"""
    json_data = request.get_json()
    id= json_data["id"]
    flag= 0
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            conn.update("update {} set flag=%s where id=%s".format(config.TABLENAME33),[flag,id])
        return jsonify({
            "code": 1,
            "data": "删除分组信息成功"
        })
    except Exception as e:
        raise e


@databigscreen.route("/savebigscreen/", methods=["POST"])
def savebigscreen():
    """保存修改大屏信息到数据库"""
    json_data = request.get_json()
    now_time = datetime.datetime.now()
    createDate = now_time.strftime("%Y-%m-%d %H:%M:%S")
    time_01 = now_time.strftime("%Y%m%d%H%M%S")
    userid= g.token["id"]
    flag=1

    # 随机验证码函数
    def generate_code(code_len=6):
        all_char = string.ascii_lowercase + string.ascii_uppercase
        index = len(all_char) + 1
        code = ''
        for _ in range(code_len):
            num = random.randint(0, index)
            code += all_char[num]
        return code


    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if "id" in dict(request.get_json()).keys() and "revisegroup" not in dict(request.get_json()).keys():
                layoutGrid = json_data["layoutGrid"]
                bigscreenName = json_data["layoutName"]
                layoutJson = json.dumps(json_data["layoutJson"])
                bigscreenGroup = json_data["bigscreenGroup"]
                thumbnail = json_data["thumbnail"].split(",")[-1]
                imgdata = base64.b64decode(thumbnail)
                path01 = config.DATABATESCREEN + time_01 + ".jpg"
                path = config.DATABIGPATH + time_01 + ".jpg"
                file = open(path01, "wb+")
                file.write(imgdata)
                file.close()
                id= request.get_json()["id"]  # 布局id
                conn.update("update {} set userid=%s,bigscreenName=%s,layoutGrid=%s, layoutJson=%s,bigscreenPath=%s,bigscreenGroup=%s,createDate=%s where id=%s and userid=%s and flag=%s".format(
                    config.TABLENAME35),(userid,bigscreenName,layoutGrid,layoutJson,path,bigscreenGroup,createDate,id,userid,flag))
                return jsonify({
                    "code": 1,
                    "data": "修改数据大屏成功"

                })
            elif "revisegroup" in dict(request.get_json()).keys():
                id = request.get_json()["id"]
                revisegroup = request.get_json()["revisegroup"]
                conn.update("update {} set bigscreenGroup=%s where id=%s and userid=%s and flag=%s".format(config.TABLENAME35),[revisegroup,id,userid,flag])
                return jsonify({
                    "code": 1,
                    "data": "修改数据大屏成功"

                })
            else:
                layoutGrid = json_data["layoutGrid"]
                bigscreenName = json_data["layoutName"]
                layoutJson = json.dumps(json_data["layoutJson"])
                bigscreenGroup = json_data["bigscreenGroup"]
                thumbnail = json_data["thumbnail"].split(",")[-1]
                imgdata = base64.b64decode(thumbnail)
                path01 = config.DATABATESCREEN + time_01 + ".jpg"
                path = config.DATABIGPATH + time_01 + ".jpg"
                file = open(path01, "wb+")
                file.write(imgdata)
                file.close()
                conn11 = mysqlpool.get_conn()
                with conn11.swich_db(config.WOWRKSHEET01):
                    while True:
                        url2 = str(userid) + generate_code(6)
                        if conn11.query_one("select * from {} where userid=%s and flag=%s and url2=%s".format(config.TABLENAME48),[userid,flag,url2]):
                            url2 = str(userid) + generate_code(6)
                        else:
                            conn11.insert_one("insert into {} (userid,url2,flag) values (%s,%s,%s)".format(config.TABLENAME48),[userid,url2,flag])
                            conn11.commit()
                            break
                conn.insert_one(
                    "insert into {}(userid,bigscreenName,layoutGrid, layoutJson,bigscreenPath,bigscreenGroup,url2,createDate,flag) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(
                        config.TABLENAME35),
                    (userid,bigscreenName,layoutGrid, layoutJson,path,bigscreenGroup, url2,createDate,flag))
                return jsonify({
                    "code": 1,
                    "data": url2

                })
    except Exception as e:
        raise e


# 分享链接返回数据
@databigscreen.route("/shareurl/", methods=["POST"])
def shareurl():
    json_data = request.get_json()
    url2 = json_data["url2"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            # 先判断有没有url2
            if conn.query_one(
                    "select id, layoutGrid, layoutJson,bigscreenName,bigscreenPath,bigscreenGroup,createDate,isshare,isidentifying,identifying,sharetime,url2 from {} where url2=%s".format(
                        config.TABLENAME35), [url2]):
                layout_msg = conn.query_one(
                    "select id, layoutGrid, layoutJson,bigscreenName,bigscreenPath,bigscreenGroup,createDate,isshare,isidentifying,identifying,sharetime,url2 from {} where url2=%s".format(
                        config.TABLENAME35), [url2])
                # 判断前端是否要传验证码
                if "identifying" in dict(json_data).keys():
                    identifying = json_data["identifying"]
                    if layout_msg["identifying"].upper() == identifying.upper():
                        return Response(json.dumps({"code": 1, "data": [layout_msg]}, cls=DateEncoder),
                                        mimetype='application/json')
                    else:
                        return jsonify({
                            "code": 1,
                            "data": "验证码验证错误，请重新输入"})
                else:
                    return Response(json.dumps({"code": 1, "data": [layout_msg]}, cls=DateEncoder),
                                    mimetype='application/json')
            else:
                return jsonify({
                    "code": -1,
                    "data": "传递的参数有误，请重新发送!"})
    except Exception as e:
        raise e

# @databigscreen.route("/savebigscreen/", methods=["POST"])
# def savebigscreen():
#     """保存修改大屏信息到数据库"""
#     json_data = request.get_json()
#     now_time = datetime.datetime.now()
#     createDate = now_time.strftime("%Y-%m-%d %H:%M:%S")
#     time_01 = now_time.strftime("%Y%m%d%H%M%S")
#     userid= g.token["id"]
#     flag=1
#     try:
#         conn = mysqlpool.get_conn()
#         with conn.swich_db(config.WOWRKSHEET01) as cursor:
#             if "id" in dict(request.get_json()).keys() and "revisegroup" not in dict(request.get_json()).keys():
#                 layoutGrid = json_data["layoutGrid"]
#                 bigscreenName = json_data["layoutName"]
#                 layoutJson = json.dumps(json_data["layoutJson"])
#                 bigscreenGroup = json_data["bigscreenGroup"]
#                 thumbnail = json_data["thumbnail"].split(",")[-1]
#                 imgdata = base64.b64decode(thumbnail)
#                 path01 = config.DATABATESCREEN + time_01 + ".jpg"
#                 path = config.DATABIGPATH + time_01 + ".jpg"
#                 file = open(path01, "wb+")
#                 file.write(imgdata)
#                 file.close()
#                 id= request.get_json()["id"]  # 布局id
#                 conn.update("update {} set userid=%s,bigscreenName=%s,layoutGrid=%s, layoutJson=%s,bigscreenPath=%s,bigscreenGroup=%s,createDate=%s where id=%s and userid=%s and flag=%s".format(
#                     config.TABLENAME35),(userid,bigscreenName,layoutGrid,layoutJson,path,bigscreenGroup,createDate,id,userid,flag))
#                 return jsonify({
#                     "code": 1,
#                     "data": "修改数据大屏成功"
#
#                 })
#             elif "revisegroup" in dict(request.get_json()).keys():
#                 id = request.get_json()["id"]
#                 revisegroup = request.get_json()["revisegroup"]
#                 conn.update("update {} set bigscreenGroup=%s where id=%s and userid=%s and flag=%s".format(config.TABLENAME35),[revisegroup,id,userid,flag])
#                 return jsonify({
#                     "code": 1,
#                     "data": "修改数据大屏成功"
#
#                 })
#             else:
#                 layoutGrid = json_data["layoutGrid"]
#                 bigscreenName = json_data["layoutName"]
#                 layoutJson = json.dumps(json_data["layoutJson"])
#                 bigscreenGroup = json_data["bigscreenGroup"]
#                 thumbnail = json_data["thumbnail"].split(",")[-1]
#                 imgdata = base64.b64decode(thumbnail)
#                 path01 = config.DATABATESCREEN + time_01 + ".jpg"
#                 path = config.DATABIGPATH + time_01 + ".jpg"
#                 file = open(path01, "wb+")
#                 file.write(imgdata)
#                 file.close()
#                 conn.insert_one(
#                     "insert into {}(userid,bigscreenName,layoutGrid, layoutJson,bigscreenPath,bigscreenGroup,createDate,flag) values (%s,%s,%s,%s,%s,%s,%s,%s)".format(
#                         config.TABLENAME35),
#                     (userid,bigscreenName,layoutGrid, layoutJson,path,bigscreenGroup, createDate,flag))
#                 return jsonify({
#                     "code": 1,
#                     "data": "保存数据大屏数据成功"
#
#                 })
#     except Exception as e:
#         raise e



@databigscreen.route("/delbigscreen/", methods=["POST"])
def delbigscreen():
    """删除数据大屏"""
    json_data = request.get_json()
    bigscreenids= json_data["ids"]
    userid= g.token["id"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
        for i in bigscreenids:
          conn.update("update {} set flag={} where id=%s and userid=%s".format(config.TABLENAME35,0),[i,userid])
      return jsonify({
          "code": 1,
          "data": "删除数据大屏成功"
      })
    except Exception as e:
        raise e


@databigscreen.route("/selbigscreen/", methods=["POST"])
def selbigscreen():
    """查找具体某一个数据大屏信息"""
    json_data = request.get_json()
    bigscreenid = json_data["id"]
    userid= g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            func = lambda x: x if x else ""
            returndata = conn.query_one(
                "select * from {} where id=%s and flag=%s and userid=%s".format(
                    config.TABLENAME35), [bigscreenid,1,userid])
            returndata["isshare"] = func(returndata["isshare"])
            returndata["isidentifying"] = func(returndata["isidentifying"])
            returndata["identifying"] = func(returndata["identifying"])
            returndata["url2"] = func(returndata["url2"])
            returndata["sharetime"] = func(returndata["sharetime"])
        return Response(json.dumps({"code": 1, "data": [returndata]}, cls=DateEncoder), mimetype='application/json')
    except Exception as e:
        raise e


@databigscreen.route("/selectAllselbigscreen/", methods=["POST"])
def selectAllselbigscreen():
    """查找全部数据大屏信息"""
    json_data = request.get_json()
    # 获取当前页数
    page = json_data["page"]
    # 获取每页信息数量
    total = json_data["pageSize"]
    flag=1
    userid = g.token["id"]
    bigscreenGroup= json_data["bigscreenGroup"]
    func = lambda x: x if x else ""
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if conn.query_all(
                "select * from {} where flag=%s and userid=%s and bigscreenGroup=%s".format(
                    config.TABLENAME35),[flag,userid,bigscreenGroup]):
                return_list = conn.query_all(
                    "select * from {} where flag=%s and userid=%s and bigscreenGroup=%s".format(
                        config.TABLENAME35),[flag,userid,bigscreenGroup])
            else:
                return jsonify({
                    "code":1,
                    "data":{
                        "page":1,
                        "total":0,
                        "rows":[]
                    }
                })

            count = len(return_list)
            # 总页数
            pages = count // total if count % total == 0 else count // total + 1
            # 总数量 大于 每页数量 但页码为一 显示第一页内容
            if total <= count and page == 1:
                return_list = conn.query_all(
                    "select * from {} where flag=%s and userid=%s and bigscreenGroup=%s LIMIT %s ".format(
                        config.TABLENAME20), [flag,userid,bigscreenGroup,total])
            elif total > count and page == 1:
                return_list = return_list
            elif count > total and 1 < page <= pages:
                return_list = conn.query_all(
                    "select * from {} where flag=%s and userid=%s and bigscreenGroup=%s LIMIT %s,%s ".format(
                        config.TABLENAME20), [flag,userid,bigscreenGroup,(page - 1) * total, total])
        return_dic = {}
        returndata = []
        for i in return_list:
            i["isshare"]= func(i["isshare"])
            i["isidentifying"]= func(i["isidentifying"])
            i["identifying"]= func(i["identifying"])
            i["url2"] = func(i["url2"])
            i["sharetime"]= func(i["sharetime"])
            i["editDate"] = datetime.datetime.now()
            returndata.append(i)


        # 返回数据
        return_dic["page"] = page
        return_dic["total"] = count
        return_dic["rows"] = returndata
        return Response(json.dumps({"code": 1, "data": return_dic}, cls=DateEncoder), mimetype='application/json')

    except Exception as e:
        raise e
