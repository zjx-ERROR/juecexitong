from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app.backstage.model import User
from utils.dbutils import db_session
# from app.apis.model import Cwebapi
# from app.apis.model import Datasource
from flask_admin import AdminIndexView
from wtforms import validators
from wtforms import SelectField
from flask_admin.contrib import rediscli
# from utils.dbutils import redis

class WebpaiModelView(ModelView):
    page_size = 8
    can_create = True
    can_edit = True
    can_delete = True
    edit_modal = True
    create_modal = True
    # can_view_details = True


class UserView(WebpaiModelView):
    column_labels = {"UserName": u'用户名', "LastLoginTime": "最新登录时间", "Mobile": "手机/电话", "Email": "邮箱", "loginIp": "登陆IP"}
    column_exclude_list = ()


class ApiView(WebpaiModelView):
    column_exclude_list = ['flag', 'sql_view']
    column_labels = {'api_name': '接口名', 'api': '接口函数', 'params': '参数', 'deal_params':'参数处理','remark': '说明', 'status': '是否启用',
                     'sql_view': '查询语句','cache_time':'缓存时间（秒）'}
    form_excluded_columns = ['flag']
    column_formatters = {'status': lambda v, c, m, p: ['启用' if m.status == 1 else '关闭']}

class SourceView(WebpaiModelView):
    column_exclude_list = ['passwd', 'flag']
    column_labels = {"source_name": "数据源名称", "type": "数据源类型", "ip": "数据源IP", "port": "数据源端口", "account": "用户名",
                     "passwd": "密码", "remark": "说明"}
    form_excluded_columns = ['flag']
    form_overrides = {"type": SelectField}
    form_args = {"type": {'validators': [validators.DataRequired(message='数据类型不能为空')],
                          "choices": (('mysql', 'mysql'), ('oracle', 'oracle'))},
                 "source_name": {'validators': [validators.DataRequired(message='数据源名称')]},
                 "ip": {'validators': [validators.DataRequired(message='数据源IP')]},
                 "port": {'validators': [validators.DataRequired(message='数据源端口')]}}


admin = Admin(template_mode='bootstrap3', name="大屏后台管理系统", index_view=AdminIndexView(name=u"首页"))
admin.add_view(UserView(User, db_session, name=u'用户管理'))
# admin.add_view(rediscli.RedisCli(redis))
# admin.add_view(ApiView(Cwebapi, db_session, name=u'API管理', category="接口管理"))
# admin.add_view(SourceView(Datasource, db_session, name=u'数据源管理', category="接口管理"))
