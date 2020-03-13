#! usr/bin/python3
# -*- coding: utf-8 -*-
"""
隐秘配置变量
"""

import os

SECRET_KEY = os.urandom(24)
TIMEZONE = 'Asia/Shanghai'
COMMAND_DIR = r'/usr/local/flask_houtai/flaskhoutai/env/bin'
SUPERVISORD_PW = 'jcxt@123456'
SUPERVISORD_USER = 'zjx'

# MySQL数据库
WOWRKSHEET = "zjx_worksheet"
WOWRKSHEET01 = "component_management"
WOWRKSHEET02 = "user_database"

# 数据库名称
DBNAME1 = 'component_management'
DBNAME2 = 'zjx_worksheet'

"""表名"""
TABLENAME1 = 'algorithmic_analysis'
TABLENAME2 = 'algorithmic_analysis_categories'
TABLENAME3 = 'test_tubiao_goucheng'
TABLENAME4 = 'datasource'
TABLENAME5 = "data_overview_template"
TABLENAME6 = "smallArr_snapshot"
TABLENAME7 = "bigArr_snapshot"
TABLENAME8 = "history_snapshot"
TABLENAME9 ="report_db"
TABLENAME10 ="quota_overview_template"
TABLENAME11 ="quota_overview_entity"
TABLENAME12 = "report_history_data"
TABLENAME13 = "reserve_plan"
TABLENAME14 = "routetable"
TABLENAME15 = "routeinfo_big"
TABLENAME16 = "userinfo"
TABLENAME17 = "roleinfo"
TABLENAME18 = "route_title"
TABLENAME19 = "roles_users"
TABLENAME20 = "layoutmsgcontent"
TABLENAME21 = "department"
TABLENAME22= "layout_passwords"
TABLENAME23= "component_category"
TABLENAME24= "report_style"
TABLENAME25 = "scheduler_python"
TABLENAME26 = "push_report"
TABLENAME27 = "analysis_report"
TABLENAME28 = "push_report_privilege"
TABLENAME29 = "layout"
TABLENAME30 = "analysis_report_part"
TABLENAME31 = "analysis_report_part_descriptions"
TABLENAME32 = "push_type"
TABLENAME33 = "databigscreengroup"
TABLENAME34 = "collection"
TABLENAME35 = "databigcreencontent"
TABLENAME36 = "hardware_big_screen_resources"
TABLENAME37 = "hardware_big_screen_resources_unit"
TABLENAME38 = "scheduling_period_appointment"
TABLENAME39 = "scheduling_period"
TABLENAME40 = "scheduling"
TABLENAME41 = "report_excel"
TABLENAME42 = "algorithmic_model"
TABLENAME43 = "datareportgroup"
TABLENAME44 = "analysisreportgroup"
TABLENAME45 = "algorithmic_assessment"
TABLENAME46 = "crawler_list"
TABLENAME47 = "user_database"
TABLENAME48 = "url2_share"
TABLENAME49 = "crawler"
TABLENAME50 = "celery_periodic_task"
TABLENAME51 = "celery_interval_schedule"
TABLENAME52 = "report_push_email"
TABLENAME53 = "celery_crontab_schedule"
TABLENAME54 = "dbcrawler"
"""表名"""
ME2_TABLENAME1 = 'worksheet_classification'
ME2_TABLENAME2 = 'worksheet_relation'
ME2_TABLENAME3 = 'origin_type'
ME2_TABLENAME4 = 'association_table_relation'

# Redis数据库

REDIS_HOST = "120.31.140.112"
REDIS_PORT = 6380
REDIS_PASSWORD = 'jcxt@123456'
REDIS_DB = 0
REDIS_DECODE_RESPONSES = 1
REDIS_ENCODING = 'utf-8'
REDIS_ENCODING_ERRORS = 'ignore'
REDIS_SOCKET_CONNECT_TIME = 1

# mongodb数据库
M_HOST = "120.31.140.112"
M_PORT = 27017
M_USER = "root"
M_PASSWORD = 'jcxt@123456'

M_DB = "admin"
M_DBNAME = "ex_infos"
M_DBNAME1 = "userconfig"
M_TABLENAME = "newinfos"

M_COLLECTION1 = "user_algorithmic_data"
M_COLLECTION2 = "algorithm_output"

# 增加算法的上传文件保存的路径
FILE_PATH = "/usr/local/algorithm/algolib+uid"

# 钉钉路径
DING_URL = "https://oapi.dingtalk.com/robot/send?access_token=166d37ce49cbea2516ac52f6b3fd1ed53cad7e8dfdb607df5835875e3cac16c7"

# mysql连接池
DB_HOST = '120.31.140.112'
DB_PORT = 3306
DB_USER = 'f_user'
DB_PASS = 'jcxt@123456'
DB_POOL_MAX_CONN = 8


# 跳过token验证
tokenpath=["/layout/shareurl/", "/layout/is_identifying/","/databigscreen/shareurl/","/operation_worksheet/return_component_con/"]
# 基础角色id
roleid="bc9359dc-1d1d-11e7-a8b1-ce19120e1336"

# celery
from kombu import Exchange
from kombu import Queue
BEAT_DB = 'test'
DB_ADMIN = 'component_management'

