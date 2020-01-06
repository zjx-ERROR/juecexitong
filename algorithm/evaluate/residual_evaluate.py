#!/usr/bin/python

__author__ = 'zJx'

"""
残差相对值分析
"""


def evaluate(testtmp, pretmp):
    # 残差序列
    testtmp = testtmp.copy()
    evt = []
    # 残差相对值检验小于10%则符合要求
    for i in range(len(testtmp)):
        testtmp[i] = abs(testtmp[i] - pretmp[i])
        evt_identify = testtmp[i] / pretmp[i]
        if evt_identify > 0.1:
            ins = "残差相对值不符合要求"
            break
        evt.append(evt_identify)
    else:
        ins = '残差相对值检验符合要求'

    return 0 if len(evt) == 0 else sum(evt) / len(evt),ins



if __name__ == "__main__":
    test = [511.625534, 523.535416, 535.722543, 548.193369]
    pred = [477.0, 504.0, 534.0, 549.0]
    print(evaluate(test, pred))
