from flask import Blueprint, request, jsonify, g, Response, send_file, make_response,send_from_directory
from utils.dbutils import mysqlpool
from instance import config
import datetime
import base64,time
import random, string
from utils.json_helper import DateEncoder
import json

# 创建数据报表应用蓝图
data_report = Blueprint("data_report", __name__)

# http://120.31.140.112:8080/componentManagement//reportDB/listAll   获取系统数据报表
@data_report.route("/reportlistAll/", methods=["POST"])
def reportlistAll():
    """获取系统数据报表"""
    json_data = request.get_json()
    uid= g.token["id"]
    flag= 1
    # 数据报表组id
    # groupid= json_data["groupid"]

    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if "groupid" not in dict(json_data) and "reportDBId" in dict(json_data):
                userid= json_data["uid"]
                aa= conn.query_one("select * from {} where uid=%s and id=%s and flag=%s".format(config.TABLENAME9),[userid,json_data["reportDBId"],flag])
                groupid= aa["groupid"]
            else:
                groupid = json_data["groupid"]
            if conn.query_all("select * from {} where uid=%s and flag=%s and groupid= %s order by createDate DESC ".format(config.TABLENAME9),[uid, flag,groupid]):
              reportdblist= conn.query_all("select * from {} where uid=%s and flag=%s and groupid= %s order by createDate DESC ".format(config.TABLENAME9),[uid, flag,groupid])
              return_list=[]
              func= lambda x: x if x else ""
              for i in reportdblist:
                  i["createDate"] = i["createDate"].strftime("%Y-%m-%d %H:%M:%S")
                  i["editDate"] = i["editDate"].strftime("%Y-%m-%d %H:%M:%S")
                  i["styleId"] = func(i["styleId"])
                  i["styleObj"] = func(i["styleObj"])
                  i["thumbnail"] = func(i["thumbnail"])
                  i["reportType"]= func(i["reportType"])
                  return_list.append(i)
            else:
                return_list=[]

        return jsonify({
            "code": 1,
            "data": return_list
        })
    except Exception as e:
          raise e

# http://120.31.140.112:8080/componentManagement//reportDB/delSelect 删除系统数据报表
@data_report.route("/delreportDB/", methods=["POST"])
def delreportDB():
    """删除系统数据报表"""
    json_data = request.get_json()
    quotasids= json_data["ids"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
        for i in quotasids:
          conn.update("update {} set flag={} where id=%s".format(config.TABLENAME9,0),[i])
      return jsonify({
          "code": 1,
          "data": "删除系统数据报表成功"
      })
    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement/reportDB/save  增加系统数据报表
@data_report.route("/addreportDB/", methods=["POST"])
def addreportDB():
    """增加系统数据报表"""
    json_data = request.get_json()
    uid = g.token["id"]
    newreportname = json_data["name"]
    token= json_data["token"]
    # 新添 reportgroup 参数 数据报表组id  int 整形
    groupid = json_data["groupid"]

    def randomid(num):
        lower_num = string.ascii_lowercase + string.digits
        randomstr = ""
        for i in range(num):
            randomstr += random.choice(lower_num)
        return randomstr
    id = randomid(8) + token[8:24] + randomid(12)
    now_time = datetime.datetime.now()
    createDate = now_time.strftime("%Y-%m-%d %H:%M:%S")
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.WOWRKSHEET01) as cursor:
        editDate = createDate
        flag = 1
        conn.insert_one("insert into {} (id,uid,groupid,name,createDate,editDate,flag) values (%s,%s,%s,%s,%s,%s,%s)".format(
                config.TABLENAME9),
            [id, uid, groupid,newreportname, createDate, editDate, flag])
      return jsonify({
          "code": 1,
          "msg": id
      })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement/dataOverviewTemplate/getByUidAndReportDBId  通过报表id获取模板图列表(业务组件)
