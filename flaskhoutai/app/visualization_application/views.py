from flask import Blueprint, request, jsonify, Response, g
from utils.dbutils import mysqlpool
from instance import config
import pymysql
import time, datetime
import base64
import random, string
import uuid

# 创建可视化应用 的蓝图
visualization_application = Blueprint("visualization_application", __name__)

# http://120.31.140.112:8080/componentManagement//chart/list  原地址
@visualization_application.route("/componentlist/", methods=["POST"])
def componentlist():
    """查找所有业务组件数据"""
    json_data = request.get_json()
    page = json_data["page"]
    rows = json_data["rows"]  # 每页数据条数
    searchValue = json_data["searchValue"]  # 搜索关键字  全部为 ""
    uid = g.token["id"]
    flag = 1

    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if searchValue=="" or searchValue=="1" or searchValue==1:
                search_where=""
            else:
                search_where = "and a.theme={searchValue}".format(searchValue=searchValue)
            if conn.query_all(
                "select * from {tableA} as a left join {tableB} as b  on a.theme = b.id where a.flag={flag} and a.uid={uid} {search_where} ORDER BY a.createDate DESC".format(
                    tableA=config.TABLENAME3, tableB=config.TABLENAME23, flag=flag, uid=uid, search_where=search_where)):
                component_list = conn.query_all(
                    "select * from {tableA} as a left join {tableB} as b  on a.theme = b.id where a.flag={flag} and a.uid={uid} {search_where} ORDER BY a.createDate DESC".format(
                        tableA=config.TABLENAME3, tableB=config.TABLENAME23, flag=flag, uid=uid, search_where=search_where))
                total = len(component_list)  # 查询总条数
                # 总页数
                if total % rows == 0:
                    pages = total // rows
                else:
                    pages = total // rows + 1
                # 总数量 大于 每页数量 但页码为一 显示第一页内容
                re_list = []
                if rows <= total and page == 1:
                    re_list = conn.query_all(
                        "select * from {tableA} as a left join {tableB} as b  on a.theme = b.id where a.flag={flag} and a.uid={uid} {search_where} ORDER BY a.createDate DESC LIMIT {limit}".format(
                            tableA=config.TABLENAME3, tableB=config.TABLENAME23, flag=flag, uid=uid, search_where=search_where,
                            limit=rows))
                elif rows > total and page == 1:
                    re_list = component_list
                elif total > rows and 1 < page <= pages:
                    re_list = conn.query_all(
                        "select * from {tableA} as a left join {tableB} as b  on a.theme = b.id where a.flag={flag} and a.uid={uid} {search_where} ORDER BY a.createDate DESC LIMIT {limit},{limit1}".format(
                            tableA=config.TABLENAME3, tableB=config.TABLENAME23, flag=flag, uid=uid,
                            search_where=search_where, limit=(page - 1) * rows, limit1=total))
                return_data = []
                func = lambda x: x if x else ""
                for i in re_list:
                    return_dic = {}
                    return_dic["cacula"] = func(i["cacula"])
                    return_dic["categoryName"] = func(i["categoryName"])
                    return_dic["chartDataSourceId"] = func(i["chartDataSourceId"])
                    return_dic["columnMap"] = func(i["columnMap"])
                    return_dic["createDate"] = i["createDate"].strftime("%Y-%m-%d %H:%M:%S")
                    return_dic["editDate"] = i["editDate"].strftime("%Y-%m-%d %H:%M:%S")
                    return_dic["flag"] = i["flag"]
                    return_dic["id"] = i["id"]
                    return_dic["jsonstr"] = i["jsonstr"]
                    return_dic["mSchema"] = func(i["mSchema"])
                    return_dic["mTable"] = func(i["mTable"])
                    return_dic["main_title"] = i["main_title"]
                    return_dic["other_opt"] = func(i["other_opt"])
                    return_dic["precentValueArr"] = func(i["precentValueArr"])
                    return_dic["reserve_param"] = func(i["reserve_param"])
                    return_dic["selectArr"] = func(i["selectArr"])
                    return_dic["selectVArr"] = func(i["selectVArr"])
                    return_dic["selectedPartStatus"] = func(i["selectedPartStatus"])
                    return_dic["showData"] = func(i["showData"])
                    return_dic["subtitle"] = func(i["subtitle"])
                    return_dic["theme"] = func(i["theme"])
                    return_dic["thumbnail"] = i["thumbnail"]
                    return_dic["type"] = i["type"]
                    return_dic["uid"] = i["uid"]
                    return_dic["user_id"] = func(i["user_id"])
                    return_dic["username"] = func(i["username"])
                    return_dic["yujingArr"] = func(i["yujingArr"])
                    return_data.append(return_dic)
                return jsonify({
                    "code": 1,
                    "data": {
                        "page": page,
                        "rows": return_data,
                        "total": total
                    }
                })
            else:
                return jsonify({
                    "code": 1,
                    "data": {
                        "page": page,
                        "rows": [],
                        "total": 0
                    }
                })
    except Exception as e:
        raise e



