from flask import Blueprint, request, jsonify, Response
from utils.dingding_util import ding

import datetime
import traceback
import threading
import os
import ctypes

# 创建数据采集的蓝图
error_handler = Blueprint("error_handler", __name__)


@error_handler.app_errorhandler(500)
def server_error(e):
    thread_msg = 'thread:{},  pid={}, ppid={}'.format(threading.get_ident(), os.getpid(),
                                                      ctypes.CDLL('libc.so.6').syscall(186))
    ding('时间:%s\n请求IP:%s\n线程信息:%s\n%s\n' % (
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), request.remote_addr, thread_msg, traceback.format_exc()))
    return "服务器搬家了，程序狗累趴了( ▼-▼ )"


@error_handler.app_errorhandler(502)
def bad_gateway(e):
    thread_msg = 'thread:{},  pid={}, ppid={}'.format(threading.get_ident(), os.getpid(),
                                                      ctypes.CDLL('libc.so.6').syscall(186))
    ding('时间:%s\n请求IP:%s\n线程信息:%s\n%s\n' % (
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), request.remote_addr, thread_msg, traceback.format_exc()))
    return jsonify({"code": -1, "msg": "这。。。赶紧呼叫程序狗(●ˇ∀ˇ●)"})


@error_handler.app_errorhandler(400)
def bad_request(e):
    return jsonify({"code": -1, "msg": "400 您的请求失败"})


@error_handler.app_errorhandler(404)
def not_found(e):
    return jsonify({"code": -1, "msg": "404 您的请求失败"})