@data_report.route("/dataOverviewTemplate/", methods=["POST"])
def dataOverviewTemplate():
    """通过报表id获取表报下的业务组件内容"""
    json_data = request.get_json()
    reportDBId = json_data["reportDBId"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.WOWRKSHEET01) as cursor:
        if conn.query_all("select componentId,size from {} where reportDBId=%s and flag=%s".format(config.TABLENAME5),[reportDBId,1]):
          componentIdlist= conn.query_all("select componentId,size from {} where reportDBId=%s and flag=%s order by sortId".format(config.TABLENAME5),[reportDBId,1])
          if len(componentIdlist) == 0:
            return jsonify({
              "code": 1,
              "msg": "获取的数据为空值！"
            })
          else:
            return_data = []

            for i in componentIdlist:
              componentmsg = {}
              componentmsg["id"] = i["componentId"]
              if conn.query_one("select jsonstr from {} where id=%s".format(config.TABLENAME3), [i["componentId"]])["jsonstr"]:
                  componentmsg["jsonstr"] = conn.query_one("select jsonstr from {} where id=%s".format(config.TABLENAME3), [i["componentId"]])["jsonstr"]
              else:
                  componentmsg["jsonstr"]=""
              componentmsg["jsonstr"] = conn.query_one("select jsonstr from {} where id=%s".format(config.TABLENAME3), [i["componentId"]])["jsonstr"]
              componentmsg["size"] = i["size"]
              return_data.append(componentmsg)
            return jsonify({
              "code": 1,
              "msg": return_data
            })
        else:
          return jsonify({
            "code": 1,
            "msg": []
          })
    except Exception as e:
      raise e


# http://120.31.140.112:8080/componentManagement//quota/queryByOverviewId  通过报表id获取模板图列表(指标组件)
@data_report.route("/quotaOverviewTemplate/", methods=["POST"])
def quotaOverviewTemplate():
    """通过报表id获取表报下的指标组件内容"""
    json_data = request.get_json()
    reportDBId = json_data["overviewId"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.WOWRKSHEET01) as cursor:
        if conn.query_all("select * from {} where reportDBId=%s and flag=%s".format(config.TABLENAME10),[reportDBId,1]):
            entityIdIdlist= conn.query_all("select *  from {} where reportDBId=%s and flag=%s order by sortId".format(config.TABLENAME10),[reportDBId,1])
            if len(entityIdIdlist) ==0 :
                return jsonify({
                    "code": 1,
                    "msg": "获取的数据为空值！"
                })
            else:
                return_data=[]
                func = lambda x: x if x else ""
                for i in entityIdIdlist:
                    entitymsg= conn.query_one("select * from {} where id=%s".format(config.TABLENAME11),[i["entityId"]])
                    entitymsg["createDate"] = entitymsg["createDate"].strftime("%Y-%m-%d %H:%M:%S")
                    entitymsg["editDate"] = entitymsg["editDate"].strftime("%Y-%m-%d %H:%M:%S")
                    entitymsg["name1"] = func(entitymsg["name1"])
                    entitymsg["name2"] = func(entitymsg["name2"])
                    entitymsg["name3"] = func(entitymsg["name3"])
                    entitymsg["name4"] = func(entitymsg["name4"])
                    entitymsg["name5"] = func(entitymsg["name5"])
                    entitymsg["reportDBId"]= i["reportDBId"]
                    entitymsg["size"] = i["size"]
                    entitymsg["sortId"] = i["sortId"]
                    entitymsg["title"] = func(entitymsg["title"])
                    entitymsg["unit1"] = func(entitymsg["unit1"])
                    entitymsg["unit2"] = func(entitymsg["unit2"])
                    entitymsg["unit3"] = func(entitymsg["unit3"])
                    entitymsg["unit4"] = func(entitymsg["unit4"])
                    entitymsg["unit5"] = func(entitymsg["unit5"])
                    entitymsg["value1"] = func(entitymsg["value1"])
                    entitymsg["value2"] = func(entitymsg["value2"])
                    entitymsg["value3"] = func(entitymsg["value3"])
                    entitymsg["value4"] = func(entitymsg["value4"])
                    entitymsg["value5"] = func(entitymsg["value5"])
                    return_data.append(entitymsg)
                return jsonify({
                    "code": 1,
                    "msg": return_data
                })
        else:
            return jsonify({
                "code": 1,
                "msg": []
            })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//quota/saveAllTemplateInReport  保存系统报表首要指标组件
