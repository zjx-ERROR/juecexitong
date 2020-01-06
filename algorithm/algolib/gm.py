#!/usr/bin/python
__author__ = 'zJx'

import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import matplotlib
import sys
import pymongo
import json
import pymysql
import importlib
from trace_back import traceback_log
from config import *
from datetime import datetime
# matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
# matplotlib.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题


class GrayForecast:
    """
    初始化
    """

    def __init__(self, data, atime=5):
        self.TIME = atime
        self.data = data
        self.forecast_list = self.data.copy()

    def level_check(self, cons=None):
        # 数据级比校验
        n = len(self.data)

        lambda_k = np.zeros(n - 1)
        dete = 2
        while dete:
            for i in range(n - 1):
                lambda_k[i] = self.data.iloc[i, -1] / self.data.iloc[i + 1, -1]
                if lambda_k[i] < np.exp(-2 / (n + 1)) or lambda_k[i] > np.exp(2 / (n + 2)):
                    if cons:
                        self.data.iloc[:, -1] += cons
                        # cons = None
                    dete -= 1
                    flag = False
                    break
            else:
                flag = True
                break

        self.lambda_k = lambda_k

        if not flag:
            print("级比校验失败，请对X(0)做平移变换")
            return False
        else:
            print("级比校验成功，请继续")
            return True

    def f(self, k):
        return (self.X_0[0] - self.u / self.a) * (1 - np.exp(self.a)) * np.exp(-self.a * (k))

    def GM_11_build_model(self, forecast=3):
        """
        GM(1,1)建模
        :param forecast:
        :return:
        """
        if forecast > len(self.data):
            raise Exception('您的数据行不够')
        # 原始时间序列
        self.X_0 = np.array(self.data.iloc[:, -1])

        # 一次累加数据序列
        X_1 = np.zeros(self.X_0.shape)
        for i in range(self.X_0.shape[0]):
            X_1[i] = np.sum(self.X_0[0:i + 1])

        Z_1 = np.zeros(X_1.shape[0] - 1)
        for i in range(1, X_1.shape[0]):
            Z_1[i - 1] = -0.5 * (X_1[i] + X_1[i - 1])

        B = np.append(np.array(np.mat(Z_1).T), np.ones(Z_1.shape).reshape((Z_1.shape[0], 1)), axis=1)

        Ym = self.X_0[1:].reshape((self.X_0[1:].shape[0], 1))

        B = np.mat(B)
        Ym = np.mat(Ym)
        a_ = (B.T * B) ** -1 * B.T * Ym

        self.a, self.u = np.array(a_.T)[0]
        # 原数据预测值
        for i in range(self.forecast_list.shape[0]):
            self.forecast_list.iloc[i:i + 1, -1] = self.f(i)

    # 预测
    def forecast(self):
        for i in range(self.TIME):
            newdf = pd.DataFrame([[self.forecast_list.iloc[-1, 0] + (self.forecast_list.iloc[-1, 0] - self.forecast_list.iloc[-2, 0]), self.f(self.forecast_list.shape[0])]],
                                 columns=self.forecast_list.columns)
            self.forecast_list = self.forecast_list.append(newdf, ignore_index=True)

    def log(self):
        """
        打印日志
        :return:
        """
        res = self.forecast_list.iloc[-self.TIME:]
        self.res = pd.concat([self.data.copy(), res])

    # def plot(self):
    #     """
    #     作图
    #     :return:
    #     """
    #     plt.figure(figsize=(14, 7))
    #     x = [i for i in self.res.index.tolist()]
    #     y = [i[0] for i in self.res.values.tolist()]
    #     plt.plot(x, y, marker='.')
    #     plt.ylabel(self.res.columns.values.tolist()[0])
    #     plt.xlabel(self.res.index.name)
    #
    #     plt.xticks([i for i in self.res.index.tolist()], rotation=60)
    #     plt.grid(linestyle='--', color='#DCDCDC')
    #     for a, b in zip([i[0] for i in self.res.values.tolist()], self.res.index.tolist()):
    #         plt.text(b, a, "%.1f" % a, ha='center', va='bottom', fontsize=10)
    #     plt.legend(self.res.columns.values.tolist(), loc='upper left', frameon=False, fontsize='large')
    #     plt.title('%s预测图表' % self.res.columns.values.tolist()[0])
    #
    #     # the_table = plt.table(cellText=self.table_vals, rowLabels=self.row_labels, colLabels=self.col_labels,
    #     #                       loc='center'
    #     #                       , colWidths=[0.4, 0.1, 0.2], cellLoc='center', bbox=[0.25, -0.45, 0.6, 0.28])
    #
    #     plt.subplots_adjust(bottom=0.3)
    #     plt.savefig('../%s预测图表.png' % self.res.columns.values.tolist()[0])
    #     # plt.show()
def str_to_datetime(t):
    if isinstance(t,str):
        d = ['%Y', '%m', '%d']
        line_count = t.count('-')
        dt = datetime.strptime(t, '-'.join(d[:line_count+1]) if line_count > 0 else d[0])
        return dt
    else:
        return None

def check_type(dict_like):
    for k, v in dict_like.items():
        for i in v:
            if not isinstance(i, str):
                continue
            else:
                #v[v.index(i)] = str_to_datetime(i)
                v[v.index(i)] = int(i)

    return dict_like

@traceback_log('/usr/local/algorithm/log/trace_back.log')
def main(jsonid):
    cli = pymongo.MongoClient(host=ghost, port=gport, username=gusername, password=gpassword)
    coll = cli['userconfig']['user_algorithmic_data']
    data = coll.find_one({'id': jsonid})['data']

    pre_data = check_type(data['data'])
    train_data = pd.DataFrame(pre_data)
    gf = GrayForecast(train_data)
    check = gf.level_check()

    if check:
        gf.GM_11_build_model()
        gf.forecast()
        gf.log()
        a = gf.res.to_dict(orient='split')
        a.pop('index')

        evalist = []
        elist = train_data.iloc[:, -1].to_list()
        forecastlist = gf.forecast_list.iloc[:, -1].to_list()

        conn = pymysql.connect(host=mhost, port=mport, user=muser, passwd=mpasswd,
                               db=mdb)
        cursor = conn.cursor()

        for de in data['evaluate']:
            cursor.execute('select name,definition,func_name from algorithmic_assessment where id = "%d"' % de)
            cf = cursor.fetchone()
            result = importlib.import_module(cf[2]).evaluate(elist, forecastlist)
            evalist.append({'name': cf[0], 'value': result[0], 'ins': result[1], 'conclusion': cf[1]})
        cursor.close()
        conn.close()

        c = {'data': a, 'evaluate': evalist, 'mark': data['mark']}

        client = pymongo.MongoClient(host=ghost, port=gport, username=gusername, password=gpassword)
        collection = client['userconfig']['algorithm_output']
        collection.update_one({'mark': data['mark']}, {"$set": c}, upsert=True)

        coll.delete_one({'id': jsonid})
        cli.close()


if __name__ == "__main__":
    sys.path.append('/usr/local/algorithm/evaluate')
    main(sys.argv[1])
    # main("c3a400b3-87f3-4e35-95ee-693a4b903e73")
