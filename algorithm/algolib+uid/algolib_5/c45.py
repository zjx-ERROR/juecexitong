__author__ = 'zJx'

from math import log
import operator
import sys
import pandas as pd
# import treeplotter
import pymongo
import json
import pymysql
import importlib
import sys
from trace_back import traceback_log


class C45Tree:
    """
    C4.5决策树
    """

    def calcShannonEnt(self, dataSet):

        """
        输入：数据集
        输出：数据集的信息熵
        描述：计算给定数据集的信息熵；熵越大，数据集的混乱程度越大
        """

        numEntries = len(dataSet)
        labelCounts = {}
        for featVec in dataSet:
            currentLabel = featVec[-1]
            if currentLabel not in labelCounts.keys():
                labelCounts[currentLabel] = 0
            labelCounts[currentLabel] += 1
        shannonEnt = 0.0
        for key in labelCounts:
            prob = float(labelCounts[key]) / numEntries
            shannonEnt -= prob * log(prob, 2)
        return shannonEnt

    def splitDataSet(self, dataSet, axis, value):
        """
        输入：数据集，选择维度，选择值
        输出：划分数据集
        描述：按照给定特征划分数据集；去除选择维度中等于选择值的项
        """
        retDataSet = []
        for featVec in dataSet:
            if featVec[axis] == value:
                reduceFeatVec = featVec[:axis]
                reduceFeatVec.extend(featVec[axis + 1:])
                retDataSet.append(reduceFeatVec)
        return retDataSet

    def chooseBestFeatureToSplit(self, dataSet):
        """
        输入：数据集
        输出：最好的划分维度
        描述：选择最好的数据集划分维度
        """
        numFeatures = len(dataSet[0]) - 1
        baseEntropy = self.calcShannonEnt(dataSet)
        bestInfoGainRatio = 0.0
        bestFeature = -1
        for i in range(numFeatures):
            featList = [example[i] for example in dataSet]
            uniqueVals = set(featList)
            newEntropy = 0.0
            splitInfo = 0.0
            for value in uniqueVals:
                subDataSet = self.splitDataSet(dataSet, i, value)
                prob = len(subDataSet) / float(len(dataSet))
                newEntropy += prob * self.calcShannonEnt(subDataSet)
                splitInfo += -prob * log(prob, 2)
            infoGain = baseEntropy - newEntropy
            if (splitInfo == 0):  # fix the overflow bug
                continue
            infoGainRatio = infoGain / splitInfo
            if (infoGainRatio > bestInfoGainRatio):
                bestInfoGainRatio = infoGainRatio
                bestFeature = i
        return bestFeature

    def majorityCnt(self, classList):
        """
        输入：分类类别列表
        输出：子节点的分类
        描述：数据集已经处理了所有属性，但是类标签依然不是唯一的，
              采用多数判决的方法决定该子节点的分类
        """
        classCount = {}
        for vote in classList:
            if vote not in classCount.keys():
                classCount[vote] = 0
            classCount[vote] += 1
        sortedClassCount = sorted(classCount.items(), key=operator.itemgetter(1), reverse=True)
        return sortedClassCount[0][0]

    def createTree(self, dataSet, labels):

        """
        输入：数据集，特征标签
        输出：决策树
        描述：递归构建决策树，利用上述的函数
        """

        classList = [example[-1] for example in dataSet]
        if classList.count(classList[0]) == len(classList):
            # 类别完全相同，停止划分
            return classList[0]
        if len(dataSet[0]) == 1:
            # 遍历完所有特征时返回出现次数最多的
            return self.majorityCnt(classList)
        bestFeat = self.chooseBestFeatureToSplit(dataSet)
        bestFeatLabel = labels[bestFeat]
        myTree = {bestFeatLabel: {}}
        del (labels[bestFeat])
        # 得到列表包括节点所有的属性值
        featValues = [example[bestFeat] for example in dataSet]
        uniqueVals = set(featValues)

        for value in uniqueVals:
            subLabels = labels[:]
            myTree[bestFeatLabel][value] = self.createTree(self.splitDataSet(dataSet, bestFeat, value), subLabels)
        return myTree

    def classify(self, inputTree, featLabels, testVec):

        """
        输入：决策树，分类标签，测试数据
        输出：决策结果
        描述：跑决策树
        """

        firstStr = list(inputTree.keys())[0]
        secondDict = inputTree[firstStr]
        featIndex = featLabels.index(firstStr)

        for key in secondDict.keys():
            if testVec[featIndex] == key:
                if type(secondDict[key]).__name__ == 'dict':
                    return self.classify(secondDict[key], featLabels, testVec)
                else:
                    classLabel = secondDict[key]
                    return classLabel

    def classifyAll(self, inputTree, featLabels, testDataSet, a=1):

        """
        输入：决策树，分类标签，测试数据集
        输出：决策结果
        描述：跑决策树
        """

        classLabelAll = []
        for testVec in testDataSet:
            classLabelAll.append(self.classify(inputTree, featLabels, testVec[:-1]))

        return classLabelAll

    def check(self, testDataSet, classLabelAll, a=1):
        print(classLabelAll)
        testset_tmp = [ts[-1] for ts in testDataSet]
        new_classLabel = list(zip(classLabelAll, testset_tmp))
        new_classLabel = list(filter(lambda x: x[0] != None, new_classLabel))
        # 召回率recall
        recall = len(new_classLabel) / len(classLabelAll)

        right_classLabel = list(filter(lambda x: x[0] == x[1], new_classLabel))
        # 正确率precision
        precision = len(right_classLabel) / len(new_classLabel)

        # F-Measure
        fmeasure = (precision * recall * (a * a + 1)) / (a * a * (precision + recall))
        return recall, precision, fmeasure

    def storeTree(self, inputTree, filename):
        """
        输入：决策树，保存文件路径
        输出：
        描述：保存决策树到文件
        """
        import pickle
        fw = open(filename, 'wb')
        pickle.dump(inputTree, fw)
        fw.close()

    def grabTree(self, filename):
        """
        输入：文件路径名
        输出：决策树
        描述：从文件读取决策树
        """
        import pickle
        fr = open(filename, 'rb')
        return pickle.load(fr)