@data_report.route("/savequotaTemplateInReport/", methods=["POST"])
def savequotaTemplateInReport():
    """保存系统报表首要指标组件"""
    json_data = request.get_json()
    reportDBId = json_data["reportDBId"]
    quotalist= json_data["list"]
    token= json_data["token"]
    userid= g.token["id"]
    # 随机产生id
    def randomid(num):
        lower_num = string.ascii_lowercase + string.digits
        randomstr = ""
        for i in range(num):
            randomstr += random.choice(lower_num)
        return randomstr

    now_time = datetime.datetime.now()
    createDate = now_time.strftime("%Y-%m-%d %H:%M:%S")
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.WOWRKSHEET01) as cursor:
        # 先删除后保存
        if conn.query_all("select * from {} where reportDBId=%s and flag=%s and uid=%s".format(config.TABLENAME10),[reportDBId,1,userid]):
            dellist=conn.query_all("select * from {} where reportDBId=%s and flag=%s and uid=%s".format(config.TABLENAME10),[reportDBId,1,userid])
            for j in dellist:
                conn.update("update {} set flag=%s where id=%s".format(config.TABLENAME10),[0,j["id"]])
            conn.commit()

        for i in quotalist:
            sortid= quotalist.index(i)+1
            entityId= i["entityId"]
            uid= i["uid"]
            id = randomid(8) + token[8:24] + randomid(12)
            size= "中"
            flag= 1
            conn.insert_one("insert into {} (id,entityId,uid, reportDBId,size,sortId,createDate,editDate,flag) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(
                config.TABLENAME10),[id, entityId,uid,reportDBId,size,sortid,createDate,createDate,flag])
      return jsonify({
          "code": 1,
          "msg": "保存系统首要指标组件成功"
      })

    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//dataOverviewTemplate/saveAllTemplateInReport  保存系统报表图表业务组件内容
@data_report.route("/savecomponentTemplateInReport/", methods=["POST"])
def savecomponentTemplateInReport():
    """保存系统报表图标业务组件"""
    json_data = request.get_json()
    reportDBId = json_data["reportDBId"]
    componentlist= json_data["list"]
    token= json_data["token"]
    uid= g.token["id"]

    # 随机产生id
    def randomid(num):
        lower_num = string.ascii_lowercase + string.digits
        randomstr = ""
        for i in range(num):
            randomstr += random.choice(lower_num)
        return randomstr

    now_time = datetime.datetime.now()
    createDate = now_time.strftime("%Y-%m-%d %H:%M:%S")
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.WOWRKSHEET01) as cursor:
        # 先删除后保存
        if conn.query_all("select * from {} where reportDBId=%s and flag=%s and uid=%s".format(config.TABLENAME5),
                        [reportDBId, 1, uid]):
          dellist = conn.query_all(
              "select * from {} where reportDBId=%s and flag=%s and uid=%s".format(config.TABLENAME5),
              [reportDBId, 1, uid])
          for j in dellist:
              conn.update("update {} set flag=%s where id=%s".format(config.TABLENAME5), [0, j["id"]])
          conn.commit()

        for i in componentlist:
            sortid= componentlist.index(i)+1
            componentId= i["componentId"]
            id = randomid(8) + token[8:24] + randomid(12)
            size= i["size"]
            flag= 1
            conn.insert_one("insert into {} (id,uid, reportDBId,componentId,size,sortId,createDate,editDate,flag) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(
                config.TABLENAME5),[id,uid,reportDBId,componentId,size,sortid,createDate,createDate,flag])
      return jsonify({
          "code": 1,
          "msg": "保存系统报表图表业务指标组件成功"
      })

    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement//reportDB/updateThumbnail   保存编辑报表截图
@data_report.route("/updateReportThumbnail/", methods=["POST"])
def updateReportThumbnail():
    """ 保存编辑报表截图"""
    json_data = request.get_json()
    reportDBId = json_data["id"]

    # 保存图片信息
    thumbnail = json_data["thumbnail"].split(",")[-1]
    imgdata = base64.b64decode(thumbnail)
    now_time = datetime.datetime.now()
    time01 = now_time.strftime("%Y%m%d%H%M%S")
    path01 = config.DATAREPORT01 + time01 + ".jpg"
    path = config.DATAREPORTPATH + time01 + ".jpg"
    file = open(path01, "wb")
    file.write(imgdata)
    file.close()

    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.WOWRKSHEET01) as cursor:
        conn.update("update {} set thumbnail=%s where id=%s".format(config.TABLENAME9),[path,reportDBId])
      return jsonify({
          "code": 1,
          "msg":"更新报表截图成功"
      })
    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement//comm/imgFlowDownload 下载报表截图图片