@visualization_application.route("/delcomponent/", methods=["POST"])
def delcomponent():
    """删除业务组件库列表"""
    json_data = request.get_json()
    componentids = json_data["ids"]
    conn = mysqlpool.get_conn()
    try:
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            for i in componentids:
                conn.update("update {} set flag={} where id=%s".format(config.TABLENAME3, 0), [i])
        return jsonify({
            "code": 1,
            "msg": "删除业务组件库成功"
        })
    except Exception as e:
        raise e


@visualization_application.route("/componentmsg/", methods=["POST"])
def componentmsg():
    """查找某个业务组件数据"""
    json_data = request.get_json()
    componentid = json_data["id"]
    conn = mysqlpool.get_conn()
    try:
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            re_list = conn.query_one("select * from {} where id=%s".format(config.TABLENAME3), [componentid])
        return_dic = {}
        func = lambda x: x if x else ""
        return_dic["chartDataSourceId"] = func(re_list["chartDataSourceId"])
        return_dic["columnMap"] = func(re_list["columnMap"])
        return_dic["createDate"] = int(time.mktime(re_list["createDate"].timetuple()))
        return_dic["editDate"] = int(time.mktime(re_list["editDate"].timetuple()))
        return_dic["flag"] = re_list["flag"]
        return_dic["id"] = re_list["id"]
        return_dic["jsonstr"] = re_list["jsonstr"]
        return_dic["mTable"] = func(re_list["mTable"])
        return_dic["mainTitle"] = re_list["main_title"]
        return_dic["otherOpt"] = func(re_list["other_opt"])
        return_dic["schema"] = func(re_list["mSchema"])
        return_dic["subtitle"] = func(re_list["subtitle"])
        return_dic["theme"] = func(re_list["theme"])
        return_dic["thumbnail"] = re_list["thumbnail"]
        return_dic["type"] = re_list["type"]
        return_dic["uid"] = re_list["uid"]
        return jsonify({
            "code": 1,
            "data": return_dic
        })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//component/getAllCategory  获取组件类型含全部
@visualization_application.route("/getAllCategory/", methods=["POST"])
def getAllCategory():
    """获取组件类型含全部"""
    json_data = request.get_json()
    conn = mysqlpool.get_conn()
    try:
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if conn.query_all("select * from {} ".format(config.TABLENAME23)):
                select_list = conn.query_all("select * from {} ".format(config.TABLENAME23))
                return_data = []
                return_data.append({"categoryName": "全部", "id": 1})
                for i in select_list:
                    i["createDate"] = i["createDate"].strftime("%Y-%m-%d %H:%M:%S")
                    i["editDate"] = i["editDate"].strftime("%Y-%m-%d %H:%M:%S")
                    return_data.append(i)
            else:
                return_data=[]
        return jsonify({
            "code": 1,
            "data": return_data
        })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//comm/QuotaOverviewEntity/delSelect 删除指标组件
@visualization_application.route("/delquotas/", methods=["POST"])
def delquotas():
    """删除指标组件库列表"""
    json_data = request.get_json()
    quotasids = json_data["ids"]
    conn = mysqlpool.get_conn()
    try:
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            for i in quotasids:
                conn.update("update {} set flag={} where id=%s".format(config.TABLENAME11, 0), [i])
        return jsonify({
            "code": 1,
            "msg": "删除指标组件成功"
        })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//quota/listEntity
