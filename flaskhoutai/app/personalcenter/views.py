from flask import Blueprint, request, jsonify, Response, g
from utils.dbutils import mysqlpool
from instance import config
import datetime, requests, json
import base64, time
import random, string
from utils.json_helper import DateEncoder
import uuid
from utils.celery_sqlalchemy_scheduler.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from utils.celery_sqlalchemy_scheduler.session import session_cleanup
from utils.celery_sqlalchemy_scheduler.session import Session
from sqlalchemy import and_
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from utils.token_utils import TokenMaker
import demjson
import sys
import pymysql
from sqlalchemy import DateTime,Numeric,Date,Time

# 创建数据报表应用蓝图
personalcenter = Blueprint("personalcenter", __name__)


# http://120.31.140.112:8080/componentManagement//pushReport/getUnreadCount
# http://120.31.140.112:8080/componentManagement//user/getDepartments  获取推送部门
@personalcenter.route("/getpushDepartments/", methods=["POST"])
def getpushDepartments():
    """获取推送部门"""
    json_data = request.get_json()
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            departmentslist = conn.query_all("select * from {}".format(config.TABLENAME21))
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
    departmentID = json_data["departmentID"]
    conn = mysqlpool.get_conn()
    Userlist = []
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        departmentsUserlist = conn.query_all("select * from {} where DepartmentID= %s".format(config.TABLENAME16),
                                             [departmentID])
    if departmentsUserlist:
        func = lambda x: x if x else ""
        for i in departmentsUserlist:
            usermsgdic = {}
            usermsgdic["createDate"] = int(time.mktime(i["createDate"].timetuple()))
            usermsgdic["departmentID"] = i["DepartmentID"]
            usermsgdic["editDate"] = int(time.mktime(i["editDate"].timetuple()))
            usermsgdic["email"] = func(i["Email"])
            usermsgdic["flag"] = i["flag"]
            usermsgdic["id"] = i["id"]
            usermsgdic["mobile"] = i["Mobile"]
            usermsgdic["password"] = i["Password"]
            usermsgdic["realName"] = i["RealName"]
            usermsgdic["remark"] = func(i["remark"])
            usermsgdic["roleID"] = i["RoleID"]
            usermsgdic["status"] = i["status"]
            usermsgdic["token"] = ""
            usermsgdic["userName"] = i["UserName"]
            Userlist.append(usermsgdic)
    return jsonify({
        "code": 1,
        "data": Userlist
    })


# http://120.31.140.112:8080/componentManagement/pushReport/save/  保存推送内容
@personalcenter.route("/reportPushSave/", methods=["POST"])
def reportPushSave():
    """保存推送内容"""

    json_data = request.get_json()
    departmentId = json_data["departmentId"]
    departmentName = json_data["departmentName"]
    pushAgain = json_data["pushAgain"]
    pushExplain = json_data["pushExplain"]
    readDelete = json_data["readDelete"]
    recipientId = json_data["recipientId"]
    recipientName = json_data["recipientName"]
    reportExplain = json_data["reportExplain"]
    reportId = json_data["reportId"]
    reportName = json_data["reportName"]
    reportType = json_data["reportType"]
    watermarkIs = json_data["watermarkIs"]
    watermarkStr = json_data["watermarkStr"]
    token = json_data["token"]
    uid = g.token["id"]
    remark = json_data.get('remark')
    update_frequency_list = ["DAYS", "HOURS", "MINUTES", "SECONDS"]
    update_frequency = json_data.get('updateFrequency')  # 更新频率
    every_value = json_data.get('every')  # 间隔值
    crontab = json_data.get('crontab')
    crontab_hour = json_data.get('crontabHour')
    crontab_minute = json_data.get('crontabMinute')
    sender_flag = 1
    recipient_flag = 1
    status = 0
    flag = 1

    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        id = str(uuid.uuid4())
        now_time = datetime.datetime.now()
        createDate = now_time.strftime("%Y-%m-%d %H:%M:%S")
        conn.insert_one(
            "insert into {} (id,uid,report_id,report_type,report_name,report_explain,department_id,department_name,recipient_id,recipient_name,push_explain,createDate,sender_flag,recipient_flag,status) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(
                config.TABLENAME26),
            [id, uid, reportId, reportType, reportName, reportExplain, departmentId, departmentName, recipientId,
             recipientName, pushExplain, createDate, sender_flag, recipient_flag, status])
        conn.insert_one(
            "insert into {} (push_report_id,push_again,watermark_is,watermark_str,read_delete,flag) values (%s,%s,%s,%s,%s,%s)".format(
                config.TABLENAME28), [id, pushAgain, watermarkIs, watermarkStr, readDelete, flag])
    datetimenow = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if crontab == 0 and update_frequency in update_frequency_list:
        task_id = TokenMaker().generate_token(token, datetime.datetime.now())
        beat_session = Session()
        with session_cleanup(beat_session):
            schedule = beat_session.query(IntervalSchedule).filter_by(every=every_value,period=getattr(IntervalSchedule,update_frequency)).first()
            if not schedule:
                schedule = IntervalSchedule(every=every_value, period=getattr(IntervalSchedule,update_frequency))
                beat_session.add(schedule)
            task = PeriodicTask(id=task_id,uid=uid,interval=schedule,name='report_push_task_%s'%task_id,task='tasks.tasks_general.report_push',args=json.dumps([uid,report_id,report_type,report_name,reportExplain, departmentId, departmentName, recipientId,
                 recipientName, pushExplain, sender_flag, recipient_flag, status, pushAgain, watermarkIs, watermarkStr, readDelete, flag]),last_run_at=datetimenow,description=remark)
            beat_session.add(task)
            beat_session.commit()
    elif crontab == 1:
        crontab_hour = str(int(crontab_hour))
        crontab_minute = str(int(crontab_minute))
        task_id = TokenMaker().generate_token(token, datetime.datetime.now())
        beat_session = Session()
        with session_cleanup(beat_session):
            schedule = beat_session.query(CrontabSchedule).filter_by(minute=crontab_minute,hour=crontab_hour,timezone=config.TIMEZONE).first()
            if not schedule:
                schedule = CrontabSchedule(minute=crontab_minute,hour=crontab_hour,timezone=config.TIMEZONE)
                beat_session.add(schedule)
            task = PeriodicTask(id=task_id,uid=uid,crontab=schedule,name='report_push_task_%s'%task_id,task='tasks.tasks_general.report_push',args=json.dumps([uid,task_id]),last_run_at=datetimenow,description=remark)
            beat_session.add(task)
            beat_session.commit()
    return jsonify({
        "code": 1,
        "msg": "保存推送内容成功"
    })