@data_report.route('/imgFlowDownload/',methods=['POST'])
def imgFlowDownload():
  json_data = request.get_json()
  thumbnail = json_data["thumbnail"].split(",")[-1]
  imgdata = base64.b64decode(thumbnail)

  return Response(imgdata, mimetype="application/octet-stream;charset=utf-8")


# http://120.31.140.112:8080/componentManagement//comm/view_report_style/listAll  获取报表风格
@data_report.route("/getreportstyles/", methods=["POST"])
def getreportstyles():
    """获取报表风格"""
    json_data = request.get_json()
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.WOWRKSHEET01) as cursor:
        reportstylelist= conn.query_all("select * from {}".format(config.TABLENAME24))

      return jsonify({
          "code": 1,
          "data": reportstylelist
      })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//reportDB/updateStyle  修改保存报表风格
@data_report.route("/updateReportStyle/", methods=["POST"])
def updateReportStyle():
    """修改保存报表风格"""
    json_data = request.get_json()
    reportDBId = json_data["id"]
    reportType= json_data["reportType"]
    styleId= json_data["styleId"]
    styleObj= json_data["styleObj"]
    now_time = datetime.datetime.now()
    editDate = now_time.strftime("%Y-%m-%d %H:%M:%S")

    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.WOWRKSHEET01) as cursor:
          if styleId=="":
              conn.update("update {} set reportType=%s,styleObj=%s,editDate=%s where id=%s".format(
                  config.TABLENAME9), [reportType, styleObj, editDate, reportDBId])
          else:
              conn.update("update {} set reportType=%s,styleId=%s,styleObj=%s,editDate=%s where id=%s".format(config.TABLENAME9),[reportType,styleId,styleObj,editDate,reportDBId])
      return jsonify({
          "code": 1,
          "msg": "修改保存报表风格成功"
      })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement/pushReport/getAllReportByUidAndType  获取用户报表信息
@data_report.route("/getAllReportByUidAndType/", methods=["POST"])
def getAllReportByUidAndType():
    """获取用户报表信息"""
    """前端用户参数type(报表类型参数没用到)"""
    json_data = request.get_json()
    reportType= json_data["type"]
    uid= g.token["id"]
    flag= 1
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.WOWRKSHEET01) as cursor:
        if conn.query_all("select * from {} where uid=%s and flag=%s".format(config.TABLENAME9),[uid, flag]):
            reportmsglist= conn.query_all("select * from {} where uid=%s and flag=%s".format(config.TABLENAME9),[uid, flag])
            return_data=[]
            for i in reportmsglist:
                reportmsgdic={}
                reportmsgdic["createDate"]=i["createDate"].strftime("%Y-%m-%d %H:%M:%S")
                reportmsgdic["id"]= i["id"]
                reportmsgdic["name"]= i["name"]
                return_data.append(reportmsgdic)
            return jsonify({
              "code": 1,
              "data": return_data
          })
        else:
            return jsonify({
                "code": -1,
                "data": "获取参数列表失败"
            })


    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement//reportDB/imgDownload  历史快照下载图片 用之前写好的接口

# http://120.31.140.112:8080/componentManagement//reportDB/get  # 信箱进模板的数据库版
@data_report.route("/getMailboxreport/", methods=["POST"])
def getMailboxreport():
    """获取信箱报表信息"""
    json_data = request.get_json()
    reportid= json_data["id"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.WOWRKSHEET01) as cursor:
          if conn.query_one("select createDate,editDate,flag,id,name,styleId,thumbnail,uid from {} where id=%s".format(config.TABLENAME9),[reportid]):
              reportmsg= conn.query_one("select createDate,editDate,flag,id,name,styleId,thumbnail,uid from {} where id=%s".format(config.TABLENAME9),[reportid])
              reportmsg["createDate"]= int(time.mktime(reportmsg["createDate"].timetuple()))
              reportmsg["editDate"] = int(time.mktime(reportmsg["editDate"].timetuple()))
              reportmsg["styleId"] = str(reportmsg["styleId"])
              return jsonify({
                "code": 1,
                "data": reportmsg
             })
          else:
             return jsonify({
                "code": -1,
                "data": "获取信箱报表信息失败"
            })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//pushReport/getPrivilege  获取报表配置信息
