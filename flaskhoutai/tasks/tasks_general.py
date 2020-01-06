from tasks.celery import celery
from instance import config
from utils.dbutils import mysqlpool
from datetime import datetime


# 例子

@celery.task
def add(a, b):
	conn = mysqlpool.get_conn()
	with conn.swich_db('test') as cursor:
		conn.insert_one('insert into celery_beat_test(createtime,numb) values(%s,%s)',[datetime.now().strftime('%y-%m-%d %H:%M:%S'),a+b])
	return '计算结果为：%s'%(a+b)


if __name__ == "__main__":
    pass
