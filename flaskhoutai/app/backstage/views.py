from flask import Blueprint, request, jsonify, g
from utils.dbutils import redis
from instance import config
import pymysql, re, string, random
from utils.token_utils import TokenMaker
import datetime, time
from utils.dbutils import mysqlpool
import uuid

# 创建后台 的蓝图  首页
backstage = Blueprint("backstage", __name__)


# http://120.31.140.112:8080/componentManagement/login  原登陆地址
@backstage.route("/login/", methods=["POST"])
def login():
    """用户登录功能"""
    json_data = request.get_json()
    userName = json_data["userName"]
    password = json_data["password"]
    if not all([userName, password]):
        return jsonify({
            "code": -1,
            "data": "缺少参数,请重新输入"})

    # 通过用户表获取token 相关信息 并判断账号密码是否正确
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            if conn.query_one(
                    "select id,DepartmentID,RoleID,UserName,RealName,Password,Mobile,Email,flag, status,remark,createDate,editDate from {} where UserName=%s".format(
                        config.TABLENAME16), userName):
                return_list = conn.query_one(
                    "select id,DepartmentID,RoleID,UserName,RealName,Password,Mobile,Email,flag, status,remark,createDate,editDate from {} where UserName=%s".format(
                        config.TABLENAME16), userName)
                # 账号密码正确
                if return_list["UserName"] == userName and return_list["Password"] == password:
                    # 判断redis 是否存有用户信息
                    token_key = ("userID:" + return_list["id"]).replace("'", "\"")
                    conn.commit()
                    if redis.exists(token_key):
                        # token = redis.get(token_key).decode()
                        token = redis.get(token_key)
                    else:
                        token = str(uuid.uuid1())
                    roleid = return_list["RoleID"]
                    conn.commit()
                    # 通过 user_database表判断用户是否为新用户
                    if not conn.query_one("select dbname from {} where flag=%s and uid=%s".format(config.TABLENAME47),
                                          [1, return_list["id"]]):
                        # 增加数据大屏默认分组   数据报表默认分组   分析报告分组
                        mo_name = "默认分组"
                        conn.insert_one(
                            "insert into {} (uid,groupname,flag) values (%s,%s,%s)".format(config.TABLENAME33),
                            [return_list["id"], mo_name, 1])
                        conn.insert_one(
                            "insert into {} (uid,groupname,flag) values (%s,%s,%s)".format(config.TABLENAME43),
                            [return_list["id"], mo_name, 1])
                        conn.insert_one(
                            "insert into {} (uid,groupname,flag) values (%s,%s,%s)".format(config.TABLENAME44),
                            [return_list["id"], mo_name, 1])
                        conn.commit()
                        # 创建新的数据库
                        dbname = return_list["id"] + "_db"
                        conn.create("create database {}".format(dbname))

                        # 并在新的数据库创建新的默认表
                        conn11 = mysqlpool.get_conn()
                        with conn11.swich_db(dbname):
                            conn11.create(
                                "CREATE TABLE `association_table`  (`id` int(11) NOT NULL AUTO_INCREMENT, `file_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL, `file_name_cn` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL, PRIMARY KEY (`id`) USING BTREE) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;")
                            conn11.create(
                                "CREATE TABLE `association_table_relation`  ( `id` int(11) NOT NULL AUTO_INCREMENT,`begin_table` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `end_table` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,`line` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `associated_field_01` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `associated_field_02` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, PRIMARY KEY (`id`) USING BTREE) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;")
                            conn11.create(
                                "CREATE TABLE `origin_type`  (`id` int(11) NOT NULL, `data_origin_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '数据来源类型',PRIMARY KEY (`id`) USING BTREE) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;")
                            conn11.create(
                                " CREATE TABLE `smallArr_snapshot`  ( `id` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `uid` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `thumbnail` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `categoryId` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,  `title` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `name1` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `value1` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `unit1` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `name2` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `value2` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,`unit2` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `name3` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,  `value3` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,  `unit3` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `name4` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,  `value4` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `unit4` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,  `name5` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `value5` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `unit5` varchar(254) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,`createDate` date NULL DEFAULT NULL, `editDate` date NULL DEFAULT NULL, `flag` int(11) NULL DEFAULT NULL) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;")
                            conn11.create(
                                "CREATE TABLE `test_tubiao_goucheng`  ( `id` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL, `uid` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '用户id', `username` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,  `thumbnail` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '缩略图地址', `theme` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,  `main_title` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '主标题', `subtitle` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '副标题',  `jsonstr` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'json',  `type` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '图表类型',  `other_opt` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,  `chartDataSourceId` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,  `mSchema` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `mTable` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `columnMap` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL, `createDate` datetime(0) NULL DEFAULT NULL, `editDate` datetime(0) NULL DEFAULT NULL, `flag` tinyint(4) NULL DEFAULT 1, `selectArr` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `selectVArr` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;")
                            conn11.commit()
                            conn11.create(
                                "CREATE TABLE `worksheet_classification`  ( `groupid` int(25) NOT NULL AUTO_INCREMENT, `type_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,`path` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, PRIMARY KEY (`groupid`) USING BTREE) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;")
                            conn11.create(
                                "CREATE TABLE `worksheet_relation`  (  `id` int(25) NOT NULL AUTO_INCREMENT,`worksheet_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,  `types` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `groupid` int(25) NULL DEFAULT NULL,  `worksheet_name_cn` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, `origin_type_id` int(100) NULL DEFAULT NULL,  PRIMARY KEY (`id`) USING BTREE) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;")
                            conn11.insert_one("insert into `origin_type` (id,data_origin_type) values (1, '文件')")
                            conn11.insert_one("insert into `origin_type` (id,data_origin_type) values (2, '数据库')")
                            conn11.insert_one("insert into `origin_type` (id,data_origin_type) values (3, '公开数据')")
                            conn11.commit()

                        # 更新用户与数据库关系表
                        conn.insert_one("insert into {} (uid,dbname,flag) values (%s,%s,%s)".format(config.TABLENAME47),
                                        [return_list["id"], dbname, 1])

                    # 更新userifo表  最新登录时间 IP地址
                    now_time = datetime.datetime.now()
                    date_time = now_time.strftime("%Y-%m-%d %H:%M:%S")
                    ip = request.remote_addr
                    conn.update(
                        "update {} set LastLoginTime=%s,loginIp=%s where UserName=%s".format(config.TABLENAME16),
                        [date_time, ip, userName])
                    conn.commit()
                    # 通过 roles_users表 查询用户关系的角色ID  一个用户可能关系多个角色
                    rolesid = conn.query_all("select roleid from {} where username=%s".format(config.TABLENAME19),
                                             [userName])
                    rolesid_list = []
                    # 如果在用户角色表中找不到用户角色  自动各用户最底层的角色
                    if rolesid == 0:
                        rolesid_list.append(config.roleid)
                        conn.insert_one("insert into {} (roleid,username) values (%s,%s)".format(config.TABLENAME19),
                                        [config.roleid, userName])
                    else:
                        for i in rolesid:
                            rolesid_list.append(i["roleid"])
                    redis_key = ("userID:" + token).replace("'", "\"")

                    # 匿名函数 if null 返回 ""
                    ft = lambda x: "" if not x else x
                    # 构建 redis 值
                    data = {}
                    data["id"] = return_list["id"]
                    data["departmentID"] = return_list["DepartmentID"]
                    data["email"] = ft(return_list["Email"])
                    data["flag"] = return_list["flag"]
                    data["mobile"] = ft(return_list["Mobile"])
                    data["password"] = return_list["Password"]
                    data["realName"] = return_list["RealName"]
                    data["roleID"] = roleid
                    data["status"] = return_list["status"]
                    data["userName"] = return_list["UserName"]
                    data["remark"] = ft(return_list["remark"])
                    data["createDate"] = int(time.mktime(return_list["createDate"].timetuple()))
                    data["editDate"] = int(time.mktime(return_list["editDate"].timetuple()))
                    data["token"] = token

                    # 存储用户具体信息  # 存储登陆用户token值
                    redis_value = "\xAC\x05t\x01D" + str(data).replace("'", "\"")
                    redis.set(redis_key, redis_value)
                    redis.expire(redis_key, 1800)
                    token_value = token
                    redis.set(token_key, token_value)
                    redis.expire(token_key, 1800)

                    return jsonify({
                        "code": 1,
                        "msg": {"roleId": return_list["id"], "token": token, "userId": return_list["id"],
                                "userName": userName}
                    })
                else:
                    return jsonify({
                        "code": -1,
                        "data": "账号或密码错误，请重新输入账号密码"})
            else:
                return jsonify({
                    "code": -1,
                    "data": "操作失败"})

    except Exception as e:
        raise e