@data_report.route("/getPrivilege/", methods=["POST"])
def getPrivilege():
    """获取报表配置信息"""
    json_data = request.get_json()
    pushReportId= json_data["pushReportId"]
    func = lambda x: x if x else ""
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.WOWRKSHEET01) as cursor:
          if conn.query_one("select * from {} where push_report_id=%s".format(config.TABLENAME28),[pushReportId]):
              pushreportmsg={}
              pushReportIdmsg= conn.query_one("select * from {} where push_report_id=%s".format(config.TABLENAME28),[pushReportId])
              pushreportmsg["flag"]= pushReportIdmsg["flag"]
              pushreportmsg["id"]= str(pushReportIdmsg["id"])
              pushreportmsg["pushAgain"]= pushReportIdmsg["push_again"]
              pushreportmsg["pushReportId"]= pushReportIdmsg["push_report_id"]
              pushreportmsg["readDelete"]= pushReportIdmsg["read_delete"]
              pushreportmsg["watermarkIs"]= pushReportIdmsg["watermark_is"]
              pushreportmsg["watermarkStr"]= func(pushReportIdmsg["watermark_str"])
              return jsonify({
                "code": 1,
                "data": pushreportmsg
             })
          else:
             return jsonify({
                "code": -1,
                "data": "获取报表配置信息失败"
            })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement/pushReport/burnAfterReading 信箱阅后即焚配置
@data_report.route("/burnAfterReading/", methods=["POST"])
def burnAfterReading():
    """信箱阅后即焚配置"""
    json_data = request.get_json()
    pushReportId= json_data["pushReportId"]
    try:
        conn= mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            conn.update("update {} set recipient_flag={},status={} where id=%s".format(config.TABLENAME26,0,1),[pushReportId])
            conn.update("update {} set flag={} where push_report_id=%s".format(config.TABLENAME28,0),[pushReportId])
        return jsonify({
            "code": 1,
            "data": True
           })

    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//analysisReport/listAllByUid 获取分析报告列表
@data_report.route("/analysisReportlistAll/", methods=["POST"])
def analysisReportlistAll():
    """获取分析报告列表"""
    json_data = request.get_json()
    uid= g.token["id"]
    groupid= json_data["groupid"]
    flag= 1
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.WOWRKSHEET01) as cursor:
          if conn.query_all("select * from {} where uid=%s and flag=%s and groupid=%s order by createDate DESC".format(config.TABLENAME27),[uid,flag,groupid]):
              analysisReportlist = conn.query_all("select * from {} where uid=%s and flag=%s and groupid=%s order by createDate DESC".format(config.TABLENAME27),[uid,flag,groupid])
              return_data=[]
              for i in analysisReportlist:
                  i["createDate"]= int(time.mktime(i["createDate"].timetuple()))
                  i["editDate"]=datetime.datetime.now()
                  return_data.append(i)
              return Response(json.dumps({"code": 1, "data": [return_data]}, cls=DateEncoder), mimetype='application/json')
             #  return jsonify({
             #    "code": 1,
             #    "data": return_data
             # })

          else:
             return jsonify({
                "code": 1,
                "data": []
            })
    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement//analysisReport/del 删除分析报告
@data_report.route("/delanalysisReport/", methods=["POST"])
def delanalysisReport():
    """删除分析报告"""
    json_data = request.get_json()
    ids= json_data["ids"]
    try:
        conn= mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            for i in ids:
                conn.update("update {} set flag={} where id=%s".format(config.TABLENAME27,0),[i])
        return jsonify({
            "code": 1,
            "data": "删除分析报告成功"
           })

    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//analysisReport/getAllReportPartById   获取分析报告内容
