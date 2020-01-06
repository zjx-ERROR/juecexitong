#  布局APP

from flask import Blueprint, request, jsonify, Response, g
from utils.dbutils import mysqlpool
from instance import config
import datetime
import random
import base64
from utils.json_helper import DateEncoder
import json
from werkzeug.utils import secure_filename

# 创建布局 的蓝图
layout = Blueprint("layout", __name__)

@layout.route("/layoutmsg/save/", methods=["POST"])
def save():
    """保存布局信息到数据库"""
    json_data = request.get_json()
    layoutGrid = json_data["layoutGrid"]
    layoutName = json_data["layoutName"]
    layoutJson = json.dumps(json_data["layoutJson"])
    type = json_data["type"]
    now_time = datetime.datetime.now()
    date_time = now_time.strftime("%Y-%m-%d %H:%M:%S")
    time_01 = now_time.strftime("%Y%m%d%H%M%S")
    userid= g.token["id"]

    # 图片数据处理
    thumbnail = json_data["path"].split(",")[-1]
    imgdata = base64.b64decode(thumbnail)
    path01 = config.LAYOUT01 + time_01 + ".jpg"
    path = config.LAYOUTPATH + time_01 + ".jpg"
    file = open(path01, "wb+")
    file.write(imgdata)
    file.close()
    flag=1
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if "id" in dict(request.get_json()).keys():
                id= request.get_json()["id"]  # 布局id
                conn.update("update {} set userid=%s,layoutGrid=%s, layoutJson=%s,layoutName=%s,path=%s,type=%s,createDate=%s where layoutid=%s and userid=%s".format(
                    config.TABLENAME20),(userid,layoutGrid,layoutJson,layoutName,path,type,date_time,id,userid))
                return jsonify({
                    "code": 1,
                    "data": "修改布局信息成功"

                })
            else:
                # 构建布局id 唯一值
                layoutid = g.token["token"][:-4] + str(random.randint(1000, 9999))
                conn.insert_one(
                    "insert into {}(layoutid,userid, layoutGrid, layoutJson,layoutName,path,type,createDate,flag) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(
                        config.TABLENAME20),
                    (layoutid,userid, layoutGrid, layoutJson, layoutName, path, type, date_time,flag))
                return jsonify({
                    "code": 1,
                    "data": "保存布局成功"
                })
    except Exception as e:
        raise e