@personalcenter.route("/reportPushEmail/", methods=["POST"])
def reportPushEmail():
    """推送邮箱"""
    json_data = request.get_json()
    token = json_data.get("token")
    email_receiver = json_data.get("emailReceiver") #邮件接收人
    email_subject = json_data.get("emailSubject") #邮件标题
    report_id = json_data["reportId"] # 报告id
    update_frequency_list = ["DAYS", "HOURS"]
    update_frequency = json_data.get('updateFrequency')  # 更新频率
    every_value = json_data.get('every')  # 间隔值
    crontab = json_data.get('crontab')
    crontab_hour = json_data.get('crontabHour')
    crontab_minute = json_data.get('crontabMinute')
    report_explain = json_data["reportExplain"] # 报表说明
    report_name = json_data["reportName"] # 报表名称
    sender = json_data["sender"] # 发送人
    uid = g.token["id"]

    # 截图保存图片

    chrome = config.CHROME_DIR
    chrome_options = Options()
    chrome_options.add_argument('--headless')  
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(executable_path=chrome,chrome_options=chrome_options)
    url = config.IMG_SERVER_HOST + config.IMG_SERVER_PORT + config.IMG_SERVER_URL + str(report_id)
    driver.set_window_size(414,736)
    driver.get(url)
    time.sleep(1)
    imgurl = "%s%s_%s.png"%(config.EMAILSENDER,report_id,int(time.time()*1000))
    driver.get_screenshot_as_file(imgurl)
    driver.quit()

    # 邮箱发送图片

    body = '<h>来自%s的推送，请查收附件</h><p>报表：%s</p><p>报表内容：%s</p><img src="cid:dns_">'%(sender,report_name,report_explain)

    msg = MIMEMultipart('related')
    # 设置邮件正文，这里是支持HTML的
    content = MIMEText(body, 'html', 'utf-8')
    msg.attach(content)
    # 图片
    with open(imgurl,'rb') as f:
        img_data = MIMEImage(f.read())
    img_data.add_header('Content-ID', 'dns_')
    msg.attach(img_data)
    # 设置正文为符合邮件格式的HTML内容
    msg['subject'] = email_subject
    # 设置邮件标题
    msg['from'] = config.EMAIL_SENDER
    # 设置发送人
    msg['to'] = email_receiver
    try:
        s = smtplib.SMTP('localhost')
        s.sendmail(config.EMAIL_SENDER, email_receiver, msg.as_string())

        return_sentence = {"code":1,"data":"发送成功"}
        # 保存数据库
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            conn.insert_one("insert into {TABLE} values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(TABLE=config.TABLENAME52),[str(uuid.uuid4()),uid,email_receiver,email_subject,report_id,report_explain,report_name,sender,"%s.png"%report_id,1,datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

    except smtplib.SMTPException as e:
        return {"code":-1,"data":"发送失败,请重试"}
    datetimenow = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 定时推送
    if crontab == 0 and update_frequency in update_frequency_list:
        task_id = TokenMaker().generate_token(token, datetime.datetime.now())
        beat_session = Session()
        with session_cleanup(beat_session):
            schedule = beat_session.query(IntervalSchedule).filter_by(every=every_value,period=getattr(IntervalSchedule,update_frequency)).first()
            if not schedule:
                schedule = IntervalSchedule(every=every_value, period=getattr(IntervalSchedule,update_frequency))
                beat_session.add(schedule)
            task = PeriodicTask(id=task_id,uid=uid,interval=schedule,name='email_push_task_%s'%task_id,task='tasks.tasks_general.report_push',args=json.dumps([sender,report_name,report_explain,imgurl,email_subject,email_receiver,report_id,uid]),last_run_at=datetimenow,description=report_explain)
            beat_session.add(task)
            beat_session.commit()
        return_sentence["taskId"] = task_id
    elif crontab == 1:
        crontab_hour = str(int(crontab_hour))
        crontab_minute = str(int(crontab_minute))
        task_id = TokenMaker().generate_token(token, datetime.datetime.now())
        beat_session = Session()
        with session_cleanup(beat_session):
            schedule = beat_session.query(CrontabSchedule).filter_by(minute=crontab_minute,hour=crontab_hour,timezone=config.TIMEZONE).first()
            if not schedule:
                schedule = CrontabSchedule(minute=crontab_minute,hour=crontab_hour,timezone=config.TIMEZONE)
                beat_session.add(schedule)
            task = PeriodicTask(id=task_id,uid=uid,crontab=schedule,name='email_push_task_%s'%task_id,task='tasks.tasks_general.report_push',args=json.dumps([sender,report_name,report_explain,imgurl,email_subject,email_receiver,report_id,uid]),last_run_at=datetimenow,description=report_explain)
            beat_session.add(task)
            beat_session.commit()
        return_sentence["taskId"] = task_id
    return return_sentence



# http://120.31.140.112:8080/componentManagement//pushReport/querySenderReports  # 推送数据模糊查询
@personalcenter.route("/querylikeSenderReports/", methods=["POST"])
def querylikeSenderReports():
    """推送数据模糊查询"""
    json_data = request.get_json()
    endDate00 = json_data["endDate"]
    page = json_data["page"]
    if page == {'isTrusted': True}:
        page = 1
    recipientName = json_data["recipientName"]
    reportName = json_data["reportName"]
    requestType = json_data["requestType"]
    rows = json_data["rows"]
    startDate00 = json_data["startDate"]
    uid = g.token["id"]

    likecondition = ""
    if reportName != "":
        likecondition = likecondition + " and  a.report_name like '%" + reportName + "%'"
    if recipientName != "":
        likecondition = likecondition + " and a.recipient_name='" + recipientName + "' "
    if requestType != "":
        likecondition = likecondition + " and a.report_type=" + str(requestType) + ""
    if startDate00 != "" and endDate00 != "":
        endDate = endDate00.replace(endDate00.split("-")[-1], str(int(endDate00.split("-")[-1]) + 1)) + " 0:0:0"
        startDate = json_data["startDate"] + " 0:0:0"
        likecondition = likecondition + " and (a.createDate Between '%s' and '%s' )" % (
        datetime.datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S'),
        datetime.datetime.strptime(endDate, '%Y-%m-%d %H:%M:%S'))

    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if not conn.query_all(
                    "select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name, a.report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where uid={uid} {likecondition} order by a.createDate DESC".format(
                            tableA=config.TABLENAME26, tableB=config.TABLENAME28, uid=uid,
                            likecondition=likecondition)):
                return jsonify({
                    "code": 1,
                    "data": {
                        "page": page,
                        "rows": [],
                        "total": 0
                    }
                })
            senderreportlist = conn.query_all(
                "select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name, report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where uid={uid} {likecondition} order by a.createDate DESC".format(
                    tableA=config.TABLENAME26, tableB=config.TABLENAME28, uid=uid, likecondition=likecondition))
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
                        tableA=config.TABLENAME26, tableB=config.TABLENAME28, uid=uid, likecondition=likecondition),
                    [rows])
            elif rows > count and page == 1:
                senderreportlist = conn.query_all(
                    "select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,"
                    " a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name,"
                    " a.report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where uid={uid} {likecondition} order by a.createDate DESC".format(
                        tableA=config.TABLENAME26, tableB=config.TABLENAME28, uid=uid, likecondition=likecondition))
            elif count > rows and 1 < page <= pages:
                senderreportlist = conn.query_all(
                    "select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,"
                    " a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name,"
                    " a.report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where uid={uid} {likecondition} order by a.createDate DESC LIMIT %s,%s ".format(
                        tableA=config.TABLENAME26, tableB=config.TABLENAME28, uid=uid, likecondition=likecondition),
                    [uid, (page - 1) * rows, rows])

            for i in senderreportlist:
                i["createDate"] = i["createDate"].strftime("%Y-%m-%d %H:%M:%S")
                reportid = i["report_id"]
                if conn.query_one("select thumbnail,flag from {} where id=%s".format(config.TABLENAME9), [reportid]):
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
                "page": page,
                "rows": senderreportlist,
                "total": count
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
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            pushMailtypelist = conn.query_all("select * from {}".format(config.TABLENAME32))
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
    recipientReportsids = json_data["ids"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.DBNAME1) as cursor:
            for i in recipientReportsids:
                conn.update("update {} set recipient_flag={} where id=%s".format(config.TABLENAME26, 0), [i])
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
    endDate00 = json_data["endDate"]
    page = json_data["page"]
    if page == {'isTrusted': True}:
        page = 1
    reportName = json_data["reportName"]
    requestType = json_data["requestType"]
    rows = json_data["rows"]
    senderName = json_data["senderName"]
    startDate00 = json_data["startDate"]
    recipient_id = g.token["id"]
    likecondition = ""
    if reportName != "":
        likecondition = likecondition + " and  a.report_name like '%" + reportName + "%'"
    if startDate00 != "" and endDate00 != "":
        startDate = json_data["startDate"] + " 0:0:0"
        endDate = endDate00.replace(endDate00.split("-")[-1], str(int(endDate00.split("-")[-1]) + 1)) + " 0:0:0"
        likecondition = likecondition + " and (a.createDate Between '%s' and '%s' )" % (
        datetime.datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S'),
        datetime.datetime.strptime(endDate, '%Y-%m-%d %H:%M:%S'))
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            userlist = conn.query_all("select id,UserName from {}".format(config.TABLENAME16))
            userid_username = {}
            username_userid = {}
            recipient_flag = 1
            sender_flag = 1
            for j in userlist:
                userid_username[j["id"]] = j["UserName"]
                username_userid[j["UserName"]] = j["id"]
            if senderName != "":
                likecondition = likecondition + " and a.uid='" + username_userid[senderName] + "' "
            if not conn.query_all(
                    "select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name, a.report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where a.recipient_id={recipient_id} and a.recipient_flag={recipient_flag} and a.sender_flag={recipient_flag} {likecondition} order by a.createDate DESC".format(
                            tableA=config.TABLENAME26, tableB=config.TABLENAME28, recipient_id=recipient_id,
                            recipient_flag=recipient_flag, sender_flag=sender_flag, likecondition=likecondition)):
                return jsonify({
                    "code": 1,
                    "data": {
                        "page": page,
                        "rows": [],
                        "total": 0
                    }
                })
            senderreportlist = conn.query_all(
                "select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name, report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where a.recipient_id={recipient_id} and a.recipient_flag={recipient_flag} and a.sender_flag={sender_flag} {likecondition} order by a.createDate DESC".format(
                    tableA=config.TABLENAME26, tableB=config.TABLENAME28, recipient_id=recipient_id,
                    recipient_flag=recipient_flag, sender_flag=sender_flag, likecondition=likecondition))

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
                        tableA=config.TABLENAME26, tableB=config.TABLENAME28, recipient_id=recipient_id,
                        recipient_flag=recipient_flag, sender_flag=sender_flag, likecondition=likecondition, rows=rows))
            elif rows > count and page == 1:
                senderreportlist = conn.query_all(
                    "select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,"
                    " a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name,"
                    " a.report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where a.recipient_id={recipient_id} and a.recipient_flag={recipient_flag} and a.sender_flag={sender_flag} {likecondition} order by a.createDate DESC".format(
                        tableA=config.TABLENAME26, tableB=config.TABLENAME28, recipient_id=recipient_id,
                        recipient_flag=recipient_flag, sender_flag=sender_flag, likecondition=likecondition))
            elif count > rows and 1 < page <= pages:
                senderreportlist = conn.query_all(
                    "select a.createDate,a.department_id,a.department_name,a.id,b.push_again,a.push_explain,b.read_delete,"
                    " a.recipient_flag,a.recipient_id,a.recipient_name,a.report_explain,a.report_id,a.report_name,"
                    " a.report_type,a.sender_flag,a.status,a.uid,b.watermark_is from {tableA} as a left join {tableB} as b on a.id=b.push_report_id where a.recipient_id={recipient_id} and a.recipient_flag={recipient_flag} and a.sender_flag={sender_flag} {likecondition} order by a.createDate DESC LIMIT {rows01},{rows} ".format(
                        tableA=config.TABLENAME26, tableB=config.TABLENAME28, recipient_id=recipient_id,
                        recipient_flag=recipient_flag, sender_flag=sender_flag, likecondition=likecondition,
                        rows01=(page - 1) * rows, rows=rows))

            for i in senderreportlist:
                i["UserName"] = userid_username[i["uid"]]
                i["createDate"] = i["createDate"].strftime("%Y-%m-%d %H:%M:%S")
                reportid = i["report_id"]
                # 通过判断 push_id 判断是否为收藏
                uid = g.token["id"]
                if conn.query_all("select * from {} where uid=%s and flag=%s and push_id=%s".format(config.TABLENAME34),
                                  [uid, 1, i["id"]]):
                    i["push_id"] = i["id"]
                else:
                    i["push_id"] = ""

                i["report_explain"] = func(i["report_explain"])
                if conn.query_one("select thumbnail,flag from {} where id=%s".format(config.TABLENAME9), [reportid]):
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
                "page": page,
                "rows": senderreportlist,
                "total": count
            }
        })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//pushReport/readPushReport 点击信箱变已读
