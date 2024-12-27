import pandas as pd
import numpy as np
import transbigdata as tbd
import os
import math
import multiprocessing
import json
import datetime

import CommonCode as cc

# 通过经纬度获取地址。
from geopy.geocoders import Nominatim
# 将地址向量化。
from sentence_transformers import SentenceTransformer, util


## 加载超参数

def GetParameters(parametersPath='./Parameters.json'):
    """_summary_
    读取并设置程序所需的超参数。
    Args:
        parametersPath (str, optional): 保存超参数的JSON文档. Defaults to './Parameters.json'.
    """
    with open(parametersPath, 'r', encoding='utf-8') as f:
        Parameters = json.load(f)

    # 全局变量声明
    global gBounds
    global gGeoParameters
    global gPoIFolderPath
    global gPoIFeatureSavePath
    global gAreaGriddingFeatureSavePath
    global gPoISocialFeatureSavePath
    global gPoIDropInforNegativelFeatureSavePath
    global gPoINegativelFeatureSavePath
    
    global gRenameColumns
    global gFileterColumne
    global gSelectedColumne
    global gCategoryMapNumber
    global gTrajectoryFolderPath
    global gUserList
    global gOutputProecessedTrajectory
    global gInputTrajectoryCsvSavePath
    global gOutpuyPath
    global gSamplingIntervalRow
    global gSaveUserTrajectoryFlag
    global gDeleteOutofBoundTrajectoryFlag
    global gSingleUserTrajectoryFeaturePath
    global gAllUsersTrajectoryFeaturePath
    # global gFeaturePath
    global gInteractionMatrixSavePath
    global gStaySavePath
    global gMoveSavePath
    global gSingleUserStaySavePath
    global gSingleUserMoveSavePath
    global gMaxRow
    global gActivityTime
    global gSingleUserStayMatrixSavePath
    global gAllUsersTrajectoriesFeatureMatrixSavePath
    global gOutputDataFormat

    # set 3D data dimension number.
    global gFeatureThirdDimension

    global gI
    gI = 0
    
    # print(Parameters)
    # 研究地域范围。通过经纬度表示。
    gBounds = list(Parameters['gBounds'])
    # print(gBounds)

    # 地域网格的大小。单位为米。
    accuracy = int(Parameters['accuracy'])
    # 网格的形状，默认是正方形。
    method = Parameters['method']

    # 设置全局地理信息。
    gGeoParameters = tbd.area_to_params(gBounds, accuracy = accuracy, method=method)
    # 停留点矩阵，每行最多的停留点数量。也就是意味着矩阵第二维的长度。
    gMaxRow = int(Parameters['gMaxRow'])
    # 用于生成停留点的时间判断阈值。
    gActivityTime = int(Parameters['gActivityTime'])
    # 单个用户停留矩阵保存路径。
    gSingleUserStayMatrixSavePath = Parameters['gSingleUserStayMatrixSavePath']

    # 轨迹原始数据采样间隔。
    gSamplingIntervalRow = float(Parameters['gSamplingIntervalRow'])

    # PoI特征输入目录。PoI文件夹的路径.
    gPoIFolderPath = Parameters['gPoIFolderPath']
    # 保存PoI特征的路径及文件名. Defaults to './Data/Output/PoIFeature.csv'.
    # 这个是保存所有PoI特征合并之后的特征。
    gPoIFeatureSavePath = Parameters['gPoIFeatureSavePath']
    
    # 将地图栅格化之后，需要按照行和列作为编号来存储每个栅格的特征。
    # 也就是以3维的形式来存储PoI特征。
    # 现有的是使用grid来作为index存储的。但是transbigdata生成的grid无法确保唯一性，先用cantor函数来生成具有唯一性的grid。
    # 并且可以使用cantor反函数来恢复行号和列号。
    gAreaGriddingFeatureSavePath = Parameters['gAreaGriddingFeatureSavePath']
    

    # 保存社会信息的PoI特征。也就是北大开源的PoI特征。
    gPoISocialFeatureSavePath = Parameters['gPoISocialFeatureSavePath']
    # 去信息化的非社会信息的PoI特征保存路径。中间零时保存的信息。
    gPoIDropInforNegativelFeatureSavePath = Parameters['gPoIDropInforNegativelFeatureSavePath']
    # 非社会信息的PoI特征保存路径。需要去信息化的特征。
    gPoINegativelFeatureSavePath = Parameters['gPoINegativelFeatureSavePath']

    gRenameColumns = dict(Parameters['gRenameColumns'])
    # print(gRenameColumns)
    gFileterColumne = list(Parameters['gFileterColumne'])
    # print(gFileterColumne)
    gSelectedColumne = list(Parameters['gSelectedColumne'])
    # print(gSelectedColumne)
    gCategoryMapNumber = dict(Parameters['gCategoryMapNumber'])
    # print(gCategoryMapNumber)
    
    
    # 轨迹数据的存储目录。
    gTrajectoryFolderPath = Parameters['gTrajectoryFolderPath']
    # 获取所有用户的名称。
    gUserList = next(os.walk(gTrajectoryFolderPath))[1]
    # 单个用户的保存目录。
    gOutputProecessedTrajectory = Parameters['gOutputProecessedTrajectory']
    # 所有用户的保存目录。
    gInputTrajectoryCsvSavePath = Parameters['gInputTrajectoryCsvSavePath']
    # 保存的输出的根目录。
    gOutpuyPath = Parameters['gOutpuyPath']
    # TrajectoriesBasePath = './Data/Geolife Trajectories 1.3/Data/'
    
    
    # 是否独立保存每个用户的轨迹。
    gSaveUserTrajectoryFlag = bool(Parameters['gSaveUserTrajectoryFlag'])
    # print(gSaveUserTrajectoryFlag, type(gSaveUserTrajectoryFlag))
    # 在处理轨迹数据时，是否将所有范围之外的经纬度都删除。
    # 1. 按照推荐系统的一般做法，会将没有出现在物品列表中的物品删除。
    # 2. 而且在没有剔除范围外的地点时会产生大量编号为负数的grid。所以最后
    # 考虑上述两个原因，先把范围之外的地点在最后生成轨迹特征时 GenerateInteractionMatrix() 删除。
    gDeleteOutofBoundTrajectoryFlag = bool(Parameters['gDeleteOutofBoundTrajectoryFlag'])

    # 单个用户轨迹附着了特征之后的保存路径。
    gSingleUserTrajectoryFeaturePath = Parameters['gSingleUserTrajectoryFeaturePath']
    # 所有用户的轨迹附着了特征之后的保存路径。
    gAllUsersTrajectoryFeaturePath = Parameters['gAllUsersTrajectoryFeaturePath']
    # 所有合并之后的特征。
    # gFeaturePath = './Data/Output/Feature.csv'
    # 暂时只有PoI特征。所以直接指向PoI特征。
    # gFeaturePath = Parameters['gFeaturePath']
    # 交互矩阵保存的路径。
    gInteractionMatrixSavePath = Parameters['gInteractionMatrixSavePath']
    
    # 所有停留点数据缓存路径。
    gStaySavePath = Parameters['gStaySavePath']
    # 所有一动点数据缓存路径。
    gMoveSavePath = Parameters['gMoveSavePath']
    
    # 单个用户停留点保存路径。
    gSingleUserStaySavePath = Parameters['gSingleUserStaySavePath']
    # 单个用户移动点保存路径。
    gSingleUserMoveSavePath = Parameters['gSingleUserMoveSavePath']
    # 设置所有用户特征矩阵的保存路径。
    gAllUsersTrajectoriesFeatureMatrixSavePath = Parameters['gAllUsersTrajectoriesFeatureMatrixSavePath']

    # select output data format.
    gOutputDataFormat = list(Parameters['gOutputDataFormat'])

    gFeatureThirdDimension = 0
    