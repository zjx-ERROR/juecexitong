from utils.dbutils import db


class User(db.Model):
    __tablename__ = 'userinfo'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    UserName = db.Column(db.String(30), nullable=False)
    Password = db.Column(db.String(200), nullable=False)
    LastLoginTime = db.Column(db.DateTime)
    Mobile = db.Column(db.String(20))
    Email = db.Column(db.String(50))
    RoleID = db.Column(db.String(255))
    DepartmentID = db.Column(db.String(100))
    RealName = db.Column(db.String(100))
    flag = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False)
    remark = db.Column(db.String(200))
    loginIp = db.Column(db.String(45))
    createDate = db.Column(db.DateTime, nullable=False)
    editDate = db.Column(db.DateTime, nullable=False)


