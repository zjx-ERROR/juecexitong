#! usr/bin/python3

"""
初始化flask
"""

from flask import Flask
# from flask_cors import CORS
from utils.dbutils import redis
from utils.websocket_util import Sockets


def create_app():
    """创建app"""
    app = Flask(__name__, instance_relative_config=True)
    # CORS(app, supports_credentials=1)

    # 加载配置
    app.config.from_object('config.default')
    app.config.from_object('config.production')
    app.config.from_pyfile('config.py')

    # 加载socket
    sockets = Sockets(app)
    redis.init_app(app)
    
    # 接口返回乱码问题
    app.config['JSON_AS_ASCII'] = False

    # 注册增加算法的蓝图
    from app.algorithm.views import add_algorithm
    app.register_blueprint(add_algorithm, url_prefix="/algorithm")

    # 注册读取excel内容，存在mongodb数据库中相关操作的蓝图
    from app.operation_excel.views import operation_table
    app.register_blueprint(operation_table, url_prefix="/operation_table")

    # 注册操作关联表的蓝图
    from app.worksheet_relation_deal.views import operation_worksheet
    app.register_blueprint(operation_worksheet, url_prefix="/operation_worksheet")

    # 注册数据采集蓝图
    from app.collect_data.views import collect_data
    app.register_blueprint(collect_data, url_prefix="/collect_data")
    from app.public_data.views import public_data
    app.register_blueprint(public_data, url_prefix="/public_data")

    # 服务器钉钉蓝图注册
    from app.error_handler.views import error_handler
    app.register_blueprint(error_handler, url_prefix="/error_handler")

    # 注册组件联动蓝图
    from app.component_linkage.views import component_linkage
    app.register_blueprint(component_linkage, url_prefix="/component_linkage")

    # 注册 快照功能 蓝图
    from app.snapshot.views import snapshot_data
    app.register_blueprint(snapshot_data, url_prefix="/snapshot_data")

    # 注册 预案 蓝图
    from app.reserve_plan.views import reserve_plan
    app.register_blueprint(reserve_plan, url_prefix="/reserve_plan")

    # 注册后台 蓝图
    from app.backstage.views import backstage
    app.register_blueprint(backstage, url_prefix="/backstage")

    # 注册用户权限管理蓝图
    from app.authority_management.views import authority_management
    app.register_blueprint(authority_management, url_prefix="/authority_management")

    # 注册 布局 蓝图
    from app.layout.views import layout
    app.register_blueprint(layout, url_prefix="/layout")

    # 注册可视化应用蓝图
    from app.visualization_application.views import visualization_application
    app.register_blueprint(visualization_application, url_prefix="/visualization_application")

    # 注册数据报表应用蓝图
    from app.datareport.views import data_report
    app.register_blueprint(data_report, url_prefix="/data_report")

    # 注册数据大屏应用蓝图
    from app.databigscreen.views import databigscreen
    app.register_blueprint(databigscreen, url_prefix="/databigscreen")

    # 注册个人中心应用蓝图
    from app.personalcenter.views import personalcenter
    app.register_blueprint(personalcenter, url_prefix="/personalcenter")

    # 注册websocket蓝图
    from app.websocket_api.views import ws
    sockets.register_blueprint(ws,url_prefix="/websocket")
    
    return app
