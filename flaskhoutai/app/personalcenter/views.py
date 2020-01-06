from flask import Blueprint, request, jsonify, Response,g
from utils.dbutils import mysqlpool
from instance import config
import datetime, requests,json
import base64,time
import random, string
from utils.json_helper import DateEncoder

# 创建数据报表应用蓝图
personalcenter = Blueprint("personalcenter", __name__)

# http://120.31.140.112:8080/componentManagement//pushReport/getUnreadCount
# http://120.31.140.112:8080/componentManagement//user/getDepartments  获取推送部门
@personalcenter.route("/getpushDepartments/", methods=["POST"])
def getpushDepartments():
    """获取推送部门"""
    json_data = request.get_json()
    try:
        conn= mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            departmentslist= conn.query_all("select * from {}".format(config.TABLENAME21))
            for i in departmentslist:
                i["createDate"] = int(time.mktime(i["createDate"].timetuple()))
                i["editDate"] = int(time.mktime(i["editDate"].timetuple()))
        return jsonify({
            "code": 1,
            "data": departmentslist
           })

    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement//user/getUserByDepartmentID  获取部门下相关推送人
@personalcenter.route("/getUserByDepartmentID/", methods=["POST"])
def getUserByDepartmentID():
    """获取推送部门下推送人"""
    json_data = request.get_json()
    departmentID= json_data["departmentID"]
    try:
        conn= mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            Userlist = []
            if len(conn.query_all("select * from {} where DepartmentID= %s".format(config.TABLENAME16),[departmentID]))> 0:
                func = lambda x: x if x else ""
                departmentsUserlist= conn.query_all("select * from {} where DepartmentID= %s".format(config.TABLENAME16),[departmentID])
                for i in departmentsUserlist:
                    usermsgdic={}
                    usermsgdic["createDate"]= int(time.mktime(i["createDate"].timetuple()))
                    usermsgdic["departmentID"]= i["DepartmentID"]
                    usermsgdic["editDate"] = int(time.mktime(i["editDate"].timetuple()))
                    usermsgdic["email"] = func(i["Email"])
                    usermsgdic["flag"] = i["flag"]
                    usermsgdic["id"] = i["id"]
                    usermsgdic["mobile"]= i["Mobile"]
                    usermsgdic["password"]= i["Password"]
                    usermsgdic["realName"]= i["RealName"]
                    usermsgdic["remark"] = func(i["remark"])
                    usermsgdic["roleID"] = i["RoleID"]
                    usermsgdic["status"]= i["status"]
                    usermsgdic["token"]=""
                    usermsgdic["userName"]= i["UserName"]
                    Userlist.append(usermsgdic)
        return jsonify({
            "code": 1,
            "data": Userlist
           })

    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement/pushReport/save/  保存推送内容
@personalcenter.route("/reportPushSave/", methods=["POST"])
def reportPushSave():
    """保存推送内容"""
    json_data = request.get_json()
    departmentId= json_data["departmentId"]
    departmentName= json_data["departmentName"]
    pushAgain= json_data["pushAgain"]
    pushExplain= json_data["pushExplain"]
    readDelete= json_data["readDelete"]
    recipientId= json_data["recipientId"]
    recipientName= json_data["recipientName"]
    reportExplain= json_data["reportExplain"]
    reportId= json_data["reportId"]
    reportName= json_data["reportName"]
    reportType= json_data["reportType"]
    watermarkIs=json_data["watermarkIs"]
    watermarkStr= json_data["watermarkStr"]
    token = json_data["token"]
    uid= g.token["id"]
    sender_flag = 1
    recipient_flag = 1
    status = 0
    flag= 1
    # 随机产生id
    def randomid(num):
        lower_num = string.ascii_lowercase + string.digits
        randomstr = ""
        for i in range(num):
            randomstr += random.choice(lower_num)
        return randomstr
    try:
        conn= mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
           id = randomid(8) + token[8:24] + randomid(12)
           now_time = datetime.datetime.now()
           createDate = now_time.strftime("%Y-%m-%d %H:%M:%S")
           conn.insert_one("insert into {} (id,uid,report_id,report_type,report_name,report_explain,department_id,department_name,recipient_id,recipient_name,push_explain,createDate,sender_flag,recipient_flag,status) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(
               config.TABLENAME26),[id,uid,reportId,reportType,reportName,reportExplain,departmentId,departmentName,recipientId,recipientName,pushExplain,createDate,sender_flag,recipient_flag,status])
           conn.insert_one("insert into {} (push_report_id,push_again,watermark_is,watermark_str,read_delete,flag) values (%s,%s,%s,%s,%s,%s)".format(
               config.TABLENAME28),[id,pushAgain,watermarkIs,watermarkStr,readDelete,flag])
        return jsonify({
            "code": 1,
            "msg": "保存推送内容成功"
           })

    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//pushReport/querySenderReports  # 推送数据模糊查询
