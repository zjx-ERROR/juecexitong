#! usr/bin/python3
# -*- coding: utf-8 -*-
from flask_redis import Redis
import pymysql
from instance import config
import gevent
from gevent import queue
from contextlib import contextmanager


# Redis实例
# redis_conn = redis.Redis(host=config.REDIS_HOST,port=config.REDIS_PORT,db=config.REDIS_DB,decode_responses=config.REDIS_DECODE_RESPONSES,encoding_errors=config.REDIS_ENCODING_ERRORS,socket_connect_timeout=config.REDIS_SOCKET_CONNECT_TIME)
redis = Redis()


def makeDictFactory(cursor):
    columnNames = [d[0] for d in cursor.description]
    def createRow(*args):
        return dict(zip(columnNames, args))
    return createRow

class ConnectionPool(object):

    """连接池"""

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls,'instance'):
            cls.instance = super(ConnectionPool,cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.max_conn = config.DB_POOL_MAX_CONN
        self._pool = queue.Queue(maxsize=self.max_conn)
        for _ in range(self.max_conn):
            conn = Connection(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                passwd=config.DB_PASS,
                charset='utf8'
            )
            conn._pool = self
            self._pool.put(conn)

    def get_conn(self, retry=3):
        """取出一个连接"""
        try:
            return self._pool.get()
        except:
            # 重试3次
            gevent.sleep(0.1)
            if retry > 0:
                retry -= 1
                return self.get_conn(retry)
            else:
                raise queue.Empty

    def put_conn(self, conn):
        """存入一个连接"""
        if not conn._pool:
            conn._pool = self
        try:
            self._pool.put(conn)
        except:
            raise queue.Full

    def size(self):
        """可用连接数"""
        return self._pool.qsize()


class Connection(pymysql.connections.Connection):


    """数据库连接"""
    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        self._pool = None
        self._cursor = None

    @contextmanager
    def swich_db(self,db,cursor=pymysql.cursors.DictCursor):
        self.ping(reconnect=1)
        self.select_db(db)
        self._cursor = self.cursor(cursor=cursor)
        yield self._cursor
        self.dispose()

    def _execute(self, query, *args):
        """执行"""
        try:
            return self._cursor and self._cursor.execute(query, *args)
        except Exception as e:
            self.rollback()
            raise e

    def _executemany(self, query, args):
        """执行"""
        try:
            return self._cursor and self._cursor.executemany(query, args)
        except Exception as e:
            self.rollback()
            raise e

    def query_all(self, query, *args):
        """查询结果集"""
        count = self._execute(query, *args)
        return count and self._cursor.fetchall()

    def query_many(self, query, num, *args):
        """查询结果集"""
        count = self._execute(query, *args)
        return count and self._cursor.fetchmany(num)

    def query_one(self, query, *args):
        """查询单一记录"""
        count = self._execute(query, *args)
        return count and self._cursor.fetchone()

    def insert_one(self, query, *args):
        """插入单一行"""
        count = self._execute(query, *args)
        return count and self._cursor.lastrowid

    def insert_many(self, query, *args):
        """插入多行"""
        count = self._executemany(query, *args)
        return count

    def update(self, query, *args):
        """修改"""
        count = self._execute(query, *args)
        return count

    def delete(self, query, *args):
        """删除"""
        count = self._execute(query, *args)
        return count

    def show(self, query, *args):
        """展示"""
        count = self._execute(query, *args)
        return count

    def drop(self, query, *args):
        """删除"""
        count = self._execute(query, *args)
        return count

    def create(self, query, *args):
        """创建"""
        count = self._execute(query, *args)
        return count

    def dispose(self):
        """关闭游标"""
        self.commit()
        self._cursor and self._cursor.close()
        self._pool.put_conn(self)
        

mysqlpool = ConnectionPool()