@data_report.route("/getanalysisReportContent/", methods=["POST"])
def getanalysisReportContent():
    """获取分析报告内容"""
    json_data = request.get_json()
    analysisReportid= json_data["id"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.WOWRKSHEET01) as cursor:
          themeDate=[]
          if conn.query_all("select id,title_name,chart_ids from {} where analysis_report_id= %s and flag=%s".format(config.TABLENAME30),[analysisReportid,1]):
              analysisReport= conn.query_one("select styleId,name from {} where id=%s and flag=%s".format(config.TABLENAME27),[analysisReportid,1])
              #  添加新字段 sortid 主题排序
              reportpartlist= conn.query_all("select id,title_name,chart_ids from {} where analysis_report_id= %s and flag=%s order by sortid".format(config.TABLENAME30),[analysisReportid,1])
              for i in reportpartlist:
                  themedic={}
                  themedic["id"]= i["id"]
                  themedic["title_name"]= i["title_name"]
                  bigAdd = []
                  for j in list(i["chart_ids"].split(",")):
                      zujianmsg= conn.query_one("select id,jsonstr from {} where id= %s".format(config.TABLENAME3),[j])
                      bigAdd.append(zujianmsg)
                  themedic["bigAdd"]= bigAdd
                  if conn.query_all("select id,descriptions from {} where analysis_report_part_id=%s".format(config.TABLENAME31),i["id"])==0:
                      themedic["descriptions"]=[]
                  else:
                      themedic["descriptions"]= conn.query_all("select id,descriptions from {} where analysis_report_part_id=%s".format(config.TABLENAME31),i["id"])

                  themeDate.append(themedic)
                  analysisReport["themeData"]= themeDate
          else:
               analysisReport = []
      return jsonify({
          "code": 1,
          "data": analysisReport
      })

    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement//analysisReport/save 保存分析报告内容
@data_report.route("/saveAnalysisReport/", methods=["POST"])
def saveAnalysisReport():
    """保存分析报告内容数据库"""
    json_data = request.get_json()
    front_id= json_data["id"]   #判断前端是否传过来id  为 "" 表示新建 修改为id
    name= json_data["name"]
    path= json_data["path"]
    styleId= json_data["styleId"]
    uid= g.token["id"]
    token= json_data["token"]

    themeData= json_data["themeData"]
    now_time = datetime.datetime.now()
    createDate = now_time.strftime("%Y-%m-%d %H:%M:%S")
    time_01 = now_time.strftime("%Y%m%d%H%M%S")
    thumbnail = json_data["thumbnail"].split(",")[-1]
    imgdata = base64.b64decode(thumbnail)
    path01 = config.ANALYSISREPORT01 + time_01 + ".jpg"
    serverpath = config.ANALYSISREPORTPATH + time_01 + ".jpg"
    file = open(path01, "wb+")
    file.write(imgdata)
    file.close()
    flag= 1
    groupid= json_data["groupid"]

    def randomid(num):
        lower_num = string.ascii_lowercase + string.digits
        randomstr = ""
        for i in range(num):
            randomstr += random.choice(lower_num)
        return randomstr

    id = randomid(8) + token[8:24] + randomid(12)
    datapath= path + id
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if front_id == "":
                conn.insert_one("insert into {} (id, uid,groupid,name,path,thumbnail,styleId,createDate,flag) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(
                    config.TABLENAME27),[id,uid,groupid,name,datapath,serverpath,styleId,createDate,flag])
                conn.commit()
                for i in themeData:
                    # 主题顺序
                    sortid= themeData.index(i)+1
                    analysis_report_part_id= randomid(8) + token[8:24] + randomid(12)
                    conn.insert_one("insert into {} (id,analysis_report_id,title_name,chart_ids,sortid,flag) values (%s,%s,%s,%s,%s,%s)".format(
                        config.TABLENAME30),[analysis_report_part_id,id,i["titleName"],i["chartIds"],sortid,flag])
                    analysis_report_part_descriptions_id= analysis_report_part_id[:-12] + randomid(12)
                    if i["descriptions"]==[]:
                        pass
                    else:
                        conn.insert_one("insert into {} (id,analysis_report_part_id,descriptions,sortid,flag) values (%s,%s,%s,%s,%s)".format(config.TABLENAME31),
                                        [analysis_report_part_descriptions_id,analysis_report_part_id,i["descriptions"],sortid,flag])
                return jsonify({
                    "code": 1,
                    "data": id
                })
            else:
                # print("进入分析报告修改程序----")
                conn.update("update {} set name=%s, path=%s, thumbnail=%s, styleId=%s where id=%s and uid=%s and flag=%s".format(
                        config.TABLENAME27), [ name, datapath, serverpath, styleId,front_id,uid,1])
                conn.update("update {} set flag=%s where analysis_report_id=%s and flag=%s".format(config.TABLENAME30),[0,front_id,1])
                conn.commit()
                for i in themeData:
                    sortid = themeData.index(i) + 1
                    analysis_report_part_id = randomid(8) + token[8:24] + randomid(12)
                    conn.insert_one("insert into {} (id,analysis_report_id,title_name,chart_ids,sortid,flag) values (%s,%s,%s,%s,%s,%s)".format(config.TABLENAME30),[analysis_report_part_id,front_id,i["titleName"],i["chartIds"],sortid,1])
                    conn.commit()
                    part_id= conn.query_one("select id from {} where analysis_report_id=%s and flag=%s".format(config.TABLENAME30),[front_id,1])
                    if i["descriptions"]==[]:
                        pass
                    else:
                        conn.update("update {} set flag=%s where analysis_report_part_id=%s and flag=%s".format(config.TABLENAME31),[0,part_id["id"],1])
                        if conn.query_one("select * from {} where analysis_report_part_id=%s and flag=%s".format(config.TABLENAME31),[part_id["id"],1])==0:
                            analysis_report_part_descriptions_id= part_id["id"][:-12] + randomid(12)
                            conn.insert_one("insert into {} (id,analysis_report_part_id,descriptions,sortid,flag) values (%s,%s,%s,%s,%s)".format(
                                config.TABLENAME31),[analysis_report_part_descriptions_id, part_id["id"], i["descriptions"],sortid,1])
                        else:
                            conn.update("update {} set descriptions=%s where analysis_report_part_id=%s and flag=%s".format(config.TABLENAME31),[i["descriptions"],part_id["id"],1])
                return jsonify({
                    "code": 1,
                    "data": front_id
                })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//reportExcel/listAll 查询reportExcel表