# BROKER_URL = 'redis://:{ps}@{host}:{port}/3'.format(ps=REDIS_PASSWORD,host=REDIS_HOST,port=REDIS_PORT)
# CELERY_RESULT_BACKEND = 'redis://:{ps}@{host}:{port}/4'.format(ps=REDIS_PASSWORD,host=REDIS_HOST,port=REDIS_PORT)
# CELERY_INCLUDE = ['tasks.tasks_general']
# CELERY_TIMEZONE = 'Asia/Shanghai'
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_RESULT_ACCEPT_CONTENT = ['json']
# CELERY_TASK_TRACK_STARTED = True
# CELERY_DISABLE_RATE_LIMITS = True
# CELERY_RESULT_EXPIRES = 1800
# CELERY_WORKER_SEND_TASK_EVENTS = "enabled"
# CELERY_TASK_SEND_SENT_EVENT = "enable"
# CELERY_REDIRECT_STDOUTS_LEVEL = 'INFO'
# # CELERY_QUEUES = (
# #     Queue("tasks_general", Exchange("tasks_general"), routing_key="tasks_general"),
# # )

# # CELERY_ROUTES = {
# #     'tasks.tasks_general.*': {"queue": "tasks_general", 'exchange':"tasks_general","routing_key": "tasks_general"},
# # }
# CELERYD_MAX_TASKS_PER_CHILD = 100
# CELERYBEAT_MAX_LOOP_INTERVAL = 10
# CELERYBEAT_SYNC_EVERY = 0
# CELERY_TRACE_APP = 0 # 生产环境关闭
# CELERY_ENABLE_UTC = True



# beat_dburi = "mysql+pymysql://{ROOT}:{PASS}@{HOST}:{PORT}/{TABLE}".format(ROOT=DB_USER, PASS=DB_PASS,
#                                                                                        HOST=DB_HOST, PORT=DB_PORT,
#                                                                                        TABLE=BEAT_DB)


broker_url = 'redis://:{ps}@{host}:{port}/3'.format(ps=REDIS_PASSWORD,host=REDIS_HOST,port=REDIS_PORT)
result_backend = 'redis://:{ps}@{host}:{port}/4'.format(ps=REDIS_PASSWORD,host=REDIS_HOST,port=REDIS_PORT)
include = ['tasks.tasks_general']
timezone = 'Asia/Shanghai'
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
result_accept_content = ['json']
# result_expires = 1800
worker_send_task_events = "enabled"
task_send_sent_event = "enable"
worker_redirect_stdouts_level = 'INFO'
worker_max_tasks_per_child = 100
enable_utc = False
task_ignore_result = True
task_store_errors_even_if_ignore = True
beat_dburi = "mysql+pymysql://{ROOT}:{PASS}@{HOST}:{PORT}/{TABLE}".format(ROOT=DB_USER, PASS=DB_PASS,
                                                                                       HOST=DB_HOST, PORT=DB_PORT,
                                                                                       TABLE=BEAT_DB)


BABEL_DEFAULT_LOCALE = "zh_CN"

SQLALCHEMY_DATABASE_URI = "mysql+pymysql://{ROOT}:{PASS}@{HOST}:{PORT}/{TABLE}".format(ROOT=DB_USER, PASS=DB_PASS,
                                                                                       HOST=DB_HOST, PORT=DB_PORT,
                                                                                       TABLE=DB_ADMIN)
SQLALCHEMY_ECHO = True
SQLALCHEMY_POOL_SIZE = 100
SQLALCHEMY_POOL_RECYCLE = 25200
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_MAX_OVERFLOW = 20
SQLALCHEMY_MAX_OVERFLOW = 20
SQLALCHEMY_POOL_SIZE = 40
# 算法代码地址
ALGORITHM_PATH = r'/usr/local/algorithm/algolib'
EVALUATE_PATH = r'/usr/local/algorithm/evaluate'
PYTHON_PATH = r'/usr/local/flask_houtai/flaskhoutai/env/bin/python'

# 数据迁移相关配置
DATA_PRETREATMENT_SIZE = 1000
DATA_RECURSION_SIZE = 10000

# 图片保存路径
IMGROUTE = '/usr/local/bigscreen'
SNAPSHOTROUTE = '/componentManagement/upload/imgFlow'
DATABATESCREEN = "/usr/local/bigscreen/componentManagement/upload/bigscreen/bigscreen_"
DATABIGPATH= "/upload/bigscreen/bigscreen_"
DATAREPORT01= "/usr/local/bigscreen/componentManagement/upload/reportDB/reportDB_"
DATAREPORT02= "/usr/local/bigscreen/componentManagement/upload/reportDB/shoujiduan_"
DATAREPORTPATH02 = "/upload/reportDB/shoujiduan_"
DATAREPORTPATH = "/upload/reportDB/reportDB_"
ANALYSISREPORT01= "/usr/local/bigscreen/componentManagement/upload/analysisReport/analysisReport_"
ANALYSISREPORTPATH = "/upload/analysisReport/analysisReport_"
LAYOUT01 = "/usr/local/bigscreen/componentManagement/upload/layout/layout_"
LAYOUTPATH =  "/upload/layout/layout_"
CHARPATH= "/upload/chart/chart_"
QUOTA01 = "/usr/local/bigscreen/componentManagement/upload/quota/quota_"
QUOTAOPATH= "/upload/quota/quota_"
SERVERCHART01= "/usr/local/bigscreen/componentManagement/upload/chart/chart_"
SERVERCHARTPATH= "/upload/chart/chart_"

# 我的信箱 下载接口
IMGROUTE_SERVER= 'http://120.31.140.112:8091/componentManagement/'

# email
EMAIL_SENDER = 'jcxtSender'

IMG_SERVER_HOST = 'http://127.0.0.1:'
IMG_SERVER_PORT = '80'
IMG_SERVER_URL = '/#/phoneSize/'
CHROME_DIR = '/home/myadmin.fs/flaskhoutai/chromedriver'