@personalcenter.route("/readPushReport/", methods=["POST"])
def readPushReport():
    """点击信箱已读"""
    json_data = request.get_json()
    readPushReportid = json_data["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.DBNAME1) as cursor:
            conn.update("update {} set status={} where id=%s".format(config.TABLENAME26, 1), [readPushReportid])
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
    endDate00 = json_data["endDate"]
    page = json_data["page"]
    if page == {'isTrusted': True}:
        page = 1
    reportName = json_data["reportName"]
    requestType = json_data["requestType"]
    rows = json_data["rows"]
    senderName = json_data["senderName"]
    startDate00 = json_data["startDate"]
    uid = g.token["id"]
    flag = 1
    likecondition = ""
    if reportName != "":
        likecondition = likecondition + " and  a.report_name like '%" + reportName + "%'"

    if startDate00 != "" and endDate00 != "":
        startDate = json_data["startDate"] + " 0:0:0"
        endDate = endDate00.replace(endDate00.split("-")[-1], str(int(endDate00.split("-")[-1]) + 1)) + " 0:0:0"
        likecondition = likecondition + " and (a.createDate Between '%s' and '%s' )" % (
        datetime.datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S'),
        datetime.datetime.strptime(endDate, '%Y-%m-%d %H:%M:%S'))
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            userlist = conn.query_all("select id,UserName from {}".format(config.TABLENAME16))
            userid_username = {}
            username_userid = {}
            for j in userlist:
                userid_username[j["id"]] = j["UserName"]
                username_userid[j["UserName"]] = j["id"]
            if senderName != "":
                likecondition = likecondition + " and a.uid='" + username_userid[senderName] + "' "

            if not conn.query_all(
                    "select b.createDate,b.department_id,b.department_name,b.id,b.push_explain,a.push_id,b.recipient_flag,b.recipient_id,b.recipient_name,b.report_explain,b.report_id,b.report_name,b.report_type,b.sender_flag,b.status,b.uid from {tableA} as a left join {tableB} as b on a.push_id= b.id where a.uid={uid} and a.flag={flag} {likecondition} order by a.createDate DESC".format(
                            tableA=config.TABLENAME34, tableB=config.TABLENAME26, uid=uid, flag=flag,
                            likecondition=likecondition)):
                return jsonify({
                    "code": 1,
                    "data": {
                        "page": page,
                        "rows": [],
                        "total": 0
                    }
                })
            collectionlist = conn.query_all(
                "select b.createDate,b.department_id,b.department_name,b.id,b.push_explain,a.push_id,b.recipient_flag,b.recipient_id,b.recipient_name,b.report_explain,b.report_id,b.report_name,b.report_type,b.sender_flag,b.status,b.uid from {tableA} as a left join {tableB} as b on a.push_id= b.id where a.uid={uid} and a.flag={flag} {likecondition} order by a.createDate DESC".format(
                    tableA=config.TABLENAME34, tableB=config.TABLENAME26, uid=uid, flag=flag,
                    likecondition=likecondition))
            # 总数量
            count = len(collectionlist)
            # 总页数
            pages = count // rows if count % rows == 0 else count // rows + 1
            func = lambda x: x if x else ""
            # 总数量 大于 每页数量 但页码为一 显示第一页内容
            if rows <= count and page == 1:
                collectionlist = conn.query_all(
                    "select b.createDate,b.department_id,b.department_name,b.id,b.push_explain,a.push_id,b.recipient_flag,b.recipient_id,b.recipient_name,b.report_explain,b.report_id,b.report_name,b.report_type,b.sender_flag,b.status,b.uid from {tableA} as a left join {tableB} as b on a.push_id= b.id where a.uid={uid} and a.flag={flag} {likecondition} order by a.createDate DESC limit %s".format(
                        tableA=config.TABLENAME34, tableB=config.TABLENAME26, uid=uid, flag=flag,
                        likecondition=likecondition), [rows])
            elif rows > count and page == 1:
                collectionlist = conn.query_all(
                    "select b.createDate,b.department_id,b.department_name,b.id,b.push_explain,a.push_id,b.recipient_flag,b.recipient_id,b.recipient_name,b.report_explain,b.report_id,b.report_name,b.report_type,b.sender_flag,b.status,b.uid from {tableA} as a left join {tableB} as b on a.push_id= b.id where a.uid={uid} and a.flag={flag} {likecondition} order by a.createDate DESC".format(
                        tableA=config.TABLENAME34, tableB=config.TABLENAME26, uid=uid, flag=flag,
                        likecondition=likecondition))
            elif count > rows and 1 < page <= pages:
                collectionlist = conn.query_all(
                    "select b.createDate,b.department_id,b.department_name,b.id,b.push_explain,a.push_id,b.recipient_flag,b.recipient_id,b.recipient_name,b.report_explain,b.report_id,b.report_name,b.report_type,b.sender_flag,b.status,b.uid from {tableA} as a left join {tableB} as b on a.push_id= b.id where a.uid={uid} and a.flag={flag} {likecondition} order by a.createDate DESC limit %s,%s".format(
                        tableA=config.TABLENAME34, tableB=config.TABLENAME26, uid=uid, flag=flag,
                        likecondition=likecondition), [(page - 1) * rows, rows])
            for i in collectionlist:
                i["UserName"] = userid_username[i["uid"]]
                i["createDate"] = i["createDate"].strftime("%Y-%m-%d %H:%M:%S")
                reportid = i["report_id"]
                i["report_explain"] = func(i["report_explain"])
                i["short_name"] = i["department_name"]
                if conn.query_one("select thumbnail,flag from {} where id=%s".format(config.TABLENAME9), [reportid]):
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
                "page": page,
                "rows": collectionlist,
                "total": count
            }
        })

    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//collection/save   点击收藏