@personalcenter.route("/querylikeSenderReports/", methods=["POST"])
def querylikeSenderReports():
    """推送数据模糊查询"""
    json_data = request.get_json()
    endDate00= json_data["endDate"]
    page= json_data["page"]
    if page =={'isTrusted': True}:
        page=1
    recipientName= json_data["recipientName"]
    reportName= json_data["reportName"]
    requestType= json_data["requestType"]
    rows= json_data["rows"]
    startDate00= json_data["startDate"]
    uid= g.token["id"]

    likecondition= ""
    if reportName != "":
        likecondition=likecondition+ " and  a.report_name like '%" +reportName+"%'"
    if recipientName != "":
        likecondition= likecondition + " and a.recipient_name='"+ recipientName + "' "
    if requestType != "":
        likecondition= likecondition + " and a.report_type=" + str(requestType) + ""
    if startDate00 != "" and endDate00 != "":
        endDate = endDate00.replace(endDate00.split("-")[-1], str(int(endDate00.split("-")[-1]) + 1)) + " 0:0:0"
        startDate = json_data["startDate"] + " 0:0:0"
        likecondition = likecondition + " and (a.createDate Between '%s' and '%s' )"%(datetime.datetime.strptime(startDate,'%Y-%m-%d %H:%M:%S'),datetime.datetime.strptime(endDate,'%Y-%m-%d %H:%M:%S'))

    try:
        conn= mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
           if not conn.query_all("select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name, a.report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where uid={uid} {likecondition} order by a.createDate DESC".format(tableA=config.TABLENAME26,tableB=config.TABLENAME28,uid=uid,likecondition=likecondition)):
               return jsonify({
                   "code": 1,
                   "data": {
                       "page": page,
                       "rows": [],
                       "total": 0
                   }
               })
           senderreportlist= conn.query_all("select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name, report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where uid={uid} {likecondition} order by a.createDate DESC".format(tableA=config.TABLENAME26,tableB=config.TABLENAME28,uid=uid,likecondition=likecondition))
           # 总数量
           count = len(senderreportlist)
           # 总页数
           pages = count // rows if count % rows == 0 else count // rows + 1
           # 总数量 大于 每页数量 但页码为一 显示第一页内容
           if rows <= count and page == 1:
               senderreportlist = conn.query_all(
                   "select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,"
                   " a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name,"
                   " a.report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where uid={uid} {likecondition} order by a.createDate DESC LIMIT %s".format(
                       tableA=config.TABLENAME26, tableB=config.TABLENAME28,uid=uid,likecondition=likecondition), [rows])
           elif rows > count and page == 1:
               senderreportlist = conn.query_all("select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,"
                                            " a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name,"
                                            " a.report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where uid={uid} {likecondition} order by a.createDate DESC".format(tableA=config.TABLENAME26,tableB=config.TABLENAME28,uid=uid,likecondition=likecondition))
           elif count > rows and 1 < page <= pages:
               senderreportlist = conn.query_all(
                   "select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,"
                   " a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name,"
                   " a.report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where uid={uid} {likecondition} order by a.createDate DESC LIMIT %s,%s ".format(
                       tableA=config.TABLENAME26, tableB=config.TABLENAME28,uid=uid,likecondition=likecondition), [uid, (page - 1) * rows,rows])

           for i in senderreportlist:
             i["createDate"]= i["createDate"].strftime("%Y-%m-%d %H:%M:%S")
             reportid= i["report_id"]
             if conn.query_one("select thumbnail,flag from {} where id=%s".format(config.TABLENAME9),[reportid]):
                 reportmsg = conn.query_one("select thumbnail,flag from {} where id=%s".format(config.TABLENAME9),
                                            [reportid])
                 i["thumbnail"] = reportmsg["thumbnail"]
                 i["reportFlag"] = reportmsg["flag"]
             else:
                 i["thumbnail"] = ""
                 i["reportFlag"] = 0
        return jsonify({
            "code": 1,
            "data": {
                "page":page,
                "rows":senderreportlist,
                "total":count
            }
           })
    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement//comm/view_push_type/listAll  获取推送类型
@personalcenter.route("/getpushMailtype/", methods=["POST"])
def getpushMailtype():
    """获取推送信息类型"""
    json_data = request.get_json()
    try:
        conn= mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            pushMailtypelist= conn.query_all("select * from {}".format(config.TABLENAME32))
        return jsonify({
            "code": 1,
            "data": pushMailtypelist
           })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//pushReport/delSelectRecipientReports  删除信箱报告
