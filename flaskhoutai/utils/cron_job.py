from gevent import monkey;monkey.patch_all()
import gevent
from utils.dbutils import mysqlpool
import pymysql
from instance import config
import datetime
from apscheduler.schedulers.gevent import GeventScheduler
import ast
import uwsgi
from utils.dingding_util import ding


# 定时任务 修改表中isshare 分享状态
def update_isshare(isshare,sharetime,layoutid):
    conn = mysqlpool.get_conn()
    with conn.swich_db(config.WOWRKSHEET01) as cursor:
        token_cn = ""
        url2 = ""
        conn.update("update {} set isshare=%s,sharetime=%s,url2=%s, token_cn=%s where layoutid=%s".format("layoutmsg"),[isshare,sharetime,url2,token_cn,layoutid])
        conn.commit()

def job_issue_token():
    conn = mysqlpool.get_conn()
    with conn.swich_db('test') as cursor:
        conn.insert_one('insert into schedler(tsam) value(%s)',datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        conn.commit()

class RunAPScheduler:
    def __init__(self, apscheduler):
        self.apscheduler = apscheduler
        self.load_scheduler()
        self.scheduler_all(self.load_scheduler())

    def load_scheduler(self):
        """加载任务"""
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            scheduler_list = conn.query_all("select * from {}".format(config.TABLENAME25))
        return self.check_scheduler(scheduler_list)

    def check_scheduler(self,scheduler_list):
        """检验任务有效性"""
        for sl in scheduler_list:
            if not sl['flag']:
                scheduler_list.remove(sl)
            else:
                key_list = []
                for i in sl:
                    if sl[i] == None:
                        key_list.append(i)
                for j in key_list:
                    sl.pop(j)
            sl['func'] = globals()[sl['func']]
            if sl.get('args'):
                sl['args'] = ast.literal_eval(sl['args'])
        return scheduler_list


    # 添加调度任务且执行
    def scheduler_all(self,scheduler_list):
        for sl in scheduler_list:
            sl.pop('createDate')
            sl.pop('uid')
            sl.pop('flag')
            sl['id'] = str(sl['id'])
            self.apscheduler.add_job(**sl)


#bs = GeventScheduler()
#RunAPScheduler(bs)
#bt = bs.start()
#bt.join()