@personalcenter.route("/clickCollect/", methods=["POST"])
def clickCollect():
    """点击收藏"""
    json_data = request.get_json()
    pushId = json_data["pushId"]
    uid = g.token["id"]
    token = json_data["token"]

    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.DBNAME1) as cursor:
            id = str(uuid.uuid4())
            now_time = datetime.datetime.now()
            createDate = now_time.strftime("%Y-%m-%d %H:%M:%S")
            conn.insert_one(
                "insert into {} (id,uid,push_id,createDate,flag) values (%s,%s,%s,%s,%s)".format(config.TABLENAME34),
                [id, uid, pushId, createDate, 1])
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
    ids = json_data["ids"]
    uid = g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.DBNAME1) as cursor:
            for i in ids:
                conn.update("update {} set flag=%s where uid=%s and flag=%s and push_id=%s".format(config.TABLENAME34),
                            [0, uid, 1, i])
        return jsonify({
            "code": 1,
            "msg": "取消收藏成功"
        })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//comm/imgDownload  下载图片 thumbnail: 图片全路径
@personalcenter.route('/imgDownload/', methods=['POST'])
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
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.DBNAME1) as cursor:
            hardware = conn.query_all("select * from {}".format(config.TABLENAME36))
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
    name = json_data["name"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.DBNAME1) as cursor:
            likename = "%" + name + "%"
            hardware = conn.query_all("select * from {} where name like %s".format(config.TABLENAME36), [likename])
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
    name = json_data["name"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.DBNAME1) as cursor:
            names = []
            if conn.query_all(
                    "select a.address,a.flag,a.hbid,a.id,a.leader,a.name,a.phone,a.size from {tableA} as a left join {tableB} as b on a.hbid=b.id where b.name=%s".format(
                            tableA=config.TABLENAME37, tableB=config.TABLENAME36), [name]):
                screenlist = conn.query_all(
                    "select a.address,a.flag,a.hbid,a.id,a.leader,a.name,a.phone,a.size from {tableA} as a left join {tableB} as b on a.hbid=b.id where b.name=%s".format(
                        tableA=config.TABLENAME37, tableB=config.TABLENAME36), [name])
            else:
                screenlist = []
            for i in screenlist:
                names.append(i["name"])
        return jsonify({
            "code": 1,
            "data": {
                "names": names,
                "list": screenlist
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
    flag = 1
    userid = g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if conn.query_all(
                    "select b.address,a.appointment_detail,a.createDate,a.editDate,a.flag,a.hardware_big_screen_resources_unit_id,a.header,a.id,b.name,a.period_p_column,a.period_p_id,a.phone,a.reception_object,a.uid,a.unit_name"
                    "  from {tableA} as a left join {tableB} as b on a.hardware_big_screen_resources_unit_id=b.id where a.flag=%s and a.uid=%s order by a.createDate DESC ".format(
                        tableA=config.TABLENAME38, tableB=config.TABLENAME37), [flag, userid]):
                return_list = conn.query_all(
                    "select b.address,a.appointment_detail,a.createDate,a.editDate,a.flag,a.hardware_big_screen_resources_unit_id,a.header,a.id,b.name,a.period_p_column,a.period_p_id,a.phone,a.reception_object,a.uid,a.unit_name"
                    "  from {tableA} as a left join {tableB} as b on a.hardware_big_screen_resources_unit_id=b.id where a.flag=%s and a.uid=%s order by a.createDate DESC ".format(
                        tableA=config.TABLENAME38, tableB=config.TABLENAME37), [flag, userid]
                )
            else:
                return jsonify({
                    "code": 1,
                    "data": {
                        "page": 1,
                        "total": 0,
                        "rows": []
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
                        tableA=config.TABLENAME38, tableB=config.TABLENAME37), [flag, userid, total])
            elif total > count and page == 1:
                return_list = return_list
            elif count > total and 1 < page <= pages:
                return_list = conn.query_all(
                    "select b.address,a.appointment_detail,a.createDate,a.editDate,a.flag,a.hardware_big_screen_resources_unit_id,a.header,a.id,b.name,a.period_p_column,a.period_p_id,a.phone,a.reception_object,a.uid,a.unit_name"
                    "  from {tableA} as a left join {tableB} as b on a.hardware_big_screen_resources_unit_id=b.id where a.flag=%s and a.uid=%s order by a.createDate DESC limit %s,%s ".format(
                        tableA=config.TABLENAME38, tableB=config.TABLENAME37),
                    [flag, userid, (page - 1) * total, total])
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
    ids = json_data["ids"]
    uid = g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.DBNAME1) as cursor:
            for i in ids:
                conn.update("update {} set flag=%s where uid=%s and flag=%s and id=%s".format(config.TABLENAME38),
                            [0, uid, 1, i["id"]])
                if conn.query_one(
                        "select scheduling_id from {} where {}= %s".format(config.TABLENAME39, i["periodPColumn"]),
                        [i["periodPId"]]):
                    scheduling_id_dic = conn.query_one(
                        "select scheduling_id from {} where {}= %s".format(config.TABLENAME39, i["periodPColumn"]),
                        [i["periodPId"]])
                    conn.update("update {} set flag=%s where flag=%s and uid=%s and id=%s".format(config.TABLENAME40),
                                [0, 1, uid, scheduling_id_dic["scheduling_id"]])
                conn.update(
                    "update {table} set {periodPColumn}=%s where {periodPColumn}= %s".format(table=config.TABLENAME39,
                                                                                             periodPColumn=i[
                                                                                                 "periodPColumn"]),
                    [0, i["periodPId"]])
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
    appointment = json_data["appointment"]
    periodP = json_data["periodP"]
    unitId = json_data["unitId"]
    reserveForm = json_data["reserveForm"]
    uid = g.token["id"]
    token = json_data["token"]
    now_time = datetime.datetime.now()
    createDate = now_time.strftime("%Y-%m-%d %H:%M:%S")
    flag = 1
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.DBNAME1) as cursor:
            if conn.query_all(
                    "select appointment_detail from {} where hardware_big_screen_resources_unit_id=%s and flag=%s and period_p_column=%s".format(
                            config.TABLENAME38), [unitId, flag, periodP]):
                datalist = conn.query_all(
                    "select appointment_detail from {} where hardware_big_screen_resources_unit_id=%s and flag=%s and period_p_column=%s".format(
                        config.TABLENAME38), [unitId, flag, periodP])
                for i in datalist:
                    if i["appointment_detail"][:10] == appointment:
                        return jsonify({
                            "code": 1,
                            "msg": "已有预约，请重新预约"
                        })
            id = str(uuid.uuid4())
            period_p_id = str(uuid.uuid4())
            conn.insert_one(
                "insert into {} (id,uid,hardware_big_screen_resources_unit_id,period_p_id,period_p_column,appointment_detail,unit_name,header,phone,reception_object,createDate,editDate,flag) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(
                    config.TABLENAME38),
                [id, uid, unitId, period_p_id, periodP, reserveForm["appointmentDetail"], reserveForm["unitName"],
                 reserveForm["header"], reserveForm["phone"], reserveForm["receptionObject"], createDate, createDate,
                 flag])
            schedulingid = str(uuid.uuid4())
            conn.insert_one(
                "insert into {} (id,uid,hardware_big_screen_resources_unit_id,appointment,className,createDate,editDate,flag) values (%s,%s,%s,%s,%s,%s,%s,%s)".format(
                    config.TABLENAME40),
                [schedulingid, uid, unitId, appointment, "markOrange", createDate, createDate, flag])
            conn.commit()
            if conn.query_one("select * from {} where scheduling_id=%s".format(config.TABLENAME39), [schedulingid]):
                conn.update("update {} set {}=%s where scheduling_id=%s".format(config.TABLENAME39, periodP),
                            [period_p_id, schedulingid])
            else:
                scheduling_period_id = str(uuid.uid4())
                if periodP == "p1":
                    insertlist = [scheduling_period_id, schedulingid, period_p_id, 0, 0, 0]
                elif periodP == "p2":
                    insertlist = [scheduling_period_id, schedulingid, 0, period_p_id, 0, 0]
                elif periodP == "p3":
                    insertlist = [scheduling_period_id, schedulingid, 0, 0, period_p_id, 0]
                elif periodP == "p4":
                    insertlist = [scheduling_period_id, schedulingid, 0, 0, 0, period_p_id]

                conn.insert_one("insert into {} (id,scheduling_id,p1,p2,p3,p4) values (%s,%s,%s,%s,%s,%s)".format(
                    config.TABLENAME39), insertlist)
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
    periodPId = json_data["periodPId"]
    uid = g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.DBNAME1) as cursor:
            if conn.query_one("select * from {} where uid=%s and period_p_id=%s".format(config.TABLENAME38),
                              [uid, periodPId]):
                sellist = conn.query_one("select * from {} where uid=%s and period_p_id=%s".format(config.TABLENAME38),
                                         [uid, periodPId])
                sellist["createDate"] = int(time.mktime(sellist["createDate"].timetuple()))
                sellist["editDate"] = int(time.mktime(sellist["editDate"].timetuple()))
                sellist["unitId"] = sellist["hardware_big_screen_resources_unit_id"]
                sellist.pop("hardware_big_screen_resources_unit_id")
                return jsonify({
                    "code": 1,
                    "data": [sellist]
                })
            else:
                return jsonify({
                    "code": 1,
                    "data": []
                })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//scheduling/getSchedulingMsgById 各预约时间段信息