@personalcenter.route("/delSelectRecipientReports/", methods=["POST"])
def delSelectRecipientReports():
    """删除信箱报告"""
    json_data = request.get_json()
    recipientReportsids= json_data["ids"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
        for i in recipientReportsids:
          conn.update("update {} set recipient_flag={} where id=%s".format(config.TABLENAME26,0),[i])
      return jsonify({
          "code": 1,
          "msg": "删除信箱报告"
      })
    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement//pushReport/queryRecipientReports  信箱模糊查询
@personalcenter.route("/querylikeRecipientReports/", methods=["POST"])
def querylikeRecipientReports():
    """信箱模糊查询"""
    json_data = request.get_json()
    endDate00= json_data["endDate"]
    page= json_data["page"]
    if page =={'isTrusted': True}:
        page=1
    reportName= json_data["reportName"]
    requestType= json_data["requestType"]
    rows= json_data["rows"]
    senderName= json_data["senderName"]
    startDate00 = json_data["startDate"]
    recipient_id= g.token["id"]
    likecondition= ""
    if reportName != "":
        likecondition=likecondition+ " and  a.report_name like '%" +reportName+"%'"
    if startDate00 != "" and endDate00 != "":
        startDate = json_data["startDate"] + " 0:0:0"
        endDate = endDate00.replace(endDate00.split("-")[-1], str(int(endDate00.split("-")[-1]) + 1)) + " 0:0:0"
        likecondition = likecondition + " and (a.createDate Between '%s' and '%s' )"%(datetime.datetime.strptime(startDate,'%Y-%m-%d %H:%M:%S'),datetime.datetime.strptime(endDate,'%Y-%m-%d %H:%M:%S'))
    try:
        conn= mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
           userlist= conn.query_all("select id,UserName from {}".format(config.TABLENAME16))
           userid_username={}
           username_userid= {}
           recipient_flag= 1
           sender_flag =1
           for j in userlist:
               userid_username[j["id"]]=j["UserName"]
               username_userid[j["UserName"]]= j["id"]
           if senderName != "":
               likecondition= likecondition + " and a.uid='"+ username_userid[senderName] + "' "
           if not conn.query_all("select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name, a.report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where a.recipient_id={recipient_id} and a.recipient_flag={recipient_flag} and a.sender_flag={recipient_flag} {likecondition} order by a.createDate DESC".format(
                   tableA=config.TABLENAME26,tableB=config.TABLENAME28,recipient_id=recipient_id,recipient_flag=recipient_flag,sender_flag=sender_flag,likecondition=likecondition)):
               return jsonify({
                   "code": 1,
                   "data": {
                       "page": page,
                       "rows": [],
                       "total": 0
                   }
               })
           senderreportlist= conn.query_all("select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name, report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where a.recipient_id={recipient_id} and a.recipient_flag={recipient_flag} and a.sender_flag={sender_flag} {likecondition} order by a.createDate DESC".format(
               tableA=config.TABLENAME26,tableB=config.TABLENAME28,recipient_id=recipient_id,recipient_flag=recipient_flag,sender_flag=sender_flag,likecondition=likecondition))

           # 总数量
           count = len(senderreportlist)
           # 总页数
           pages = count // rows if count % rows == 0 else count // rows + 1
           func = lambda x: x if x else ""
           # 总数量 大于 每页数量 但页码为一 显示第一页内容
           if rows <= count and page == 1:
               senderreportlist = conn.query_all(
                   "select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,"
                   " a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name,"
                   " a.report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where a.recipient_id={recipient_id} and a.recipient_flag={recipient_flag} and a.sender_flag={sender_flag} {likecondition} order by a.createDate DESC LIMIT {rows}".format(
                       tableA=config.TABLENAME26, tableB=config.TABLENAME28,recipient_id=recipient_id,recipient_flag=recipient_flag,sender_flag=sender_flag,likecondition=likecondition,rows=rows))
           elif rows > count and page == 1:
               senderreportlist = conn.query_all("select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,"
                                            " a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name,"
                                            " a.report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where a.recipient_id={recipient_id} and a.recipient_flag={recipient_flag} and a.sender_flag={sender_flag} {likecondition} order by a.createDate DESC".format(
                   tableA=config.TABLENAME26,tableB=config.TABLENAME28,recipient_id=recipient_id,recipient_flag=recipient_flag,sender_flag=sender_flag,likecondition=likecondition))
           elif count > rows and 1 < page <= pages:
               senderreportlist = conn.query_all(
                   "select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,"
                   " a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name,"
                   " a.report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where a.recipient_id={recipient_id} and a.recipient_flag={recipient_flag} and a.sender_flag={sender_flag} {likecondition} order by a.createDate DESC LIMIT {rows01},{rows} ".format(
                       tableA=config.TABLENAME26, tableB=config.TABLENAME28,recipient_id=recipient_id,recipient_flag=recipient_flag,sender_flag=sender_flag,likecondition=likecondition,rows01=(page - 1) * rows,rows=rows))

           for i in senderreportlist:
             i["UserName"]=userid_username[i["uid"]]
             i["createDate"]= i["createDate"].strftime("%Y-%m-%d %H:%M:%S")
             reportid= i["report_id"]
             # 通过判断 push_id 判断是否为收藏
             uid = g.token["id"]
             if conn.query_all("select * from {} where uid=%s and flag=%s and push_id=%s".format(config.TABLENAME34),
                               [uid, 1, i["id"]]):
                 i["push_id"] = i["id"]
             else:
                 i["push_id"] = ""

             i["report_explain"] = func(i["report_explain"])
             if conn.query_one("select thumbnail,flag from {} where id=%s".format(config.TABLENAME9),[reportid]):
                 reportmsg = conn.query_one("select thumbnail,flag from {} where id=%s".format(config.TABLENAME9),
                                            [reportid])
                 i["thumbnail"] = func(reportmsg["thumbnail"])
                 i["reportFlag"] = reportmsg["flag"]
             else:
                 i["thumbnail"] = ""
                 i["reportFlag"] = 0
        return jsonify({
            "code": 1,
            "data": {
                "page":page,
                "rows":senderreportlist,
                "total":count
            }
           })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//pushReport/readPushReport 点击信箱变已读
@personalcenter.route("/readPushReport/", methods=["POST"])
def readPushReport():
    """点击信箱已读"""
    json_data = request.get_json()
    readPushReportid= json_data["id"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
          conn.update("update {} set status={} where id=%s".format(config.TABLENAME26,1),[readPushReportid])
      return jsonify({
          "code": 1,
          "msg": "信箱已读"
      })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//collection/query 收藏列表
@personalcenter.route("/querycollection/", methods=["POST"])
def querycollection():
    """收藏列表"""
    json_data = request.get_json()
    endDate00= json_data["endDate"]
    page= json_data["page"]
    if page =={'isTrusted': True}:
        page=1
    reportName= json_data["reportName"]
    requestType= json_data["requestType"]
    rows= json_data["rows"]
    senderName= json_data["senderName"]
    startDate00 = json_data["startDate"]
    uid= g.token["id"]
    flag = 1
    likecondition= ""
    if reportName != "":
        likecondition=likecondition+ " and  a.report_name like '%" +reportName+"%'"

    if startDate00 != "" and endDate00 != "":
        startDate = json_data["startDate"] + " 0:0:0"
        endDate = endDate00.replace(endDate00.split("-")[-1], str(int(endDate00.split("-")[-1]) + 1)) + " 0:0:0"
        likecondition = likecondition + " and (a.createDate Between '%s' and '%s' )"%(datetime.datetime.strptime(startDate,'%Y-%m-%d %H:%M:%S'),datetime.datetime.strptime(endDate,'%Y-%m-%d %H:%M:%S'))
    try:
        conn= mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
           userlist= conn.query_all("select id,UserName from {}".format(config.TABLENAME16))
           userid_username={}
           username_userid= {}
           for j in userlist:
               userid_username[j["id"]]=j["UserName"]
               username_userid[j["UserName"]]= j["id"]
           if senderName != "":
               likecondition = likecondition + " and a.uid='" + username_userid[senderName] + "' "

           if not conn.query_all("select b.createDate,b.department_id,b.department_name,b.id,b.push_explain,a.push_id,b.recipient_flag,b.recipient_id,b.recipient_name,b.report_explain,b.report_id,b.report_name,b.report_type,b.sender_flag,b.status,b.uid from {tableA} as a left join {tableB} as b on a.push_id= b.id where a.uid={uid} and a.flag={flag} {likecondition} order by a.createDate DESC".format(
                tableA=config.TABLENAME34,tableB=config.TABLENAME26,uid=uid,flag=flag,likecondition=likecondition)):
               return jsonify({
                   "code": 1,
                   "data": {
                       "page": page,
                       "rows": [],
                       "total": 0
                   }
               })
           collectionlist= conn.query_all("select b.createDate,b.department_id,b.department_name,b.id,b.push_explain,a.push_id,b.recipient_flag,b.recipient_id,b.recipient_name,b.report_explain,b.report_id,b.report_name,b.report_type,b.sender_flag,b.status,b.uid from {tableA} as a left join {tableB} as b on a.push_id= b.id where a.uid={uid} and a.flag={flag} {likecondition} order by a.createDate DESC".format(
                tableA=config.TABLENAME34,tableB=config.TABLENAME26,uid=uid,flag=flag,likecondition=likecondition))
           # 总数量
           count = len(collectionlist)
           # 总页数
           pages = count // rows if count % rows == 0 else count // rows + 1
           func = lambda x: x if x else ""
           # 总数量 大于 每页数量 但页码为一 显示第一页内容
           if rows <= count and page == 1:
               collectionlist = conn.query_all(
                   "select b.createDate,b.department_id,b.department_name,b.id,b.push_explain,a.push_id,b.recipient_flag,b.recipient_id,b.recipient_name,b.report_explain,b.report_id,b.report_name,b.report_type,b.sender_flag,b.status,b.uid from {tableA} as a left join {tableB} as b on a.push_id= b.id where a.uid={uid} and a.flag={flag} {likecondition} order by a.createDate DESC limit %s".format(
                       tableA=config.TABLENAME34, tableB=config.TABLENAME26, uid=uid, flag=flag,likecondition=likecondition),[rows])
           elif rows > count and page == 1:
               collectionlist = conn.query_all("select b.createDate,b.department_id,b.department_name,b.id,b.push_explain,a.push_id,b.recipient_flag,b.recipient_id,b.recipient_name,b.report_explain,b.report_id,b.report_name,b.report_type,b.sender_flag,b.status,b.uid from {tableA} as a left join {tableB} as b on a.push_id= b.id where a.uid={uid} and a.flag={flag} {likecondition} order by a.createDate DESC".format(
                tableA=config.TABLENAME34,tableB=config.TABLENAME26,uid=uid,flag=flag,likecondition=likecondition))
           elif count > rows and 1 < page <= pages:
               collectionlist = conn.query_all(
                   "select b.createDate,b.department_id,b.department_name,b.id,b.push_explain,a.push_id,b.recipient_flag,b.recipient_id,b.recipient_name,b.report_explain,b.report_id,b.report_name,b.report_type,b.sender_flag,b.status,b.uid from {tableA} as a left join {tableB} as b on a.push_id= b.id where a.uid={uid} and a.flag={flag} {likecondition} order by a.createDate DESC limit %s,%s".format(
                       tableA=config.TABLENAME34, tableB=config.TABLENAME26, uid=uid, flag=flag,likecondition=likecondition),[(page - 1) * rows,rows])
           for i in collectionlist:
             i["UserName"]=userid_username[i["uid"]]
             i["createDate"]= i["createDate"].strftime("%Y-%m-%d %H:%M:%S")
             reportid= i["report_id"]
             i["report_explain"] = func(i["report_explain"])
             i["short_name"]= i["department_name"]
             if conn.query_one("select thumbnail,flag from {} where id=%s".format(config.TABLENAME9),[reportid]):
                 reportmsg = conn.query_one("select thumbnail,flag from {} where id=%s".format(config.TABLENAME9),
                                            [reportid])
                 i["thumbnail"] = func(reportmsg["thumbnail"])
                 i["reportFlag"] = reportmsg["flag"]
             else:
                 i["thumbnail"] = ""
                 i["reportFlag"] = 0
        return jsonify({
            "code": 1,
            "data": {
                "page":page,
                "rows":collectionlist,
                "total":count
            }
           })

    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement//collection/save   点击收藏
@personalcenter.route("/clickCollect/", methods=["POST"])
def clickCollect():
    """点击收藏"""
    json_data = request.get_json()
    pushId= json_data["pushId"]
    uid= g.token["id"]
    token= json_data["token"]
    # 随机产生id
    def randomid(num):
        lower_num = string.ascii_lowercase + string.digits
        randomstr = ""
        for i in range(num):
            randomstr += random.choice(lower_num)
        return randomstr
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
          id = randomid(8) + token[8:24] + randomid(12)
          now_time = datetime.datetime.now()
          createDate = now_time.strftime("%Y-%m-%d %H:%M:%S")
          conn.insert_one("insert into {} (id,uid,push_id,createDate,flag) values (%s,%s,%s,%s,%s)".format(config.TABLENAME34),[id,uid,pushId,createDate,1])
      return jsonify({
          "code": 1,
          "msg": "点击收藏成功"
      })
    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement//collection/delSelectByPushId  取消收藏
@personalcenter.route("/delCollection/", methods=["POST"])
def delCollection():
    """取消收藏"""
    json_data = request.get_json()
    ids= json_data["ids"]
    uid= g.token["id"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
         for i in ids:
             conn.update("update {} set flag=%s where uid=%s and flag=%s and push_id=%s".format(config.TABLENAME34),[0,uid,1,i])
      return jsonify({
          "code": 1,
          "msg": "取消收藏成功"
      })
    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement//comm/imgDownload  下载图片 thumbnail: 图片全路径
@personalcenter.route('/imgDownload/',methods=['POST'])
def imgDownload():
  json_data = request.get_json()
  thumbnail = config.IMGROUTE_SERVER + json_data["thumbnail"]
  try:
      imagedate = requests.get(thumbnail)
      return Response(imagedate, mimetype="text/html")
      # return Response(imagedate, mimetype="application/octet-stream;charset=utf-8")
  except Exception as e:
      raise e


# http://120.31.140.112:8080/componentManagement//hardware/list 大屏资源一张图数据列表
@personalcenter.route("/hardwarelist/", methods=["POST"])
def hardwarelist():
    """大屏资源一张图数据列表"""
    json_data = request.get_json()
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
         hardware= conn.query_all("select * from {}".format(config.TABLENAME36))
      return jsonify({
          "code": 1,
          "data": hardware
      })
    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement//hardware/query  大屏资源模糊查询
@personalcenter.route("/hardwarelike/", methods=["POST"])
def hardwarelike():
    """大屏资源模糊查询"""
    json_data = request.get_json()
    name= json_data["name"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
         likename= "%"+ name +"%"
         hardware= conn.query_all("select * from {} where name like %s".format(config.TABLENAME36),[likename])
      return jsonify({
          "code": 1,
          "data": hardware
      })
    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement//hardware/getUnitByName  大屏信息
@personalcenter.route("/getUnitByName/", methods=["POST"])
def getUnitByName():
    """大屏信息查询"""
    json_data = request.get_json()
    name= json_data["name"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
          names=[]
          if conn.query_all("select a.address,a.flag,a.hbid,a.id,a.leader,a.name,a.phone,a.size from {tableA} as a left join {tableB} as b on a.hbid=b.id where b.name=%s".format(
              tableA=config.TABLENAME37,tableB=config.TABLENAME36),[name]):
              screenlist= conn.query_all("select a.address,a.flag,a.hbid,a.id,a.leader,a.name,a.phone,a.size from {tableA} as a left join {tableB} as b on a.hbid=b.id where b.name=%s".format(
                  tableA=config.TABLENAME37,tableB=config.TABLENAME36),[name])
          else:
              screenlist=[]
          for i in screenlist:
              names.append(i["name"])
      return jsonify({
          "code": 1,
          "data": {
              "names":names,
              "list":screenlist
          }
      })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//scheduling/listAppointment  预约管理列表
@personalcenter.route("/listAppointment/", methods=["POST"])
def listAppointment():
    """预约管理列表"""
    json_data = request.get_json()
    page = json_data["page"]
    total = json_data["rows"]
    flag=1
    userid = g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if conn.query_all(
                "select b.address,a.appointment_detail,a.createDate,a.editDate,a.flag,a.hardware_big_screen_resources_unit_id,a.header,a.id,b.name,a.period_p_column,a.period_p_id,a.phone,a.reception_object,a.uid,a.unit_name"
                "  from {tableA} as a left join {tableB} as b on a.hardware_big_screen_resources_unit_id=b.id where a.flag=%s and a.uid=%s order by a.createDate DESC ".format(
                    tableA=config.TABLENAME38,tableB=config.TABLENAME37),[flag,userid]):
                return_list = conn.query_all(
                    "select b.address,a.appointment_detail,a.createDate,a.editDate,a.flag,a.hardware_big_screen_resources_unit_id,a.header,a.id,b.name,a.period_p_column,a.period_p_id,a.phone,a.reception_object,a.uid,a.unit_name"
                    "  from {tableA} as a left join {tableB} as b on a.hardware_big_screen_resources_unit_id=b.id where a.flag=%s and a.uid=%s order by a.createDate DESC ".format(
                        tableA=config.TABLENAME38, tableB=config.TABLENAME37), [flag, userid]
                )
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
                    "select b.address,a.appointment_detail,a.createDate,a.editDate,a.flag,a.hardware_big_screen_resources_unit_id,a.header,a.id,b.name,a.period_p_column,a.period_p_id,a.phone,a.reception_object,a.uid,a.unit_name"
                    "  from {tableA} as a left join {tableB} as b on a.hardware_big_screen_resources_unit_id=b.id where a.flag=%s and a.uid=%s order by a.createDate DESC limit %s ".format(
                        tableA=config.TABLENAME38, tableB=config.TABLENAME37), [flag, userid,total])
            elif total > count and page == 1:
                return_list = return_list
            elif count > total and 1 < page <= pages:
                return_list = conn.query_all(
                    "select b.address,a.appointment_detail,a.createDate,a.editDate,a.flag,a.hardware_big_screen_resources_unit_id,a.header,a.id,b.name,a.period_p_column,a.period_p_id,a.phone,a.reception_object,a.uid,a.unit_name"
                    "  from {tableA} as a left join {tableB} as b on a.hardware_big_screen_resources_unit_id=b.id where a.flag=%s and a.uid=%s order by a.createDate DESC limit %s,%s ".format(
                        tableA=config.TABLENAME38, tableB=config.TABLENAME37), [flag, userid,(page - 1) * total, total])
        return_dic = {}
        returndata = []
        for i in return_list:
            returndata.append(i)
        # 返回数据
        return_dic["page"] = page
        return_dic["total"] = count
        return_dic["rows"] = returndata
        return Response(json.dumps({"code": 1, "data": return_dic}, cls=DateEncoder), mimetype='application/json')
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//scheduling/delSelectAppointment 取消预约
@personalcenter.route("/delSelectAppointment/", methods=["POST"])
def delSelectAppointment():
    """取消预约"""
    json_data = request.get_json()
    ids= json_data["ids"]
    uid= g.token["id"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
         for i in ids:
             conn.update("update {} set flag=%s where uid=%s and flag=%s and id=%s".format(config.TABLENAME38),[0,uid,1,i["id"]])
             if conn.query_one("select scheduling_id from {} where {}= %s".format(config.TABLENAME39,i["periodPColumn"]),[i["periodPId"]]):
                 scheduling_id_dic= conn.query_one("select scheduling_id from {} where {}= %s".format(config.TABLENAME39,i["periodPColumn"]),[i["periodPId"]])
                 conn.update("update {} set flag=%s where flag=%s and uid=%s and id=%s".format(config.TABLENAME40),[0,1,uid,scheduling_id_dic["scheduling_id"]])
             conn.update("update {table} set {periodPColumn}=%s where {periodPColumn}= %s".format(table=config.TABLENAME39,periodPColumn=i["periodPColumn"]),[0,i["periodPId"]])
      return jsonify({
          "code": 1,
          "msg": "取消预约成功"
      })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//scheduling/add   添加预约排期
@personalcenter.route("/addscheduling/", methods=["POST"])
def addscheduling():
    """添加预约排期"""
    json_data = request.get_json()
    appointment= json_data["appointment"]
    periodP= json_data["periodP"]
    unitId= json_data["unitId"]
    reserveForm= json_data["reserveForm"]
    uid= g.token["id"]
    token= json_data["token"]
    now_time = datetime.datetime.now()
    createDate = now_time.strftime("%Y-%m-%d %H:%M:%S")
    flag = 1

    def randomid(num):
        lower_num = string.ascii_lowercase + string.digits
        randomstr = ""
        for i in range(num):
            randomstr += random.choice(lower_num)
        return randomstr
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
          if conn.query_all("select appointment_detail from {} where hardware_big_screen_resources_unit_id=%s and flag=%s and period_p_column=%s".format(config.TABLENAME38),[unitId,flag,periodP]):
              datalist=  conn.query_all("select appointment_detail from {} where hardware_big_screen_resources_unit_id=%s and flag=%s and period_p_column=%s".format(config.TABLENAME38),[unitId,flag,periodP])
              for i in datalist:
                  if i["appointment_detail"][:10]== appointment:
                      return jsonify({
                          "code":1,
                          "msg" : "已有预约，请重新预约"
                      })
          id = randomid(8) + token[8:24] + randomid(12)
          period_p_id= randomid(8) + token[8:24] + randomid(12)
          conn.insert_one("insert into {} (id,uid,hardware_big_screen_resources_unit_id,period_p_id,period_p_column,appointment_detail,unit_name,header,phone,reception_object,createDate,editDate,flag) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(
              config.TABLENAME38),[id,uid,unitId,period_p_id,periodP,reserveForm["appointmentDetail"],reserveForm["unitName"],reserveForm["header"],reserveForm["phone"],reserveForm["receptionObject"],createDate,createDate,flag])
          schedulingid =randomid(8) + token[8:24] + randomid(12)
          conn.insert_one("insert into {} (id,uid,hardware_big_screen_resources_unit_id,appointment,className,createDate,editDate,flag) values (%s,%s,%s,%s,%s,%s,%s,%s)".format(
              config.TABLENAME40),[schedulingid,uid,unitId,appointment,"markOrange",createDate,createDate,flag])
          conn.commit()
          if conn.query_one("select * from {} where scheduling_id=%s".format(config.TABLENAME39),[schedulingid]):
              conn.update("update {} set {}=%s where scheduling_id=%s".format(config.TABLENAME39,periodP),[period_p_id,schedulingid])
          else:
              scheduling_period_id= randomid(8) + token[8:24] + randomid(12)
              if periodP =="p1":
                  insertlist=[scheduling_period_id,schedulingid,period_p_id,0,0,0]
              elif periodP == "p2":
                  insertlist = [scheduling_period_id, schedulingid,0,period_p_id,0, 0]
              elif periodP == "p3":
                  insertlist = [scheduling_period_id, schedulingid,0,0,period_p_id, 0]
              elif periodP == "p4":
                  insertlist = [scheduling_period_id, schedulingid,0,0,0,period_p_id]

              conn.insert_one("insert into {} (id,scheduling_id,p1,p2,p3,p4) values (%s,%s,%s,%s,%s,%s)".format(config.TABLENAME39),insertlist)
      return jsonify({
          "code": 1,
          "msg": "添加预约排期成功"
      })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//scheduling/getAppointmentByPeriodPId  预约时间段具体信息
@personalcenter.route("/getAppointmentByPeriodPId/", methods=["POST"])
def getAppointmentByPeriodPId():
    """预约时间段具体信息"""
    json_data = request.get_json()
    periodPId= json_data["periodPId"]
    uid= g.token["id"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
          if conn.query_one("select * from {} where uid=%s and period_p_id=%s".format(config.TABLENAME38),[uid,periodPId]):
              sellist= conn.query_one("select * from {} where uid=%s and period_p_id=%s".format(config.TABLENAME38),[uid,periodPId])
              sellist["createDate"] = int(time.mktime(sellist["createDate"].timetuple()))
              sellist["editDate"] = int(time.mktime(sellist["editDate"].timetuple()))
              sellist["unitId"]= sellist["hardware_big_screen_resources_unit_id"]
              sellist.pop("hardware_big_screen_resources_unit_id")
              return jsonify({
                  "code": 1,
                  "data": [sellist]
              })
          else:
              return jsonify({
                  "code":1,
                  "data":[]
              })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//scheduling/getSchedulingMsgById 各预约时间段信息
@personalcenter.route("/getSchedulingMsgById/", methods=["POST"])
def getSchedulingMsgById():
    """预约时间段具体信息"""
    json_data = request.get_json()
    schedulingId= json_data["schedulingId"]
    uid= g.token["id"]
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
          if conn.query_one("select * from {} where scheduling_id=%s".format(config.TABLENAME39),[schedulingId]):
              perioddic= conn.query_one("select * from {} where scheduling_id=%s".format(config.TABLENAME39),[schedulingId])
              array=[perioddic["p1"],perioddic["p2"],perioddic["p3"],perioddic["p4"]]
              appointmentlist=[]
              for i in array:
                  if i !="0":
                      sellist = conn.query_one(
                          "select * from {} where uid=%s and period_p_id=%s".format(config.TABLENAME38), [uid, i])
                      sellist["createDate"] = int(time.mktime(sellist["createDate"].timetuple()))
                      sellist["editDate"] = int(time.mktime(sellist["editDate"].timetuple()))
                      sellist["unitId"] = sellist["hardware_big_screen_resources_unit_id"]
                      sellist.pop("hardware_big_screen_resources_unit_id")
                      appointmentlist.append(sellist)
              return jsonify({
                  "code":1,
                  "data":{
                      "appointment": appointmentlist,
                      "array":array,
                      "period":perioddic
                  }
              })
          else:
              return jsonify({
                  "code":1,
                  "data":""
              })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//scheduling/getSchedulingByAppointment  查询大屏使用排期
@personalcenter.route("/getSchedulingByAppointment/", methods=["POST"])
def getSchedulingByAppointment():
    """查询大屏使用排期"""
    json_data = request.get_json()
    appointment= json_data["appointment"]
    unitId= json_data["unitId"]
    uid= g.token["id"]
    flag=1
    appointment_start= appointment+ "-01"
    appointment_end = appointment + "-31"
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
          if conn.query_all("select * from {} where uid=%s and hardware_big_screen_resources_unit_id=%s and flag=%s and createDate Between %s and %s".format(
              config.TABLENAME40),[uid,unitId,flag,appointment_start,appointment_end]):
              appointmentlist= conn.query_all("select * from {} where uid=%s and hardware_big_screen_resources_unit_id=%s and flag=%s and createDate Between %s and %s".format(
                  config.TABLENAME40),[uid,unitId,flag,appointment_start,appointment_end]
              )

              for i in appointmentlist:
                  i["createDate"] = int(time.mktime(i["createDate"].timetuple()))
                  i["editDate"] = int(time.mktime(i["editDate"].timetuple()))
                  i["unitId"] = i["hardware_big_screen_resources_unit_id"]
                  i.pop("hardware_big_screen_resources_unit_id")
          else:
              appointmentlist = []
          return jsonify({
              "code":1,
              "data": appointmentlist
          })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//pushReport/getUnreadCount  信箱未读数量
@personalcenter.route("/getUnreadCount/", methods=["POST"])
def getUnreadCount():
    """信箱未读数量"""
    json_data = request.get_json()
    uid= g.token["id"]
    status= 0
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
          if conn.query_all("select * from {} where recipient_id=%s and status=%s and recipient_flag=%s and sender_flag=%s".format(config.TABLENAME26),[uid,status,1,1]):
              num=len(conn.query_all("select * from {} where recipient_id=%s and status=%s and recipient_flag=%s and sender_flag=%s".format(config.TABLENAME26),[uid,status,1,1]))
              return jsonify({
                  "code": 1,
                  "data": str(num)
              })
          else:
              return jsonify({
                  "code": 1,
                  "data": "0"
              })

    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement//pushReport/readReportCount  清空信箱未读数
@personalcenter.route("/clearUnreadCount/", methods=["POST"])
def clearUnreadCount():
    """清空信箱未读数量"""
    json_data = request.get_json()
    uid= g.token["id"]
    status= 0
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:

          if conn.query_all("select * from {} where recipient_id=%s and status=%s and recipient_flag=%s and sender_flag=%s".format(config.TABLENAME26),[uid,status,1,1]):
              statuslist= conn.query_all("select * from {} where recipient_id=%s and status=%s and recipient_flag=%s and sender_flag=%s".format(config.TABLENAME26),[uid,status,1,1])
              for i in statuslist:
                  conn.update("update {} set status=%s where id=%s".format(config.TABLENAME26),[1,i["id"]])
          return jsonify({
              "code":1,
              "msg": "读取成功"
          })
    except Exception as e:
        raise e

# http://120.31.140.112:8080/componentManagement/comm/view_layout_name/listAll  页面名称列表(旧驾驶舱)
@personalcenter.route("/view_layout_name_listAll/", methods=["POST"])
def view_layout_name_listAll():
    """页面名称列表(旧驾驶舱)"""
    # """原java接口是全部输出 没有分用户 where uid=%s"""
    json_data = request.get_json()
    uid= g.token["id"]
    flag= 1
    try:
      conn= mysqlpool.get_conn()
      with conn.swich_db(config.DBNAME1) as cursor:
          viewlist= conn.query_all("select id,layoutName,pageUrl from {} where flag=%s ORDER BY createDate DESC".format(config.TABLENAME29),[flag])
          return jsonify({
              "code":1,
              "data": viewlist
          })
    except Exception as e:
        raise e
