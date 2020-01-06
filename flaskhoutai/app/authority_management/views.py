from flask import Blueprint, request, jsonify, Response, g
from utils.dbutils import mysqlpool
from instance import config
import pymysql
from flask import g
from utils.json_helper import DateEncoder
import json
import random
import copy
from functools import reduce

# 创建后台 的蓝图  首页
authority_management = Blueprint("authority_management", __name__)


@authority_management.route("/select_authority/", methods=["POST"])
def select_authority():
    """全部用户权限查找"""
    json_data = request.get_json()
    # 获取当前页数
    page = json_data["page"]
    # 获取当前信息数量
    total = json_data["pageSize"]
    return_dic = {}
    try:
        # 获取全部角色
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            roles_list = conn.query_all(
                "select id, RoleName,Roledescribe,role_route  from {}".format(config.TABLENAME17))
            # 总数量
            count = len(roles_list)
            # 总页数
            pages = count // total if count % total == 0 else count // total + 1
            rows_list = []
            if total <= count and page == 1:
                roles_list = conn.query_all(
                    "select id, RoleName,Roledescribe,role_route from {} LIMIT %s ".format(config.TABLENAME17), [total])
            elif total > count and page == 1:
                roles_list = roles_list
            elif count > total and 1 < page <= pages:
                roles_list = conn.query_all(
                    "select id, RoleName,Roledescribe,role_route  from {} LIMIT %s,%s ".format(config.TABLENAME17),
                    [(page - 1) * total, total])

            for i in roles_list:
                role_id = i["id"]
                # 获取角色下的所有用户
                users_list = conn.query_all("select username from {} where roleid=%s".format(config.TABLENAME19),
                                            [role_id])
                users = []
                for j in users_list:
                    users.append(j["username"])
                # 角色描述信息
                roledescribe = i["Roledescribe"]
                # 获取角色下的包含的所有用户
                role_users = users
                # 获取角色 路由权限
                role_route = i["role_route"]
                role_dic = {}
                role_dic["role_id"] = role_id
                role_dic["role_name"] = i["RoleName"]
                role_dic["role_usernames"] = role_users
                routes = role_route.replace("'", "\"").replace("True", "true").replace("False", "false")
                role_dic["role_route"] = json.loads(routes)
                role_dic["roledescribe"] = roledescribe
                rows_list.append(role_dic)

        return_dic["page"] = page
        return_dic["total"] = count
        return_dic["rows"] = rows_list
        return jsonify({
            "code": 1,
            "data": return_dic
        })

    except Exception as e:
        raise e


@authority_management.route("/users_msg/", methods=["POST"])
def users_msg():
    """获取所有用户信息"""
    json_data = request.get_json()
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            users_list = conn.query_all("select id,UserName,RoleID,RealName from {}".format(config.TABLENAME16))

        return jsonify({
            "code": 1,
            "data": users_list
        })
    except Exception as e:
        raise e


