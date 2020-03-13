#! usr/bin/python
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, Response ,g
from instance import config
import pymysql
import demjson
from xpinyin import Pinyin
from utils.dbutils import redis
from utils.token_utils import TokenMaker
from utils.dbutils import mysqlpool
from utils.celery_sqlalchemy_scheduler.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from utils.celery_sqlalchemy_scheduler.session import session_cleanup
from utils.celery_sqlalchemy_scheduler.session import Session
import importlib
import uuid
import datetime
import json
import copy

# 创建数据采集的蓝图
public_data = Blueprint("public_data", __name__)

@public_data.route("/return_table_msg/", methods=["POST"])
def return_table_msg():
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.DBNAME3) as cursor:
        fetdata = conn.query_all('select id,cityEn,cityZh,provinceZh from city where provinceEn="guangdong"')
    return Response(json.dumps({"code": 1, "data": fetdata}), mimetype='application/json')

@public_data.route("/save_apitable/", methods=['POST'])
def save_apitable():
    obj = request.get_json()
    table_name = obj["tableName"]
    table_type = obj["tableType"]
    group_name = obj["groupName"]
    conn = mysqlpool.get_conn()
    uid = g.token.get("id")
    with conn.swich_db("%s_db"%uid) as cursor:
        if conn.query_one('select * from {TABLE} where worksheet_name = %s'.format(TABLE=config.ME2_TABLENAME2), table_name):
            return jsonify({"code": -1, "data": "改表名已存在"})
        elif not conn.query_one('select * from {TABLE} where id = %s'.format(TABLE=config.ME2_TABLENAME3), table_type):
            return jsonify({"code": -1, "data": "表类型不存在"})
        else:
            groupid = conn.query_one('select groupid from {TABLE} where type_name = %s'.format(TABLE=config.ME2_TABLENAME1), group_name)
            if groupid:
                try:
                    conn.insert_one(
                        'insert into {TABLE}(worksheet_name,groupid,origin_type_id) values(%s,%s,%s)'.format(TABLE=config.ME2_TABLENAME2),
                        [table_name, groupid, table_type])
                except Exception as e:
                    return jsonify({"code": -1, "data": "创建表失败"})
                else:
                    return jsonify({"code": -1, "data": "操作成功"})
            else:
                return jsonify({"code": -1, "data": "该分组不存在"})


@public_data.route("/save_pctable/", methods=['POST'])
def save_pctable():
    """
    保存工作表
    :return:
    """
    obj = request.get_json()
    table_type = obj["tableType"]
    change_table_datas = obj["changeTableDatas"]
    uid = g.token.get("id")
    conn = mysqlpool.get_conn()
    with conn.swich_db("%s_db" % uid,cursor=pymysql.cursors.Cursor) as cursor:
        for ctd in change_table_datas:
            if len(ctd):
                table_name = Pinyin().get_pinyin(ctd["tableName"], '')
                if conn.query_one('select * from {TABLE} where worksheet_name = %s'.format(config.ME2_TABLENAME2), table_name):
                    return jsonify({"code": -1, "data": "%s表已存在" % ctd["tableName"]})
                else:
                    try:
                        conn.insert_one(
                            'insert into {TABLE}(worksheet_name,groupid,worksheet_name_cn,origin_type_id) values(%s,%s,%s,%s)'.format(config.ME2_TABLENAME2),
                            [table_name, ctd["groupName"], ctd["tableName"], table_type])
                        cursor.commit()
                    except Exception as e:
                        return jsonify({"code": -1, "data": 'insert into' + str(e)})
                    try:
                        conn.create(
                            'create table ' + table_name + '_cn' + ' (id int primary key auto_increment,prime_name varchar(128),cn_name varchar(128),status int default 1)')
                        cursor.commit()
                    except Exception as e:
                        return jsonify({"code": -1, "data": str(e)})
                    try:
                        conn.insert_many(
                            'insert into ' + table_name + '_cn' + '(prime_name,cn_name,status) values(%s,%s,%s)',
                            [tuple(i.values())[0:3] for i in ctd["tableField"]])
                        cursor.commit()
                    except Exception as e:
                        return jsonify({"code": -1, "data": str(e)})
                    try:
                        conn.show('use %s;'%config.WOWRKSHEET01)
                        oldb = conn.query_all(
                            'select ds.link,cl.firTitle,cl.subTitle from {TABLE1} as ds,{TABLE2} as cl where cl.id = %s and ds.id = cl.datasourceId;'.format(TABLE1=config.TABLENAME4,TABLE2=config.TABLENAME46),
                            ctd["tableId"])[0]
                        conn.show("use %s_db" % uid)
                        old_table = oldb[0].replace('jdbc:mysql://127.0.0.1:3306/', '')
                        conn.create('create table ' + table_name + ' like ' + old_table + '.fetchdata_prp;')
                        cursor.commit()
                        conn.insert_one(
                            'insert into ' + "%s_db" % uid + '.' + table_name + ' select * from ' + old_table + '.fetchdata_prp where t1=%s and t2=%s;',
                            [oldb[1], oldb[2]])
                        cursor.commit()
                    except Exception as e:
                        return jsonify({"code": -1, "data": 'select' + str(e)})

    return jsonify({"code": 1, "data": "操作成功"})


