from flask import Flask, Blueprint
import json
import os
import gevent
from utils.dbutils import redis
ws = Blueprint(r'websocket', __name__)



@ws.route('/sysupervisord')
def echo_socket(socket):
    while not socket.closed:
        message = socket.receive()
        print('接收socket数据：',message)
        socket.send(message)


@ws.route('/ws/<client_name>')
def send_socket(socket,client_name):
    channel = 'ws'
    rp = redis.pubsub()
    rp.subscribe(channel)

    while not socket.closed:
        listen_msg = rp.parse_response(block=False)
        message = socket.receive()
        if message:
            who_send_msg = {
                    "send_user": client_name,
                    "send_msg": message,
                }
            redis.publish(channel,json.dumps(who_send_msg))
        if listen_msg:
            if listen_msg[0] == 'message':
                try:
                    if json.loads(listen_msg[-1])['send_user'] == client_name:
                        continue
                except:
                    pass
            socket.send(json.dumps(listen_msg))
             