@authority_management.route("/update_authority/", methods=["POST"])
def update_authority():
    """用户权限信息修改"""
    json_data = request.get_json()["data"]
    roledescribe = json_data['roledescribe']
    role_id = json_data["role_id"]
    role_name = json_data["role_name"]
    role_route = json_data["role_route"]
    role_usernames = json_data["role_usernames"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            #  修改角色描述 角色名称 角色权限 角色用户 角色表  roleinfo表
            conn.update(
                "update {} set roledescribe=%s, RoleName=%s, role_route=%s where id= %s".format(config.TABLENAME17),
                [roledescribe, role_name, str(role_route), role_id])
            # 先删除 role_user表 用户信息 再添加数据
            conn.delete("DELETE from {} where roleid=%s".format(config.TABLENAME19), [role_id])
            for i in role_usernames:
                conn.insert_one("insert into {} (roleid, username) values (%s,%s)".format(config.TABLENAME19),
                                [role_id, i])
        return jsonify({
            "code": 1,
            "data": "修改成功"
        })
    except Exception as e:
        raise e


@authority_management.route("/add_authority/", methods=["POST"])
def add_authority():
    """增加用户权限信息"""
    json_data = request.get_json()["data"]
    roledescribe = json_data['roledescribe']
    role_id = g.token["token"][:-4] + str(random.randint(1000, 9999))
    role_name = json_data["role_name"]
    role_route = json_data["role_route"]
    # 角色用户列表
    role_usernames = json_data["role_usernames"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            # 添加 角色用户关系表 roles_user表
            for i in role_usernames:
                conn.insert_one("insert into {} (roleid, username) values (%s,%s)".format(config.TABLENAME19),
                                [role_id, i])
            #  添加角色描述 角色名称 角色权限 角色用户 角色表  roleinfo表
            conn.insert_one(
                "insert into {} (id, RoleName,Roledescribe,role_route) values (%s,%s,%s,%s)".format(config.TABLENAME17),
                [role_id, role_name, roledescribe, str(role_route)])
        return jsonify({
            "code": 1,
            "data": "增加成功"
        })
    except Exception as e:
        raise e


@authority_management.route("/del_authority/", methods=["POST"])
def del_authority():
    """删除用户权限信息"""
    json_data = request.get_json()
    # 获取角色id 可能删除多个角色id
    role_id = json_data["id"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            for i in role_id:
                conn.delete("DELETE from {} where id=%s".format(config.TABLENAME17), [i])
                conn.delete("DELETE from {} where roleid=%s".format(config.TABLENAME19), [i])
        return jsonify({
            "code": 1,
            "data": "删除角色成功"
        })
    except Exception as e:
        raise e


@authority_management.route("/authority/select/", methods=["POST"])
def select():
    """查找用户所有权限"""
    json_data = request.get_json()
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            roles_list = conn.query_all(
                "select id,name,icon,iconClass, path,children,isMail from {}".format(config.TABLENAME18))
        return jsonify({
            "code": 1,
            "data": roles_list
        })
    except Exception as e:
        raise e


@authority_management.route("/authority/", methods=["POST"])
def authority():
    """查找某个用户的权限"""
    json_data = request.get_json()
    username = g.token["userName"]
    title = json_data["title"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            roleID_list = conn.query_all("select roleid from {} where username=%s".format(config.TABLENAME19),
                                         [username])
            titlelist = []
            data_dic = {}
            for i in roleID_list:
                role_route = conn.query_one("select role_route from {} where id=%s".format(config.TABLENAME17),
                                            [i["roleid"]])
                roles = role_route["role_route"].replace("'", "\"").replace("True", "true").replace("False", "false")
                roles = json.loads(roles)

                for j in roles:
                    if j["checked"] == True and j["title"] not in titlelist:
                        data_dic[j["title"]] = j
                        titlelist.append(j["title"])
                    elif j["checked"] == True and j["title"] in titlelist:
                        list_all = data_dic[j["title"]]["children"] + j["children"]
                        data_dic[j["title"]]["children"] = list_all

        #  去重方法
        def dg(dict_like):
            data = dict_like["children"]
            if len(data) == 1:
                dict_like["children"] = reduce(lambda x, y: x if y in x else x + [y], [[], ] + data)
                return dict_like
            sn1 = 0
            while 1:
                del_list = []
                sn2 = sn1 + 1
                while 1:
                    data_co = copy.deepcopy(data)
                    if data[sn1] == data_co[sn2]:
                        del_list.append(sn2)
                    elif all([data[sn1].get("children"), data_co[sn2].get("children")]):
                        j = copy.deepcopy(data[sn1])
                        n = copy.deepcopy(data_co[sn2])
                        if j == n:
                            jc = j.pop("children")
                            nc = n.pop("children")
                            jc += nc
                            data[sn1]["children"] = jc
                            data[sn1] = dg(data[sn1])
                            del_list.append(sn2)
                    if sn2 >= len(data_co) - 1:
                        break
                    sn2 += 1
                dl = 0
                for i in del_list:
                    data.pop(i - dl)
                    dl += 1
                if del_list:
                    if sn1 >= len(data) - 1:
                        break
                elif sn1 >= len(data) - 2:
                    break
                sn1 += 1
            dict_like["children"] = data
            return dict_like

        for k, v in data_dic.items():
            data_dic[k] = dg(v)

        return_data = []
        return_data.append(data_dic[title])
        return jsonify({
            "code": 1,
            "data": return_data
        })
    except Exception as e:
        raise e