@public_data.route("/cache_target/", methods=['POST'])
def cache_target():
    """
    缓存指标
    :return:
    """
    obj = request.get_json()
    token = obj["token"]
    datasource_id = obj["datasourceId"]
    reids_key = TokenMaker().generate_token(token, datasource_id)
    redis.set(reids_key, )


@public_data.route("/crawl_go/", methods=['POST'])
def crawl_go():
    update_frequency_list = ["DAYS","HOURS","MINUTES"]
    obj = request.get_json()
    website_link = obj.get('websiteLink') # 爬取url
    update_frequency = obj.get('updateFrequency') # 更新频率
    every_value = obj.get('every') # 间隔值
    remark = obj.get('remark') # 说明
    table_name = obj.get('tableName') # 表名
    token = g.token.get('token')
    update_type = obj.get("updateType") # 更新数据类型
    data_type_dict = {2:'DXYarea',1:'DXYOverall',3:'DXYNews',4:'MoveInFSCount',5:'FSqzhx',6:'DXYProvinces',7:'DXYgd',8:'DXYGDarea',9:"DXYfs"}
    data_type = data_type_dict.get(obj.get('dataType')) # 分类（暂定）
    crontab = obj.get('crontab')
    crontab_hour = obj.get('crontabHour')
    crontab_minute = obj.get('crontabMinute')
    """
    1:全国
    2：省市
    3：新闻
    4: 佛山迁入占比
    5：佛山确诊人员画像
    6：省疫情数据
    7：广东全省疫情数据
    8：广东省各市疫情数据
    9：佛山疫情数据
    10：来粤来佛人数登记
    11：来佛人员与车辆变化趋势
    12：12345热线数据
    13：防控动态
    """
    uid = g.token.get("id") # 用户ID

    impomodule = importlib.import_module("utils.govdatacrawl.%s"%data_type)
    main_run = getattr(impomodule,'main') # 执行爬虫

    res = main_run()

    redis.set("%s:crawl_data"%token, demjson.encode(res))
    redis.expire("%s:crawl_data"%token, 1800)
    if crontab == 0 and update_frequency in update_frequency_list:
        task_id = TokenMaker().generate_token(token,datetime.datetime.now())
        task_msg = {'crontab':crontab,'update_frequency':update_frequency,'task_id':task_id,'every_value':every_value,"website_link":website_link,"data_type":data_type,'update_type':update_type,'remark':remark}
        redis.set('%s:task_msg'%uid, demjson.encode(task_msg))
        redis.expire('%s:task_msg'%uid, 1800)
        return jsonify({'code':1,'task_id':task_id,'crawl_data':res,'table_name':table_name})
    elif crontab == 1:
        crontab_hour = str(int(crontab_hour))
        crontab_minute = str(int(crontab_minute))
        task_id = TokenMaker().generate_token(token,datetime.datetime.now())
        task_msg = {'crontab':crontab,'crontab_hour':crontab_hour,'task_id':task_id,'crontab_minute':crontab_minute,"website_link":website_link,"data_type":data_type,'update_type':update_type,'remark':remark}
        redis.set('%s:task_msg'%uid, demjson.encode(task_msg))
        redis.expire('%s:task_msg'%uid, 1800)
        return jsonify({'code':1,'task_id':task_id,'crawl_data':res,'table_name':table_name})

    return jsonify({'code':1,'task_id':None,'crawl_data':res,'table_name':table_name})