@personalcenter.route("/getSchedulingMsgById/", methods=["POST"])
def getSchedulingMsgById():
    """预约时间段具体信息"""
    json_data = request.get_json()
    schedulingId = json_data["schedulingId"]
    uid = g.token["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.DBNAME1) as cursor:
            if conn.query_one("select * from {} where scheduling_id=%s".format(config.TABLENAME39), [schedulingId]):
                perioddic = conn.query_one("select * from {} where scheduling_id=%s".format(config.TABLENAME39),
                                           [schedulingId])
                array = [perioddic["p1"], perioddic["p2"], perioddic["p3"], perioddic["p4"]]
                appointmentlist = []
                for i in array:
                    if i != "0":
                        sellist = conn.query_one(
                            "select * from {} where uid=%s and period_p_id=%s".format(config.TABLENAME38), [uid, i])
                        sellist["createDate"] = int(time.mktime(sellist["createDate"].timetuple()))
                        sellist["editDate"] = int(time.mktime(sellist["editDate"].timetuple()))
                        sellist["unitId"] = sellist["hardware_big_screen_resources_unit_id"]
                        sellist.pop("hardware_big_screen_resources_unit_id")
                        appointmentlist.append(sellist)
                return jsonify({
                    "code": 1,
                    "data": {
                        "appointment": appointmentlist,
                        "array": array,
                        "period": perioddic
                    }
                })
            else:
                return jsonify({
                    "code": 1,
                    "data": ""
                })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//scheduling/getSchedulingByAppointment  查询大屏使用排期
@personalcenter.route("/getSchedulingByAppointment/", methods=["POST"])
def getSchedulingByAppointment():
    """查询大屏使用排期"""
    json_data = request.get_json()
    appointment = json_data["appointment"]
    unitId = json_data["unitId"]
    uid = g.token["id"]
    flag = 1
    appointment_start = appointment + "-01"
    appointment_end = appointment + "-31"
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.DBNAME1) as cursor:
            if conn.query_all(
                    "select * from {} where uid=%s and hardware_big_screen_resources_unit_id=%s and flag=%s and createDate Between %s and %s".format(
                            config.TABLENAME40), [uid, unitId, flag, appointment_start, appointment_end]):
                appointmentlist = conn.query_all(
                    "select * from {} where uid=%s and hardware_big_screen_resources_unit_id=%s and flag=%s and createDate Between %s and %s".format(
                        config.TABLENAME40), [uid, unitId, flag, appointment_start, appointment_end]
                )

                for i in appointmentlist:
                    i["createDate"] = int(time.mktime(i["createDate"].timetuple()))
                    i["editDate"] = int(time.mktime(i["editDate"].timetuple()))
                    i["unitId"] = i["hardware_big_screen_resources_unit_id"]
                    i.pop("hardware_big_screen_resources_unit_id")
            else:
                appointmentlist = []
            return jsonify({
                "code": 1,
                "data": appointmentlist
            })
    except Exception as e:
        raise e