@visualization_application.route("/quotaslist/", methods=["POST"])
def quotaslist():
    """查找所有指标组件数据"""
    """
    重写java代码小问题, 请求参数searchValue 为3 时（字符串 ） 查询数据表的 categoryId 为1
    前端值 比 后端值 大一
    """
    json_data = request.get_json()
    page = json_data["page"]
    rows = json_data["rows"]  # 每页数据条数
    uid = g.token["id"]
    flag = 1
    if "searchValue" in dict(json_data).keys():
        searchValue = json_data["searchValue"]  # 搜索关键字  全部为 ""
        if searchValue=="" or searchValue==1 or searchValue=="1":
            select_where=""
        else:
            categoryId = str(int(searchValue) - 1)
            select_where = " and categoryId={} ".format(categoryId)
    else:
        select_where=""
    conn = mysqlpool.get_conn()
    try:
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if conn.query_all(
                "select * from {table} where uid=%s and flag=%s {select_where} ORDER BY createDate DESC".format(
                    table=config.TABLENAME11, select_where=select_where), [uid, flag]):
                quotas_list = conn.query_all(
                    "select * from {table} where uid=%s and flag=%s {select_where} ORDER BY createDate DESC".format(
                        table=config.TABLENAME11, select_where=select_where), [uid, flag])
                total = len(quotas_list)  # 查询总条数
                # 总页数
                if total % rows == 0:
                    pages = total // rows
                else:
                    pages = total // rows + 1
                # 总数量 大于 每页数量 但页码为一 显示第一页内容
                quotas_return = []
                if rows <= total and page == 1:
                    quotas_return = conn.query_all(
                        "select * from {table} where uid=%s and flag=%s {select_where} ORDER BY createDate DESC LIMIT {limit}".format(
                            table=config.TABLENAME11, select_where=select_where, limit=rows), [uid, flag])
                elif rows > total and page == 1:
                    quotas_return = quotas_list
                elif total > rows and 1 < page <= pages:
                    quotas_return = conn.query_all(
                        "select * from {table} where uid=%s and flag=%s {select_where} ORDER BY createDate DESC LIMIT {limit},{limit1}".format(
                            table=config.TABLENAME11, select_where=select_where, limit=(page - 1) * rows, limit1=total),
                        [uid, flag])
                return_data = []
                func = lambda x: x if x else ""
                for i in quotas_return:
                    return_dic = {}
                    return_dic["categoryId"] = i["categoryId"]
                    return_dic["createDate"] = i["createDate"].strftime("%Y-%m-%d %H:%M:%S")
                    return_dic["editDate"] = i["editDate"].strftime("%Y-%m-%d %H:%M:%S")
                    return_dic["flag"] = i["flag"]
                    return_dic["id"] = i["id"]
                    return_dic["name1"] = func(i["name1"])
                    return_dic["name2"] = func(i["name2"])
                    return_dic["name3"] = func(i["name3"])
                    return_dic["name4"] = func(i["name4"])
                    return_dic["name5"] = func(i["name5"])
                    return_dic["thumbnail"] = i["thumbnail"]
                    return_dic["title"] = func(i["title"])
                    return_dic["uid"] = i["uid"]
                    return_dic["unit1"] = func(i["unit1"])
                    return_dic["unit2"] = func(i["unit2"])
                    return_dic["unit3"] = func(i["unit3"])
                    return_dic["unit4"] = func(i["unit4"])
                    return_dic["unit5"] = func(i["unit5"])
                    return_dic["value1"] = func(i["value1"])
                    return_dic["value2"] = func(i["value2"])
                    return_dic["value3"] = func(i["value3"])
                    return_dic["value4"] = func(i["value4"])
                    return_dic["value5"] = func(i["value5"])
                    return_data.append(return_dic)
                return jsonify({
                    "code": 1,
                    "data": {
                        "page": page,
                        "rows": return_data,
                        "total": total
                    }
                })
            else:
                return jsonify({
                    "code": 1,
                    "data": {
                        "page": page,
                        "rows": [],
                        "total": 0
                    }
                })

    except Exception as e:
        raise e



