#!/usr/bin/python

__author__ = 'zJx'

import numpy as np
from math import sqrt

"""
后验差比值检验
"""


def evaluate(testtmp, pretmp):
    # 原始序列标准差
    testtmp_mean = sum(testtmp) / len(testtmp)
    test_var = 0.0
    for i in testtmp:
        test_var += (i - testtmp_mean) ** 2
    test_std = sqrt(test_var / len(testtmp))

    testtmp = testtmp.copy()
    for i in range(len(testtmp)):
        testtmp[i] = abs(testtmp[i] - pretmp[i])

    # 残差序列标准差
    pretmp_mean = sum(testtmp) / len(testtmp)
    pre_var = 0.0
    for i in testtmp:
        pre_var += (i - pretmp_mean) ** 2
    pre_std = sqrt(pre_var / len(testtmp))

    # 计算后验差比值
    # 模型精度 c<0.35 优 | c<0.5 合格 | c<0.65 勉强合格 | c>0.65 不合格
    c = (pre_std / test_std)

    if c < 0.35:
        c_indetify = '后验差比值检验属优'
    elif c < 0.5:
        c_indetify = '后验差比值检验属合格'
    elif c < 0.65:
        c_indetify = '后验差比值检验属勉强合格'
    else:
        c_indetify = '后验差比值检验属不合格'
    return c, c_indetify


if __name__ == "__main__":
    test = [511.625534, 523.535416, 535.722543, 548.193369]
    pred = [477.0, 504.0, 534.0, 549.0]
    print(evaluate(test, pred))