@layout.route("/dellayout/", methods=["POST"])
def dellayout():
    """删除布局"""
    json_data = request.get_json()
    layoutids= json_data["ids"]
    userid= g.token["id"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
        for i in layoutids:
          conn.update("update {} set flag={} where layoutid=%s and userid=%s".format(config.TABLENAME20,0),[i,userid])
      return jsonify({
          "code": 1,
          "data": "删除布局成功"
      })
    except Exception as e:
        raise e


@layout.route("/layoutmsg/select/", methods=["POST"])
def select():
    """查找具体某一个布局信息"""
    json_data = request.get_json()
    layoutid = json_data["layoutid"]
    userid= g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            returndata = conn.query_one(
                "select * from {} where layoutid=%s and flag=%s and userid=%s".format(
                    config.TABLENAME20), [layoutid,1,userid])
        return Response(json.dumps({"code": 1, "data": [returndata]}, cls=DateEncoder), mimetype='application/json')
    except Exception as e:
        raise e


@layout.route("/layoutmsg/select_all/", methods=["POST"])
def select_all():
    """查找全部布局信息"""
    json_data = request.get_json()
    # 获取当前页数
    page = json_data["page"]
    # 获取每页信息数量
    total = json_data["pageSize"]
    flag=1
    userid = g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            returndata = []
            return_dic = {}
            if conn.query_all(
                "select * from {} where flag=%s and userid=%s".format(
                    config.TABLENAME20),[flag,userid]):
                return_list = conn.query_all(
                    "select * from {} where flag=%s and userid=%s".format(
                        config.TABLENAME20),[flag,userid])
                # 总数量
                count = len(return_list)
                # 总页数
                pages = count // total if count % total == 0 else count // total + 1
                # 总数量 大于 每页数量 但页码为一 显示第一页内容
                if total <= count and page == 1:
                    return_list = conn.query_all(
                        "select * from {} where flag=%s and userid=%s LIMIT %s ".format(
                            config.TABLENAME20), [flag,userid,total])
                elif total > count and page == 1:
                    return_list = return_list
                elif count > total and 1 < page <= pages:
                    return_list = conn.query_all(
                        "select * from {} where flag=%s and userid=%s LIMIT %s,%s ".format(
                            config.TABLENAME20), [flag,userid,(page - 1) * total, total])
                for i in return_list:
                    returndata.append(i)
            else:
                count=0
        # 返回数据
        return_dic["page"] = page
        return_dic["total"] = count
        return_dic["rows"] = returndata
        return Response(json.dumps({"code": 1, "data": return_dic}, cls=DateEncoder), mimetype='application/json')
    except Exception as e:
        raise e


# 图片存储接口 返回图片存储地址
@layout.route("/picture/", methods=["POST"])
def picture():
    """图片保存 返回保存地址"""
    json_data = request.get_json()
    now_time = datetime.datetime.now()
    time_01 = now_time.strftime("%Y%m%d%H%M%S")

    # 图片数据处理
    thumbnail = json_data["picture"].split(",")[-1]
    imgdata = base64.b64decode(thumbnail)
    path = config.LAYOUT01 + time_01 + ".jpg"
    return_path = config.CHARPATH + time_01 + ".jpg"
    file = open(path, "wb+")
    file.write(imgdata)
    file.close()

    return jsonify({
        "code": 1,
        "data": [return_path]

    })


@layout.route('/datafile/', methods=['POST'])
def datafile():
    # 获取post过来的文件名称，从name=file参数中获取
    file = request.files['file']
    now_time = datetime.datetime.now()
    time_01 = now_time.strftime("%Y%m%d%H%M%S")

    filename= file.filename
    filesuffix = filename.split('.')[1]
    file_name = time_01 + '.' + filename.rsplit('.', 1)[1]
    path =config.LAYOUT01 + file_name
    file.save(path)

    # 返回前端地址
    return_path = config.LAYOUTPATH + file_name
    dic ={}
    dic["path"] = return_path
    dic["filesuffix"] = filesuffix
    return jsonify({
        "code": 1,
        "data": [dic]
    })

@layout.route("/sharelayout/", methods=["POST"])
def sharelayout():
    # 分享布局验证 产生token秘钥
    json_data = request.get_json()
    layoutid = json_data["layoutid"]
    # 是否需要验证码
    isidentifying = json_data["isidentifying"]
    uid = int(g.token["id"])

    # 随机验证码函数
    def random_code(num):
        code = ""
        for i in range(0, num):
            zm = chr(random.randint(65, 90))
            code = code + zm
        return code

    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            current_layoutmsg = conn.query_one("select * from {} where layoutid=%s".format(config.TABLENAME20),
                                               [layoutid])
            # 验证码状态的判断与赋值
            if isidentifying == 1 and current_layoutmsg["isidentifying"] == 1:
                if not current_layoutmsg["identifying"] or current_layoutmsg["identifying"] == "":
                    identifying = random_code(4)
                else:
                    identifying = current_layoutmsg["identifying"]
            elif isidentifying == 1 and current_layoutmsg["isidentifying"] == 0:
                isidentifying = 1
                identifying = random_code(4)
            else:
                isidentifying = 0
                identifying = ""

            # 判断当前是否在分享状态
            if current_layoutmsg["isshare"] == 1 and current_layoutmsg["url2"] != "":
                url2 = current_layoutmsg["url2"]
                isshare = 1
            else:
                url2 = random_code(6)
                isshare = 1

            # # 执行定时任务
            if "sharetime" in dict(json_data).keys():
                sharetime = json_data["sharetime"]
                args = str((0, sharetime, layoutid))
                now_time = datetime.datetime.now()
                date_time = now_time.strftime("%Y-%m-%d %H:%M:%S")

                # 将定时任务数据添加到 scheduler_python定时任务表中  判断表中是否有相应的数据 没有就插入
                if conn.query_one("select * from {} where uid=%s and flag=%s and layoutid=%s".format(config.TABLENAME25),[uid,1,layoutid]):
                    conn.update("update {} set args=%s,createDate=%s,flag=%s where uid=%s and flag=%s and layoutid=%s".format(config.TABLENAME25),[args,date_time,1,uid,1,layoutid])
                    schedulerid= conn.query_one("select * from {} where uid=%s and flag=%s and layoutid=%s".format(config.TABLENAME25),[uid,1,layoutid])["id"]
                else:
                    schedulerid= conn.insert_one(
                        "insert into {} (uid,layoutid,schedulertype,func,args,run_date,createDate,flag) values (%s,%s,%s,%s,%s,%s,%s,%s)".format(
                            config.TABLENAME25), (uid, layoutid,"date", "update_isshare", args,sharetime,date_time,1))

                token_cn = {"layoutid": layoutid, "uid": uid, "isidentifying": isidentifying, "sharetime": sharetime}
                token_cn = str(token_cn)
                conn.update(
                    "update {table} set isshare=%s,isidentifying=%s,identifying=%s,url2=%s, sharetime=%s,token_cn=%s,schedulerid=%s where layoutid=%s".format(
                        table=config.TABLENAME20, token_cn=token_cn),
                    [isshare, isidentifying, identifying, url2, sharetime, token_cn,schedulerid, layoutid])
            else:
                # 更新到数据库 layoutmsg
                token_cn = {"layoutid": layoutid, "uid": uid, "isidentifying": isidentifying}
                token_cn = str(token_cn)
                conn.update(
                    "update {} set isshare=%s,isidentifying=%s,identifying=%s,url2=%s,token_cn=%s where layoutid=%s".format(
                        config.TABLENAME20), [isshare, isidentifying, identifying, url2, token_cn, layoutid])
            return jsonify({
                "code": 1,
                "data": [{"isidentifying": isidentifying, "identifying": identifying, "url2": url2}]
            })

    except Exception as e:
        raise e


@layout.route("/close_sharelayout/", methods=["POST"])
def close_sharelayout():
    # 手动关闭分享状态
    json_data = request.get_json()
    layoutid = json_data["layoutid"]
    userid= g.token["id"]
    isshare = 0
    url2 = ""
    token_cn = ""
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            schedulerid= conn.query_one("select * from {} where userid=%s and layoutid=%s".format(config.TABLENAME20),[userid,layoutid])["schedulerid"]
            conn.update("update {} set flag=%s where layoutid=%s and id=%s".format(config.TABLENAME25),[0,layoutid,schedulerid])
            conn.update("update {} set isshare=%s,url2=%s,token_cn=%s where layoutid=%s and userid=%s".format(config.TABLENAME20),
                        [isshare, url2, token_cn, layoutid,userid])
        return jsonify({
            "code": 1,
            "data": "手动关闭布局分享状态"
        })
    except Exception as e:
        raise e


# 分享链接返回数据
@layout.route("/shareurl/", methods=["POST"])
def shareurl():
    json_data = request.get_json()
    url2 = json_data["url2"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            # 先判断有没有url2
            if conn.query_one(
                    "select layoutid, layoutGrid, layoutJson,layoutName,path,type,createDate,isshare,isidentifying,identifying,sharetime,url2 from {} where url2=%s".format(
                        config.TABLENAME20), [url2]):
                layout_msg = conn.query_one(
                    "select layoutid, layoutGrid, layoutJson,layoutName,path,type,createDate,isshare,isidentifying,identifying,sharetime,url2 from {} where url2=%s".format(
                        config.TABLENAME20), [url2])
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


# 判断是否要验证码
@layout.route("/is_identifying/", methods=["POST"])
def is_identifying():
    json_data = request.get_json()
    url2 = json_data["url2"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            # 先判断有没有url2
            if conn.query_one(
                    "select layoutid, layoutGrid, layoutJson,layoutName,path,type,createDate,isshare,isidentifying,identifying,sharetime,url2 from {} where url2=%s".format(
                        config.TABLENAME20), [url2]):
                layout_msg = conn.query_one(
                    "select layoutid, layoutGrid, layoutJson,layoutName,path,type,createDate,isshare,isidentifying,identifying,sharetime,url2 from {} where url2=%s".format(
                        config.TABLENAME20), [url2])

                # 判断前端是否要传验证码
                if layout_msg["isidentifying"] == 1:
                    return jsonify({
                        "code": 1,
                        "data": [{"isidentifying": 1}]})
                else:
                    return jsonify({
                        "code": 1,
                        "data": [{"isidentifying": 0}]})
            else:
                return jsonify({
                    "code": -1,
                    "data": "传递的参数有误，请重新发送!"})
    except Exception as e:
        raise e