@public_data.route("/save_table/", methods=['POST'])
def save_table():
    """
    保存工作表
    """
    uid = g.token.get("id")
    obj = request.get_json()
    token = obj.get("token")
    remark = obj.get("remark")
    change_table_datas = obj["changeTableDatas"]
    table_type = obj.get("tableType")
    task_id = obj.get("taskId")
    conn = mysqlpool.get_conn()
    dbtype = None
    res = demjson.decode(redis.get("%s:crawl_data"%token))
    if res:
        with conn.swich_db("%s_db" % uid) as cursor:
            for ctd in change_table_datas:
                tb_name = str(uuid.uuid4()).replace(' ','').replace('-','')
                conn.drop('drop table if EXISTS `%s`' % tb_name)
                conn.drop('drop table if EXISTS `%s`' % (tb_name + "_cn"))
                conn.commit()
                try:
                    conn.insert_one(
                        'insert into {}(worksheet_name,types,worksheet_name_cn,groupid,origin_type_id) values(%s,%s,%s,%s,%s)'.format(
                            config.ME2_TABLENAME2),
                        [tb_name, dbtype, ctd["chineseTableName"], ctd["groupName"], table_type])
                except Exception as e:
                    conn.rollback()
                    return jsonify({"code": -1, "data": "插入关键数据失败", "mis":str(e)})
                try:
                    conn.create(
                        'create table ' + tb_name + '_cn' + ' (id int primary key auto_increment,prime_name varchar(128),cn_name varchar(128),status int default 1)')
                except Exception as e:
                    conn.rollback()
                    return jsonify({"code": -1, "data": "创建失败"})
                try:
                    conn.insert_many(
                        'insert into ' + tb_name + '_cn' + '(prime_name,cn_name,status) values(%s,%s,%s)',
                        [(i["englishName"], i["chineseName"], i["code"]) for i in ctd["tableField"]])
                except Exception as e:
                    conn.rollback()
                    return jsonify({"code": -1, "data": "插入数据失败"})

                try:
                    
                    
                    columns_list = list(res[0].keys())
                    baifens = '%s,'
                    field_sentence = ""
                    for j in range(len(columns_list)):
                        baifens += '%s,'
                        field_sentence += "`%s` text,"%columns_list[j] 

                    create_sentence = "CREATE TABLE `%s` (worksheet_id varchar(32) NOT NULL,"%tb_name + field_sentence + "UNIQUE KEY `worksheet_id` (`worksheet_id`) USING BTREE) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC"

                    conn.create(create_sentence)
                    insert_sentence = 'insert into `%s` (%s)'%(tb_name,"worksheet_id,%s"%','.join(res[0].keys())) + ' values(' + baifens[:-1] + ')'
                    insert_data = []
                    for v in res:
                        for v_value in v:
                            if type(v[v_value]) in [list,dict]:
                                v[v_value] = demjson.encode(v[v_value])

                        insert_data.append(tuple([TokenMaker().generate_token('worksheet_id',demjson.encode(v.values(),encoding="utf-8"))]+list(v.values())))
                    conn.insert_many(insert_sentence,insert_data)

                except Exception as e:
                    conn.rollback()
                    # raise e
                    return jsonify({"code": -1, "data": "操作失败"})
        if task_id:
            
            task_msg = demjson.decode(redis.get('%s:task_msg'%uid))
            
            datetimenow = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            
            if task_msg['crontab'] == 0:
                conn = mysqlpool.get_conn()
                with conn.swich_db(config.WOWRKSHEET01,cursor=pymysql.cursors.Cursor) as cursor:
                    conn.insert_one("insert into {TABLE}(id,uid,remark,updateFrequency,tableName,websiteLink,createDate) values(%s,%s,%s,%s,%s,%s,%s)".format(TABLE=config.TABLENAME49)
                        ,[task_id,uid,task_msg["remark"],task_msg["update_frequency"],tb_name,task_msg["website_link"],datetimenow])
                beat_session = Session()
                with session_cleanup(beat_session):
                    schedule = beat_session.query(IntervalSchedule).filter_by(every=task_msg["every_value"],period=getattr(IntervalSchedule,task_msg["update_frequency"])).first()
                    if not schedule:
                        schedule = IntervalSchedule(every=task_msg["every_value"], period=getattr(IntervalSchedule,task_msg["update_frequency"]))
                        beat_session.add(schedule)
                    task = PeriodicTask(id=task_id,uid=uid,interval=schedule,name='crawl_task_%s'%task_id,task='tasks.tasks_general.datacrawl',args=json.dumps([uid,task_id,task_msg["update_type"],task_msg["data_type"]]),last_run_at=datetimenow,description=remark,table_name=tb_name)
                    beat_session.add(task)
                    beat_session.commit()
            elif task_msg['crontab'] == 1:
                conn = mysqlpool.get_conn()
                with conn.swich_db(config.WOWRKSHEET01,cursor=pymysql.cursors.Cursor) as cursor:
                    conn.insert_one("insert into {TABLE}(id,uid,remark,tableName,websiteLink,createDate) values(%s,%s,%s,%s,%s,%s)".format(TABLE=config.TABLENAME49)
                        ,[task_id,uid,task_msg["remark"],tb_name,task_msg["website_link"],datetimenow])
                beat_session = Session()
                with session_cleanup(beat_session):
                    schedule = beat_session.query(CrontabSchedule).filter_by(minute=task_msg["crontab_minute"],hour=task_msg["crontab_hour"],timezone=config.TIMEZONE).first()
                    if not schedule:
                        schedule = CrontabSchedule(minute=task_msg["crontab_minute"],hour=task_msg["crontab_hour"],timezone=config.TIMEZONE)
                        beat_session.add(schedule)
                    task = PeriodicTask(id=task_id,uid=uid,crontab=schedule,name='crawl_task_%s'%task_id,task='tasks.tasks_general.datacrawl',args=json.dumps([uid,task_id,task_msg["update_type"],task_msg["data_type"]]),last_run_at=datetimenow,description=remark,table_name=tb_name)
                    beat_session.add(task)
                    beat_session.commit()
            else:
                return jsonify({"code": -1, "data": "操作失败"})
            
            
        return jsonify({"code": 1, "data": "操作成功"})
    else:
        return jsonify({"code": -1, "data": "数据不能为空"})