class GetData:
    """
    获取数据
    """

    def __init__(self, filedir, sheet_name):
        self.filedir = filedir
        self.sheet_name = sheet_name

    def from_excel(self):
        try:
            data = pd.read_excel(self.filedir, sheet_name=self.sheet_name)
        except Exception as e:
            raise e
        else:
            self.labels = data.columns.tolist()
            dataset = data.values.tolist()[:int(data.__len__() * 0.7)]
            testset = data.values.tolist()[int(data.__len__() * 0.7):]
        return dataset, testset, self.labels

    def fit_from_excel(self, fit_filedir, fit_sheet_name):
        try:
            data = pd.read_excel(fit_filedir, sheet_name=fit_sheet_name)
        except Exception as e:
            raise e
        else:
            labels = data.columns.tolist()
            dataset = data.values.tolist()
            if labels != self.labels:
                return None
            else:
                return dataset


class Persist:

    def __init__(self, document):
        self.document = document

    def to_mongo(self):
        client = pymongo.MongoClient(host='127.0.0.1', port=27017, username='master', password='master')
        collection = client['userconfig']['algorithm_output']
        collection.update_one({'mark': self.document['mark']}, {"$set": self.document}, upsert=True)


def k_to_en(dictlike):
    n_list = []
    if isinstance(dictlike, dict):
        for i in dictlike:
            dictlike[i] = k_to_en(dictlike[i])
            n_list.append({'name': i, 'children': dictlike[i]})
    else:
        n_list.append({'name': dictlike, 'children': []})
    return n_list


def train(data):
    document = {}
    c45 = C45Tree()

    train_data = pd.DataFrame(data['data'])
    labels = train_data.columns.tolist()
    dataset = train_data.values.tolist()[:int(train_data.__len__() * 0.7)]
    testset = train_data.values.tolist()[int(train_data.__len__() * 0.7):]
    labels_tmp = labels[:-1]
    testset_tmp = [ts[-1] for ts in testset]

    # 决策树desicionTree
    desicionTree = c45.createTree(dataset, labels_tmp)
    test_reslult = c45.classifyAll(desicionTree, labels[:-1], testset)
    evalist = []

    conn = pymysql.connect(host="192.168.5.128", port=3306, user='gykj', passwd='123456', db='component_management')
    cursor = conn.cursor()
    for de in data['evaluate']:
        cursor.execute('select name,func_name,definition from algorithmic_assessment where id = "%d"' % de)
        cf = cursor.fetchone()
        evalist.append(
            {'name': cf[0], 'value': importlib.import_module(cf[1]).evaluate(testset_tmp, test_reslult), 'ins': '',
             'conclusion': cf[2]})

    cursor.close()
    conn.close()

    document['data'] = json.loads(json.dumps(desicionTree))

    document['mark'] = data['mark']
    document['evaluate'] = evalist

    document['data'] = k_to_en(document['data'])

    # treeplotter.createPlot(desicionTree, figsize=[44, 16], fname=document['data'])
    p = Persist(document)
    p.to_mongo()


def forcast(data):
    c45 = C45Tree()
    forcast_data = pd.DataFrame(data['data'])
    labels = forcast_data.columns.tolist()
    dataset = forcast_data.values.tolist()

    from_mark = data['mark'].replace('forcast', 'train')
    client = pymongo.MongoClient(host='127.0.0.1', port=27017, username='master', password='master')
    collection = client['userconfig']['algorithm_output']
    desicionTree = collection.find_one({'mark': from_mark})['desicionTree']
    result = c45.classifyAll(desicionTree, labels, dataset)
    collection.insert_one({'mark': data['mark'], 'forcast_data': result})
    client.close()


@traceback_log('trace_back.log')
def main(jsonid):
    cli = pymongo.MongoClient(host='127.0.0.1', port=27017, username='master', password='master')
    coll = cli['userconfig']['user_algorithmic_data']
    data = coll.find_one({'id': jsonid})['data']

    # data = json.loads(jsondata)
    if data['mark'].endswith('train'):
        train(data)
    elif data['mark'].endswith('forcast'):
        forcast(data)
    else:
        print('Error')
    coll.delete_one({'id': jsonid})
    cli.close()


if __name__ == "__main__":
    sys.path.append('../evaluate')
    main('a4a9477b-7a42-491d-ba49-f4207ad40558')
    # main(sys.argv[1])