# http://120.31.140.112:8080/componentManagement//pushReport/getUnreadCount  信箱未读数量
@personalcenter.route("/getUnreadCount/", methods=["POST"])
def getUnreadCount():
    """信箱未读数量"""
    json_data = request.get_json()
    uid = g.token["id"]
    status = 0
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.DBNAME1) as cursor:
            if conn.query_all(
                    "select * from {} where recipient_id=%s and status=%s and recipient_flag=%s and sender_flag=%s".format(
                            config.TABLENAME26), [uid, status, 1, 1]):
                num = len(conn.query_all(
                    "select * from {} where recipient_id=%s and status=%s and recipient_flag=%s and sender_flag=%s".format(
                        config.TABLENAME26), [uid, status, 1, 1]))
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
    uid = g.token["id"]
    status = 0
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.DBNAME1) as cursor:

            if conn.query_all(
                    "select * from {} where recipient_id=%s and status=%s and recipient_flag=%s and sender_flag=%s".format(
                            config.TABLENAME26), [uid, status, 1, 1]):
                statuslist = conn.query_all(
                    "select * from {} where recipient_id=%s and status=%s and recipient_flag=%s and sender_flag=%s".format(
                        config.TABLENAME26), [uid, status, 1, 1])
                for i in statuslist:
                    conn.update("update {} set status=%s where id=%s".format(config.TABLENAME26), [1, i["id"]])
            return jsonify({
                "code": 1,
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
    uid = g.token["id"]
    flag = 1
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.DBNAME1) as cursor:
        viewlist = conn.query_all(
            "select id,layoutName,pageUrl from {} where flag=%s ORDER BY createDate DESC".format(
                config.TABLENAME29), [flag])
        return jsonify({
            "code": 1,
            "data": viewlist
        })


@personalcenter.route("/task_query_all/", methods=['POST'])
def task_query_all():
    """查询定时任务"""
    def result_to_dict(results):
        res = [dict(zip(r.keys(), r)) for r in results]
        for r in res:
            find_datetime(r)
        return res
    def find_datetime(value):
        for v in value:
            if (isinstance(value[v], datetime.datetime)):
                value[v] = convert_datetime(value[v])
    def convert_datetime(value):
        if value:
            if(isinstance(value,(datetime.datetime,DateTime))):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            elif(isinstance(value,(date,Date))):
                return value.strftime("%Y-%m-%d")
            elif(isinstance(value,(Time,time))):
                return value.strftime("%H:%M:%S")
        else:
            return ""

    uid = g.token.get('id')
    beat_session = Session()
    with session_cleanup(beat_session):
        tasks_msg = beat_session.query(PeriodicTask.id,PeriodicTask.table_name,PeriodicTask.expires,PeriodicTask.one_off,PeriodicTask.last_run_at,PeriodicTask.total_run_count,PeriodicTask.enabled,PeriodicTask.description,IntervalSchedule.every,IntervalSchedule.period,CrontabSchedule.minute,CrontabSchedule.hour).outerjoin(IntervalSchedule,PeriodicTask.interval_id==IntervalSchedule.id).outerjoin(CrontabSchedule,PeriodicTask.crontab_id==CrontabSchedule.id).filter(and_(PeriodicTask.uid==uid,PeriodicTask.flag==True)).all()
    res = result_to_dict(tasks_msg)
    conn = mysqlpool.get_conn()
    with conn.swich_db("%s_db"%uid, cursor=pymysql.cursors.Cursor) as cursor:
        for pl in res:
            print(type(pl),pl,file=sys.stdout)
            qres = conn.query_one("select worksheet_name_cn from {TABLE} where worksheet_name=%s".format(TABLE=config.ME2_TABLENAME2),[pl['table_name']])
            if qres:
                pl['table_name'] = qres[0]
            
    return Response(demjson.encode(res))


@personalcenter.route("/task_switch/", methods=['POST'])
def task_switch():
    """
    开启/暂停定时任务
    """
    uid = g.token.get('id')
    json_data = request.get_json()
    task_id = json_data.get('task_id')
    enabled = bool(json_data.get('enabled'))
    try:
        beat_session = Session()
        with session_cleanup(beat_session):
            beat_row = beat_session.query(PeriodicTask).filter_by(id=task_id,uid=uid).first()
            beat_row.enabled = enabled
            beat_session.commit()
        return jsonify({'code':1,'data':'操作成功'})
    except Exception as e:
        return jsonify({'code':-1,'data':'操作失败'})

@personalcenter.route("/task_revok/", methods=['POST'])
def task_revok():
    """
    取消定时任务
    """
    uid = g.token.get('id')
    json_data = request.get_json()
    task_id = json_data.get('task_id')  
    try:
        beat_session = Session()
        with session_cleanup(beat_session):
            beat_row = beat_session.query(PeriodicTask).filter_by(id=task_id,uid=uid).first()
            beat_row.flag = 0
            beat_row.enabled = False
            beat_session.commit()
        return jsonify({'code':1,'data':'操作成功'})
    except:
        return jsonify({'code':-1,'data':'操作失败'})


from tasks.tasks_general import add
@personalcenter.route("/testtask/", methods=['POST'])
def testtask():
    res = add.apply_async((3,7),countdown=200)
    return jsonify({'code':1,'id':res.task_id})


from tasks.celery import CeleryResult
@personalcenter.route("/queryresult/", methods=['POST'])
def queryresult():  
    json_data = request.get_json()
    task_id = json_data.get('task_id')
    state = CeleryResult(task_id).state
    return jsonify({'code':1,'state':state})

from tasks.celery import celery
@personalcenter.route("/tasksrevoke/", methods=['POST'])
def tasksrevoke():  
    json_data = request.get_json()
    task_id = json_data.get('task_id')
    celery.control.terminate(task_id,signal='SIGKILL')

    return jsonify({'code':1})