@backstage.route("/queryUserByUserName/", methods=["POST"])
def queryUserByUserName():
    """登陆用户信息查询接口"""
    json_data = request.get_json()
    username = json_data["userName"]
    try:
        conn = mysqlpool.get_conn()
        with conn.swich_db(config.WOWRKSHEET01) as cursor:
            # 通过 roles_users表 查询用户关系的角色ID  一个用户可能关系多个角色
            rolesid = conn.query_all(
                "select a.roleid,b.RoleName from {tableA} as a LEFT JOIN {tableB} as b on a.roleid= b.id where a.username=%s".format(
                    tableA=config.TABLENAME19, tableB=config.TABLENAME17), [username])
            rolesid_list = []
            rolesname_list = []
            for i in rolesid:
                rolesid_list.append(i["roleid"])
                rolesname_list.append(i["RoleName"])
            user_msg = conn.query_one(
                "select a.id,a.DepartmentID,a.LastLoginTime,a.RealName,a.Mobile,a.Email,a.status,a.remark,a.loginIp,b.full_name,b.short_name from {tableA} as a LEFT JOIN {tableB} as b on a.DepartmentID = b.number where a.UserName=%s".format(
                    tableA=config.TABLENAME16, tableB=config.TABLENAME21), [username])
        # 匿名函数 if null 返回 ""
        ft = lambda x: "" if not x else x
        return_dic = {}
        return_dic["DepartmentID"] = user_msg["DepartmentID"]
        return_dic["Email"] = ft(user_msg["Email"])
        return_dic["LastLoginTime"] = user_msg["LastLoginTime"].strftime("%Y-%m-%d %H:%M:%S")
        return_dic["Mobile"] = ft(user_msg["Mobile"])
        return_dic["RealName"] = user_msg["RealName"]
        return_dic["RoleID"] = rolesid_list
        return_dic["RoleName"] = rolesname_list
        return_dic["UserName"] = username
        return_dic["full_name"] = user_msg["full_name"]
        return_dic["id"] = user_msg["id"]
        return_dic["loginIp"] = user_msg["loginIp"]
        return_dic["remark"] = ft(user_msg["remark"])
        return_dic["short_name"] = ft(user_msg["short_name"])
        return_dic["status"] = user_msg["status"]

    except Exception as e:
        raise e
    return jsonify({
        "code": 1,
        "data": {
            "page": 1,
            "rows": [return_dic],
            "total": 1
        }
    })


# 退出接口
@backstage.route("/signout/", methods=["POST"])
def signout():
    """用户退出"""
    json_data = request.get_json()
    uid = g.token["id"]
    token_cn = json_data["token"]
    try:
        # conn = mysqlpool.get_conn()
        # with conn.swich_db(config.WOWRKSHEET01) as cursor:
        redis.delete("userID:{}".format(uid))
        redis.delete("userID:{}".format(token_cn))

    except Exception as e:
        raise e
    finally:
        return jsonify({
            "code": 1,
            "data": "退出成功"
        })
