## server mechanics
chdir = '/usr/local/flask_houtai/flaskhoutai'
pidfile = '%s/gunicorn.pid'%chdir
pythonpath = '%s/env/python/bin'%chdir

## server socket
bind = '127.0.0.1:833'
backlog = 1024

## worker 进程
workers = 7
worker_class = 'utils.websocket_util.worker'

# worker_connections = 1000
max_requests = 5000
max_requests_jitter = 1000
keepalive = 60

## security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 5120

## debugging
reload = True

## process naming
# proc_name = 'websocket_server'

## server hooks