# http://120.31.140.112:8080/componentManagement//quota/saveQuotaOverviewEntity 增加保存指标类型数据
@visualization_application.route("/saveQuotaOverviewEntity/", methods=["POST"])
def saveQuotaOverviewEntity():
    """ 增加/修改 保存指标类型数据"""
    json_data = request.get_json()
    uid = g.token["id"]
    categoryId = json_data["categoryId"]
    name1 = json_data["name1"]
    name2 = json_data["name2"]
    name3 = json_data["name3"]
    name4 = json_data["name4"]
    name5 = json_data["name5"]
    token = json_data["token"]
    # 随机产生id

    # def randomid(num):
    #     lower_num = string.ascii_lowercase + string.digits
    #     randomstr = ""
    #     for i in range(num):
    #         randomstr += random.choice(lower_num)
    #     return randomstr
    # id = randomid(8) + token[8:24] + randomid(12)
    # 保存图片信息
    thumbnail = json_data["thumbnail"].split(",")[-1]
    imgdata = base64.b64decode(thumbnail)
    now_time = datetime.datetime.now()
    time01 = now_time.strftime("%Y%m%d%H%M%S")
    createDate = now_time.strftime("%Y-%m-%d %H:%M:%S")
    path01 = config.QUOTA01 + time01 + ".jpg"
    path = config.QUOTAOPATH + time01 + ".jpg"
    file = open(path01, "wb")
    file.write(imgdata)
    file.close()
    title = json_data["title"]
    unit1 = json_data["unit1"]
    unit2 = json_data["unit2"]
    unit3 = json_data["unit3"]
    unit4 = json_data["unit4"]
    unit5 = json_data["unit5"]
    value1 = json_data["value1"]
    value2 = json_data["value2"]
    value3 = json_data["value3"]
    value4 = json_data["value4"]
    value5 = json_data["value5"]
    conn = mysqlpool.get_conn()
    try:
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            # 初始化赋值
            editDate = createDate
            flag = 1
            # conn.update("update {} set userid=%s,bigscreenName=%s,layoutGrid=%s, layoutJson=%s,bigscreenPath=%s,bigscreenGroup=%s,createDate=%s where id=%s and userid=%s and flag=%s".format(
            #                     config.TABLENAME35),(userid,bigscreenName,layoutGrid,layoutJson,path,bigscreenGroup,createDate,id,userid,flag))
            if "id" in dict(json_data).keys():
                sid = json_data["id"]
                conn.update(
                    "update {} set thumbnail=%s, categoryId=%s,title=%s,name1=%s,value1=%s,unit1=%s,name2=%s,value2=%s,unit2=%s,name3=%s,value3=%s,unit3=%s,name4=%s,value4=%s,unit4=%s,name5=%s,value5=%s,unit5=%s,createDate=%s,editDate=%s,flag=%s where id=%s".format(
                        config.TABLENAME11),
                    [path, categoryId, title, name1, value1, unit1, name2, value2, unit2, name3, value3, unit3, name4,
                     value4, unit4, name5, value5, unit5, createDate, editDate, flag,sid])
            else:
                sid = str(uuid.uuid4())
                conn.insert_one(
                    "insert into {} (id,uid,thumbnail,categoryId,title,name1,value1,unit1,name2,value2,unit2,name3,value3,unit3,name4,value4,unit4,name5,value5,unit5,createDate,editDate,flag) values (%s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s)".format(
                        config.TABLENAME11),
                    [sid, uid, path, categoryId, title, name1, value1, unit1, name2, value2, unit2, name3, value3, unit3,
                     name4,
                     value4, unit4, name5, value5, unit5, createDate, editDate, flag])
        return jsonify({
            "code": 1,
            "msg": sid
        })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement/comm/view_component_category/listAll  获取组件类型
@visualization_application.route("/view_component_categorylistAll/", methods=["POST"])
def view_component_categorylistAll():
    """获取组件类型"""
    json_data = request.get_json()
    conn = mysqlpool.get_conn()
    try:
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            select_list = conn.query_all("select * from {} ".format(config.TABLENAME23))
        return_data = []
        for i in select_list:
            i["createDate"] = i["createDate"].strftime("%Y-%m-%d %H:%M:%S")
            i["editDate"] = i["editDate"].strftime("%Y-%m-%d %H:%M:%S")
            return_data.append(i)
        return jsonify({
            "code": 1,
            "data": return_data
        })
    except Exception as e:
        raise  e


# http://120.31.140.112:8080/componentManagement//comm/view_datasource_name/listAll  获取数据源
@visualization_application.route("/view_datasource_namelistAll/", methods=["POST"])
def view_datasource_namelistAll():
    """获取数据源"""
    json_data = request.get_json()
    flag =1
    conn = mysqlpool.get_conn()
    try:
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            select_list = conn.query_all("select id,sourceName from {} where flag=%s order by createDate DESC".format(config.TABLENAME4),[flag])
        return jsonify({
            "code": 1,
            "data": select_list
        })
    except Exception as e:
        raise e



