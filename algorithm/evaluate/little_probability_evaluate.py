#!/usr/bin/python

__author__ = 'zJx'

from math import sqrt
"""
小误差概率检验
"""


def evaluate(testtmp, pretmp):
    # 计算小误差频率 P>0.95 优 | P>0.80 合格 | P>0.70 勉强合格 | P<0.70 不合格

    # 原始序列标准差
    testtmp_mean = sum(testtmp) / len(testtmp)
    test_var = 0.0
    for i in testtmp:
        test_var += (i - testtmp_mean) ** 2
    test_std = sqrt(test_var / len(testtmp))*0.675

    # 残差序列
    testtmp = testtmp.copy()
    # 残差相对值检验小于10%则符合要求
    for i in range(len(testtmp)):
        testtmp[i] = abs(testtmp[i] - pretmp[i])
    tmp_mean = sum(testtmp)/len(testtmp)

    count = 0

    for i in testtmp:
        if abs(i-tmp_mean) < test_std:
            count += 1

    p = count / len(testtmp)

    if p > 0.95:
        p_indetify = '小误差频率检验属优'
    elif p > 0.8:
        p_indetify = '小误差频率检验属合格'
    elif p > 0.7:
        p_indetify = '小误差频率检验属勉强合格'
    else:
        p_indetify = '小误差频率检验属不合格'

    return p,p_indetify
if __name__ == "__main__":
    test = [511.625534, 523.535416, 535.722543, 548.193369]
    pred = [477.0, 504.0, 534.0, 549.0]
    print(evaluate(test, pred))