@data_report.route("/reportExcellistAll/", methods=["POST"])
def reportExcellistAll():
    """获取reportExcel列表"""
    json_data = request.get_json()
    uid= g.token["id"]
    flag= 1
    try:
      conn= mysqlpool.get_conn()
      func = lambda x: x if x else ""
      with conn.swich_db(config.WOWRKSHEET01) as cursor:
          if conn.query_all("select * from {} where uid=%s and flag=%s order by createDate DESC".format(config.TABLENAME41),[uid,flag]):
              analysisReportlist = conn.query_all("select * from {} where uid=%s and flag=%s order by createDate DESC".format(config.TABLENAME41),[uid,flag])
              return_data=[]
              for i in analysisReportlist:
                  i["createDate"]= i["createDate"].strftime("%Y-%m-%d %H:%M:%S")
                  i["styleObj"] = func(i["styleObj"])
                  return_data.append(i)
              return jsonify({
                "code": 1,
                "data": return_data
             })
          else:
             return jsonify({
                "code": -1,
                "data": "获取report_excel失败"
            })
    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement//comm/view_report_style/listAll  获取报表风格
@data_report.route("/getreportstylelistAll/", methods=["POST"])
def getreportstylelistAll():
    """获取报表风格"""
    json_data = request.get_json()
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.WOWRKSHEET01) as cursor:
          stylelist= conn.query_all("select * from {}".format(config.TABLENAME24))

          return jsonify({
                "code": 1,
                "data": stylelist
            })
    except Exception as e:
        raise e


# 数据报表分组接口 新增数据报表分组信息
@data_report.route("/addgroup/", methods=["POST"])
def addgroup():
    """新增数据报表分组信息"""
    json_data = request.get_json()
    groupname = json_data["groupname"]
    uid= g.token["id"]
    flag= 1
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            conn.insert_one("insert into {} (uid, groupname,flag) values (%s,%s,%s)".format(config.TABLENAME43),[uid,groupname,flag])
        return jsonify({
            "code": 1,
            "data": "新增数据报表分组成功"
        })
    except Exception as e:
        raise e

# 修改数据报表分组信息
@data_report.route("/updategroup/", methods=["POST"])
def updategroup():
    """修改数据报表分组信息"""
    json_data = request.get_json()
    id= json_data["id"]
    groupname = json_data["groupname"]
    uid= g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            conn.update("update {} set groupname=%s where id=%s and flag=%s and uid=%s".format(config.TABLENAME43),[groupname,id,1,uid])
        return jsonify({
            "code": 1,
            "data": "修改数据报表分组信息成功"
        })
    except Exception as e:
        raise e

# 删除数据报表分组信息
@data_report.route("/delgroup/", methods=["POST"])
def delgroup():
    """删除数据报表分组信息"""
    json_data = request.get_json()
    id= json_data["id"]
    flag= 0
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            conn.update("update {} set flag=%s where id=%s".format(config.TABLENAME43),[flag,id])
        return jsonify({
            "code": 1,
            "data": "删除数据表报分组信息成功"
        })
    except Exception as e:
        raise e


