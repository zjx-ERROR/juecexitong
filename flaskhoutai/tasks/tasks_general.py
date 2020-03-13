from tasks.celery import celery
from instance import config
from utils.dbutils import mysqlpool
from datetime import datetime
import importlib
import pymysql
import cx_Oracle
from utils.token_utils import TokenMaker
import demjson
import copy
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import smtplib
import uuid
# 例子

@celery.task
def add(a, b):
    print("计算结果：",a+b)
    # conn = mysqlpool.get_conn()
    # with conn.swich_db('test') as cursor:
    #     conn.insert_one('insert into celery_beat_test(createtime,numb) values(%s,%s)',[datetime.now().strftime('%y-%m-%d %H:%M:%S'),a+b])

@celery.task
def datacrawl(uid,task_id,update_type,data_type):
    """
    update_type:1为增量，2为覆盖
    """
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01,cursor=pymysql.cursors.Cursor) as cursor:
        res = conn.query_one("select tableName from {TABLE} where uid = \"{UID}\" and id = \"{TASKID}\"".format(TABLE=config.TABLENAME49,UID=uid,TASKID=task_id))[0]
    if res:
        impomodule = importlib.import_module("utils.govdatacrawl.%s"%data_type)
        main_run = getattr(impomodule,'main') # 执行爬虫
        result = main_run()
        if result:
            insert_data = []
            for v in result:
                for v_value in v:
                    try:
                        if len(v[v_value]) == 0:
                            v[v_value] = ""
                    except:
                        pass
                vv = copy.deepcopy(v)
                vv.pop('crawlTime')
                insert_data.append(tuple([TokenMaker().generate_token('worksheet_id',demjson.encode(vv.values(),encoding="utf-8"))]+list(v.values())))

            baifens = '%s'
            for j in range(len(result[0])):
                baifens += ',%s'

            insert_sentence = "insert into {TABLE}({FIELD}) values(".format(TABLE=res,FIELD="worksheet_id,%s"%','.join(result[0].keys())) + baifens +")"
            conn = mysqlpool.get_conn()
            with conn.swich_db("%s_db" % uid,cursor=pymysql.cursors.Cursor) as cursor:
                if int(update_type) == 2:
                    conn.update("truncate table `%s`"%res)
                conn.insert_many(insert_sentence,insert_data)

@celery.task
def report_push(uid,report_id,report_type,report_name,reportExplain, departmentId, departmentName, recipientId,recipientName, pushExplain, sender_flag, recipient_flag, status, pushAgain, watermarkIs, watermarkStr, readDelete, flag):

    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        id = str(uuid.uuid4())
        createDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.insert_one(
            "insert into {} (id,uid,report_id,report_type,report_name,report_explain,department_id,department_name,recipient_id,recipient_name,push_explain,createDate,sender_flag,recipient_flag,status) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(
            config.TABLENAME26),
            [id, uid, reportId, reportType, reportName, reportExplain, departmentId, departmentName, recipientId,
            recipientName, pushExplain, createDate, sender_flag, recipient_flag, status])
        conn.insert_one(
            "insert into {} (push_report_id,push_again,watermark_is,watermark_str,read_delete,flag) values (%s,%s,%s,%s,%s,%s)".format(
                config.TABLENAME28), [id, pushAgain, watermarkIs, watermarkStr, readDelete, flag])

@celery.task
def email_push(sender,report_name,report_explain,imgurl,email_subject,email_receiver,report_id,uid):

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
        # 保存数据库
        s = smtplib.SMTP('localhost')
        s.sendmail(config.EMAIL_SENDER, email_receiver, msg.as_string())

        # 发送邮件！
        send_status = 1
    except smtplib.SMTPException:
        conn.rollback()
        send_status = 0
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        conn.insert_one("insert into {TABLE} values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(TABLE=config.TABLENAME52),[str(uuid.uuid4()),uid,email_receiver,email_subject,report_id,report_explain,report_name,sender,"%s.png"%report_id,send_status,datetime.now().strftime('%Y-%m-%d %H:%M:%S')])


@celery.task
def dbcrawl(tb_name,origin_table_name,sourceid,uid,update_type,customize_sql):
    """
    update_type:1为增量，2为覆盖
    """
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        query_res = conn.query_one("select sourceType,account,password,link from {TABLE} where id = %s".format(TABLE=config.TABLENAME4),sourceid)
    pre_link = query_res["link"]
    host, pad = pre_link.split(":")
    port, databasename = pad.split("/")
    dbtype = query_res["sourceType"]
    user = query_res['account']
    password = query_res['password']

    if dbtype.lower() == "mysql":
        db = pymysql.connect(
            host="{}".format(host),
            user="{}".format(user),
            port=int(port),
            password="{}".format(password),
            db=databasename
        )

        cur = db.cursor(cursor=pymysql.cursors.DictCursor)
        if customize_sql:
            sql = customize_sql
        else:
            sql = "select * from %s;" % (origin_table_name)
        cur.execute(sql)

    elif dbtype.lower() == "oracle":
        from utils.dbutils import makeDictFactory
        dsn = cx_Oracle.makedsn(host, port, databasename.upper())
        conn = cx_Oracle.connect(user=user, password=password, dsn=dsn, encoding="UTF-8")
        cur = conn.cursor()
        if customize_sql:
            sql = customize_sql
        else:
            sql = "select * from {TABLE}".format(TABLE=origin_table_name.upper())
        cur.execute(sql)
        cur.rowfactory = makeDictFactory(cur)

    fetdata = cur.fetchall()
    cur.close()
    db.close()
    columns = [list(i.keys()) for i in fetdata][0]
    baifens = ''
    for j in range(len(columns)):
        baifens += '%s,'
    conn = mysqlpool.get_conn()
    with conn.swich_db("%s_db" % uid) as cursor:
        if int(update_type) == 2:
            conn.update("truncate table `%s`"%tb_name)
        insert_sentence = 'insert ignore into `%s` (%s)'%(tb_name,"worksheet_id,%s"%','.join(columns)) + ' values(' + baifens[:-1] + ')'
        insert_data = [tuple([TokenMaker().generate_token('worksheet_id',demjson.encode(i.values(),encoding="utf-8"))]+list(i.values())) for i in fetdata]
        conn.insert_many(insert_sentence,insert_data)


if __name__ == "__main__":
    pass