# 获取数据表报分组信息
@data_report.route("/queryAllgroup/", methods=["POST"])
def queryAllgroup():
    """获取数据表报分组信息"""
    json_data = request.get_json()
    flag = 1
    uid= g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if conn.query_all("select * from {} where flag=%s and uid=%s".format(config.TABLENAME43),[flag,uid]):
                dadareportlist = conn.query_all("select * from {} where flag=%s and uid=%s".format(config.TABLENAME43),[flag,uid])
            else:
                dadareportlist = []

        return jsonify({
            "code": 1,
            "data": dadareportlist
        })
    except Exception as e:
        raise e


#  新增分析报告分组信息
@data_report.route("/addAnalysisreportGroup/", methods=["POST"])
def addAnalysisreportGroup():
    """新增分析报告分组信息"""
    json_data = request.get_json()
    groupname = json_data["groupname"]
    uid= g.token["id"]
    flag= 1
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            conn.insert_one("insert into {} (uid,groupname,flag) values (%s,%s,%s)".format(config.TABLENAME44),[uid,groupname,flag])
        return jsonify({
            "code": 1,
            "data": "新增分析报告分组成功"
        })
    except Exception as e:
        raise e

# 修改分析报告分组信息
@data_report.route("/updateAnalysisreportGroup/", methods=["POST"])
def updateAnalysisreportGroup():
    """修改分析报告分组信息"""
    json_data = request.get_json()
    id= json_data["id"]
    groupname = json_data["groupname"]
    uid= g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            conn.update("update {} set groupname=%s where id=%s and uid=%s".format(config.TABLENAME44),[groupname,id,uid])
        return jsonify({
            "code": 1,
            "data": "修改分析报告分组信息成功"
        })
    except Exception as e:
        raise e

# 删除分析报告分组信息
@data_report.route("/delAnalysisreportGroup/", methods=["POST"])
def delAnalysisreportGroup():
    """删除分析报告分组信息"""
    json_data = request.get_json()
    id= json_data["id"]
    flag= 0
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            conn.update("update {} set flag=%s where id=%s".format(config.TABLENAME44),[flag,id])
        return jsonify({
            "code": 1,
            "data": "删除分析报告分组信息成功"
        })
    except Exception as e:
        raise e


# 获取分析报告分组信息
@data_report.route("/queryAllAnalysisreportGroup/", methods=["POST"])
def queryAllAnalysisreportGroup():
    """获取分析报告分组信息"""
    json_data = request.get_json()
    flag = 1
    uid= g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if conn.query_all("select * from {} where flag=%s and uid=%s ".format(config.TABLENAME44),[flag,uid]):
                dadareportlist = conn.query_all("select * from {} where flag=%s and uid=%s ".format(config.TABLENAME44),[flag,uid])
            else:
                dadareportlist=[]
            return jsonify({
                "code": 1,
                "data": dadareportlist
            })
    except Exception as e:
        raise e


# 通过分析报表id 修改组
@data_report.route("/updateGroup_analysisreportid/", methods=["POST"])
def updateGroup_analysisreportid():
    """修改分析报表组id"""
    json_data = request.get_json()
    id = json_data["id"] # 分析报表id
    groupid= json_data["groupid"]
    flag = 1
    uid= g.token["id"]

    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            conn.update("update {} set groupid=%s where id=%s and uid=%s and flag=%s".format(config.TABLENAME27),[groupid,id,uid,flag])
            return jsonify({
                "code": 1,
                "data": "修改分析报表组成功"
            })
    except Exception as e:
        raise e

# 通过数据报表id 修改组号
@data_report.route("/updateGroup_reportid/", methods=["POST"])
def updateGroup_reportid():
    """修改数据报表组id"""
    json_data = request.get_json()
    id = json_data["id"]  #   数据报表id
    groupid= json_data["groupid"]
    flag = 1
    uid= g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            conn.update("update {} set groupid=%s where id=%s and uid=%s and flag=%s".format(config.TABLENAME9),[groupid,id,uid,flag])
            return jsonify({
                "code": 1,
                "data": "修改数据报表成功"
            })
    except Exception as e:
        raise e
