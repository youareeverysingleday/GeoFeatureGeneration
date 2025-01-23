import pandas as pd
import polars as pl
import numpy as np
import transbigdata as tbd
import os
# display polars' progress bar.
# os.environ['POLARS_VERBOSE'] = '1'
import math
import multiprocessing
import json
import datetime

import csv

import CommonCode as cc

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
    global gOutputPath
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
    global gRefreshDataFlag

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
    gOutputPath = Parameters['gOutputPath']
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
    # 将所有的数据刷新。
    gRefreshDataFlag = bool(Parameters['gRefreshDataFlag'])


## --- 读取轨迹数据 ---
def GetEntireTime(df):
    # 先拼成完整的时间。
    df['entireTime'] = \
        pd.Timestamp(datetime.datetime.strptime((df['date'] + ' ' + df['time']),'%Y-%m-%d %H:%M:%S'))
    return df

# entireTime
def GenerateTimeFeature(df, col='stime'):
    """_summary_
    生成时间特征。。提供给pandas apply使用的。
    Args:
        df (_type_): _description_

    Returns:
        _type_: _description_
    """

    # 生成时间特征。
    df['weekofyear'] = df[col].weekofyear
    # 一周中的星期几。
    df['dayofweek'] = df[col].dayofweek
    # 一年中的第几天。
    df['dayofyear'] = df[col].dayofyear
    # 一年中的第几个季度。
    df['quarter'] = df[col].quarter
    # SingleUserTrajectory_pd['weekday_name'] = SingleUserTrajectory_pd['entireTime'].dt.weekday_name
    # 一年中的第几个月。
    df['month'] = df[col].month
    # 第几年。这个没有必要。
    # SingleUserTrajectory_pd['year'] = SingleUserTrajectory_pd['entireTime'].dt.year
    # 一天中的第几个小时。
    df['hour'] = df[col].hour
    # df['halfhour'] = df['entireTime'].floor(freq='30Min')
    return df

# --- 轨迹预处理 ---

def PreprocessSingleTrajectoryIndependent(user):
    """_summary_
    对单个用户的轨迹进行处理。主要这里是输出时保存为每个用户的轨迹文件。
    原因是，单个大的csv文件在读入pandas时对计算的性能要求比较高；所以分为每个文件可以加快处理速度。
    Args:
        user (_type_): _description_
    """
    userdata = gTrajectoryFolderPath + '/{}/Trajectory/'.format(user)

    # 返回指定路径下所有文件和文件夹的名字，并存放于一个列表中
    filelist = os.listdir(userdata)  
    names = ['lat','lng','zero','alt','days','date','time']
    # f为文件索引号，header为头部需要跳过的行数，names为列表列名，index_col为行索引的列编号或列名。
    df_list = [pd.read_csv(userdata + f, header=6, names=names, index_col=False) for f in filelist]
    
    # 表格列字段不同的表合并
    df = pd.concat(df_list, ignore_index=True)

    # 删除未使用的列
    df.drop(['zero', 'days'], axis=1, inplace=True) #drop函数默认删除行，列需要加axis = 1
    
    # 准备对数据进行抽样，降低数据密度。
    df_sampling = pd.DataFrame()
    
    if gSamplingIntervalRow != 0:
        # 每隔1~5秒记录一次数据，这种情况太频繁了。将它减少到每分钟
        df_sampling = df.iloc[::gSamplingIntervalRow, :] #每隔12行取一次
        df_sampling.head(5)  #查看前5行
    else:
        # 如果不进行抽样的动作，那么直接复制。
        df_sampling = df.copy()
    
    # df.shape()：
    # print ('Total GPS points: ' + str(df_sampling.shape[0]))

    # 生成完整的时间列。
    # df_sampling = df_sampling.apply(GetEntireTime, axis=1)
    df_sampling['entireTime'] = pd.to_datetime((df_sampling['date'] + ' ' + df_sampling['time']), format='%Y-%m-%d %H:%M:%S')
    df_sampling.drop(['date', 'time'], axis=1, inplace=True) 

    # 生成时间特征。
    # SingleUserTrajectory['weekofyear'] = SingleUserTrajectory['entireTime'].dt.weekofyear
    # # 一周中的星期几。
    # SingleUserTrajectory['dayofweek'] = SingleUserTrajectory['entireTime'].dt.dayofweek
    # # 一年中的第几天。
    # SingleUserTrajectory['dayofyear'] = SingleUserTrajectory['entireTime'].dt.dayofyear
    # # 一年中的第几个季度。
    # SingleUserTrajectory['quarter'] = SingleUserTrajectory['entireTime'].dt.quarter
    # # SingleUserTrajectory_pd['weekday_name'] = SingleUserTrajectory_pd['entireTime'].dt.weekday_name
    # # 一年中的第几个月。
    # SingleUserTrajectory['month'] = SingleUserTrajectory['entireTime'].dt.month
    # # 第几年。这个没有必要。
    # # SingleUserTrajectory_pd['year'] = SingleUserTrajectory_pd['entireTime'].dt.year
    # # 一天中的第几个小时。
    # SingleUserTrajectory['hour'] = SingleUserTrajectory['entireTime'].dt.hour
    # SingleUserTrajectory['halfhour'] = SingleUserTrajectory['entireTime'].dt.floor(freq='30Min')

    # 修改列名。
    df_sampling.rename(columns={'lat': 'latitude', 'lng': 'longitude'}, inplace=True)

    # 生成区域ID。
    df_sampling['loncol'], df_sampling['latcol'] = tbd.GPS_to_grid(df_sampling['longitude'], df_sampling['latitude'], gGeoParameters)
    df_sampling = df_sampling.apply(cc.GenerateGrid, axis=1)
    
    # 这段代码必须放在 df_sampling = df_sampling.apply(GenerateGrid, axis=1) 之后来执行。
    # 因为当删除超出范围的用户轨迹数据时，有118、132、160三个用户的轨迹完全不在指定的范围内，虽有这三个用户的轨迹数据为空。
    # 而对于空的dataframe，df_sampling = df_sampling.apply(GenerateGrid, axis=1) 不会新生成'grid'列。
    # 从而直接导致在将PoIFeature和轨迹数据合并时报KeyError的错误。
    if gDeleteOutofBoundTrajectoryFlag == True:
        # Delete out of bounds .
        df_sampling = tbd.clean_outofbounds(df_sampling, bounds = gBounds, col = ['longitude', 'latitude'])
    
    df_sampling['userID'] = user

    if user == 118 or user == 132 or user == 160:
        print('\n s Null Trajectory columns {}'.format(df_sampling.columns))

    if gSaveUserTrajectoryFlag == True:
        df_sampling.to_csv(gOutputProecessedTrajectory.format(user))

def PreprocessSingleTrajectoryMerged(user, sharedData, lock):
    """_summary_
    对单个用户的轨迹进行处理。主要这里是输出时保存为所有用户的轨迹文件。也就是所有用户的轨迹保存为了一个文件。
    保存为一个文件的优点在于，当计算机性能允许的情况下可以比较直接的做整表的逻辑运算。
    比如在生成交互矩阵时就必须需要对所有用户同时进行计算。
    Args:
        user (_type_): _description_
        sharedData (_type_): _description_
        lock (_type_): _description_
    """
    userdata = gTrajectoryFolderPath + '/{}/Trajectory/'.format(user)

    # 返回指定路径下所有文件和文件夹的名字，并存放于一个列表中
    filelist = os.listdir(userdata)  
    names = ['lat','lng','zero','alt','days','date','time']
    # f为文件索引号，header为头部需要跳过的行数，names为列表列名，index_col为行索引的列编号或列名。
    df_list = [pd.read_csv(userdata + f, header=6, names=names, index_col=False) for f in filelist]
    
    # 表格列字段不同的表合并
    df = pd.concat(df_list, ignore_index=True)

    # 删除未使用的列
    df.drop(['zero', 'days'], axis=1, inplace=True) #drop函数默认删除行，列需要加axis = 1
    
    # 准备对数据进行抽样，降低数据密度。
    df_sampling = pd.DataFrame()
    
    if gSamplingIntervalRow != 0:
        # 每隔1~5秒记录一次数据，这种情况太频繁了。将它减少到每分钟
        df_sampling = df.iloc[::gSamplingIntervalRow, :] #每隔12行取一次
        df_sampling.head(5)  #查看前5行
    else:
        # 如果不进行抽样的动作，那么直接复制。
        df_sampling = df.copy()
    
    # df.shape()：
    # print ('Total GPS points: ' + str(df_sampling.shape[0]))

    # 生成完整的时间列。
    # df_sampling = df_sampling.apply(GetEntireTime, axis=1)
    df_sampling['entireTime'] = pd.to_datetime((df_sampling['date'] + ' ' + df_sampling['time']), format='%Y-%m-%d %H:%M:%S')
    df_sampling.drop(['date', 'time'], axis=1, inplace=True) 

    # 生成时间特征。
    # SingleUserTrajectory['weekofyear'] = SingleUserTrajectory['entireTime'].dt.weekofyear
    # # 一周中的星期几。
    # SingleUserTrajectory['dayofweek'] = SingleUserTrajectory['entireTime'].dt.dayofweek
    # # 一年中的第几天。
    # SingleUserTrajectory['dayofyear'] = SingleUserTrajectory['entireTime'].dt.dayofyear
    # # 一年中的第几个季度。
    # SingleUserTrajectory['quarter'] = SingleUserTrajectory['entireTime'].dt.quarter
    # # SingleUserTrajectory_pd['weekday_name'] = SingleUserTrajectory_pd['entireTime'].dt.weekday_name
    # # 一年中的第几个月。
    # SingleUserTrajectory['month'] = SingleUserTrajectory['entireTime'].dt.month
    # # 第几年。这个没有必要。
    # # SingleUserTrajectory_pd['year'] = SingleUserTrajectory_pd['entireTime'].dt.year
    # # 一天中的第几个小时。
    # SingleUserTrajectory['hour'] = SingleUserTrajectory['entireTime'].dt.hour
    # SingleUserTrajectory['halfhour'] = SingleUserTrajectory['entireTime'].dt.floor(freq='30Min')

    # 修改列名。
    df_sampling.rename(columns={'lat': 'latitude', 'lng': 'longitude'}, inplace=True)

    # 生成区域ID。
    df_sampling['loncol'], df_sampling['latcol'] = tbd.GPS_to_grid(df_sampling['longitude'], df_sampling['latitude'], gGeoParameters)
    df_sampling = df_sampling.apply(cc.GenerateGrid, axis=1)
    
    # 这段代码必须放在 df_sampling = df_sampling.apply(GenerateGrid, axis=1) 之后来执行。
    # 因为当删除超出范围的用户轨迹数据时，有118、132、160三个用户的轨迹完全不在指定的范围内，虽有这三个用户的轨迹数据为空。
    # 而对于空的dataframe，df_sampling = df_sampling.apply(GenerateGrid, axis=1) 不会新生成'grid'列。
    # 从而直接导致在将PoIFeature和轨迹数据合并时报KeyError的错误。
    if gDeleteOutofBoundTrajectoryFlag == True:
        # Delete out of bounds .
        df_sampling = tbd.clean_outofbounds(df_sampling, bounds = gBounds, col = ['longitude', 'latitude'])
    
    if user == 118 or user == 132 or user == 160:
        print('\n m Null Trajectory columns {}'.format(df_sampling.columns))

    df_sampling['userID'] = user

    if gSaveUserTrajectoryFlag == True:
        df_sampling.to_csv(gOutputProecessedTrajectory.format(user))
    
    with lock:
        # sharedData.dat.append(df_sampling.copy())
        sharedData.dat = pd.concat([sharedData.dat, df_sampling])


def PreprocessTrajectory(userRange, 
                         outputType='merged',
                         userList=[]):
    """_summary_
    对轨迹数据进行处理。注意相关的超参数都是以全局变量的形式存储的。
    主要以对所有用户且保存为一个文件为主要选择项。
    Args:
        userRange (string): 有3个值可供选择：single, multi, all。
                        当range为all时，不需要用到userList。直接从TrajectoriesBasePath目录下读取所有的user轨迹。
        outputType (string): 有2个值可供选择： independent, merged。
                        independent表示每个用户生成独立的轨迹文件。
                        merged表示将所有用户组合成一个轨迹文件。
        userList (list): 需要读取的用户列表。需要和range配合使用，如果只读取一个用户的，那么userList中只有一个元素。
                        如果读取多个用户的，那么userList中会有多个用户。
                        如果读取全部用户的，那么userList中会有所有用户的ID。
    """
    saveLcoation = ''
    # 对所有用户进行处理。
    if userRange == 'all':
        userList = gUserList
        saveLcoation = (gOutputPath + 'Trajectory_{}.csv').format(userRange)
    # 处理输入的多个用户的轨迹。
    elif userRange == 'multi':
        if len(userList) == 0:
            print('ERROR, userRange {}, input userlist is NULL.'.format(userRange))
            return
        saveLcoation = (gOutputPath + 'Trajectory_{}.csv').format(userRange)
    # 处理输入的单个用户的轨迹。
    elif userRange == 'single':
        if len(userList) == 0:
            print('ERROR, userRange {}, input userlist is NULL.'.format(userRange))
            return
        # user = userList[0]
        saveLcoation = (gOutputPath + 'Trajectory_{}_{}.csv').format(userRange, userList[0])

    # 每个用户输出各自处理好的轨迹数据。
    if outputType == 'independent':
        gSaveUserTrajectoryFlag = True

        ProcessPool = multiprocessing.Pool()
        result = ProcessPool.map(PreprocessSingleTrajectoryIndependent, userList)

        ProcessPool.close()
        ProcessPool.join()
    # 将所有用户的轨迹数据合并成为一个文件输出。
    elif outputType == 'merged':
        startTime = cc.PrintStartInfo(functionName='PreprocessTrajectory')
        i = 0
        # MultiTrajectorys_pd = None

        ProcessPool = multiprocessing.Pool()
        ProcessManager = multiprocessing.Manager()
        ProcessSharedData = ProcessManager.Namespace()
        ProcessSharedData.dat = pd.DataFrame()
        ProecessLock = ProcessManager.Lock()
        for user in userList:
            ProcessPool.apply_async(PreprocessSingleTrajectoryMerged, 
                                    args=(user, ProcessSharedData, ProecessLock))
        
        ProcessPool.close()
        ProcessPool.join()

        # print('list len {} .'.format(len(ProcessSharedData.dat)))

        # MultiTrajectorys_pd = pd.concat(ProcessSharedData.dat)
 
        # 保存。
        ProcessSharedData.dat.to_csv(saveLcoation)
        # print('\n Output all user trajectory shape is {}. in this time, hast attach PoI feature.\n'.format(ProcessSharedData.dat.shape))
        cc.PrintEndInfo(functionName='PreprocessTrajectory', startTime=startTime)
        # return MultiTrajectorys_pd

## --- 将特征附着到轨迹上 ---

def AttachFeaturetoSingleUserTrajectoryByPolars(PoIFeature, user):

    startTime = cc.PrintStartInfo(functionName='AttachFeaturetoSingleUserTrajectoryByPolars()')

    userTrajectory = pl.read_csv(gOutputProecessedTrajectory.format(user), 
                                 has_header=True).lazy()
    userTrajectory = userTrajectory.with_columns(pl.col('grid').cast(pl.Int32))
    userTrajectory = userTrajectory.join(PoIFeature, 
                                         on='grid', how='left').fill_nan(0)
    
    userTrajectory = userTrajectory.collect(type_coercion=True,
                                            projection_pushdown=True)
    userTrajectory.write_csv(gSingleUserTrajectoryFeaturePath.format(user))
    cc.PrintEndInfo(functionName='AttachFeaturetoSingleUserTrajectoryByPolars()', startTime=startTime)

def AttachFeaturetoAllUsersTrajectoryByPolars():
    PoIFeature = pl.read_csv(gPoIFeatureSavePath, has_header=True).lazy()
    PoIFeature = PoIFeature.rename({PoIFeature.collect_schema().names()[0]: 'grid'})
    # PoIFeature.collect()
    PoIFeature = PoIFeature.with_columns(pl.col('grid').cast(pl.Int32))
    # PoIFeature_lazy = PoIFeature.lazy()
    PoIFeature.collect()

    AllUsersTrajectory = pl.read_csv(gOutputPath + 'Trajectory_all.csv', 
                                     has_header=True).lazy()
    AllUsersTrajectory = AllUsersTrajectory.with_columns(pl.col('grid').cast(pl.Int32))
    AllUsersTrajectory = AllUsersTrajectory.join(PoIFeature, 
                                                 on='grid', how='left').fill_nan(0)
    
    AllUsersTrajectory = AllUsersTrajectory.collect(type_coercion=True,
                                                    projection_pushdown=True)
    AllUsersTrajectory.write_csv(gAllUsersTrajectoryFeaturePath)

def AttachFeaturetoSingleUserTrajectoryByPolarsMultiProccess(user):
    """_summary_
    将特征附着到单个用户的轨迹上。在multiprocessing中使用。
    Args:
        user (_type_): 用户ID。
    """
    # print('p mp {} start'.format(user))
    PoIFeature = pl.read_csv(gPoIFeatureSavePath, has_header=True).lazy()
    PoIFeature = PoIFeature.rename({PoIFeature.collect_schema().names()[0]: 'grid'})
    # PoIFeature.collect()
    PoIFeature = PoIFeature.with_columns(pl.col('grid').cast(pl.Int32))
    PoIFeature.collect()

    userTrajectory = pl.read_csv(gOutputProecessedTrajectory.format(user), 
                                 has_header=True).lazy()
    userTrajectory = userTrajectory.with_columns(pl.col('grid').cast(pl.Int32))
    userTrajectory = userTrajectory.join(PoIFeature, 
                                         on='grid', how='left').fill_nan(0)
    
    userTrajectory = userTrajectory.collect(type_coercion=True,
                                            projection_pushdown=True)
    userTrajectory.write_csv(gSingleUserTrajectoryFeaturePath.format(user))
    # print('polars multiproccess {} completed.'.format(user))

def AttachFeaturetoSingleUserTrajectory(user):
    """_summary_
    将特征附着到单个用户的轨迹上。在multiprocessing中使用。
    Args:
        user (_type_): 用户ID。
    """
    PoIFeature = pd.read_csv(gPoIFeatureSavePath, index_col=0)
    PoIFeature['grid'] = PoIFeature.index
    # print('\n 1 {} PoIFeature shape is {}. columns {}.\n'.format(user, PoIFeature.shape, PoIFeature.columns))
    
    userTrajectory = pd.read_csv(gOutputProecessedTrajectory.format(user), index_col=0)

    userTrajectory = userTrajectory.merge(PoIFeature, 
                                          on='grid', how='left').fillna(0)
    # print('\n 1 {} UserTrajectory shape is {}. columns {}.\n'.format(user ,userTrajectory.shape, userTrajectory.columns))
    userTrajectory.to_csv(gSingleUserTrajectoryFeaturePath.format(user))


def MergeUsersTrajectoryandPoIFeature(chunk):
    PoIFeature = pd.read_csv(gPoIFeatureSavePath, index_col=0)
    PoIFeature['grid'] = PoIFeature.index
    # global gI
    # gI += 1
    # print(chunk.head(2))

    # print(chunk.columns)
    # print(PoIFeature.columns)
    merge_chunk = pd.merge(chunk, PoIFeature, on='grid', how='left').fillna(0)
    return merge_chunk

def AttachFeaturetoTrajectory(outputType='merged', chunksize = 250):
    """_summary_
    将特征附着到所有用户的轨迹上。
    Args:
        outputType (str, optional): _description_. Defaults to 'merged'.
    """
    startTime = cc.PrintStartInfo(functionName='AttachFeaturetoTrajectory()')

    # 输出每个用户各自的附着了特征之后的轨迹。
    if outputType == 'independent':
        userList = gUserList
        # ---
        ProcessPool = multiprocessing.Pool()
        ProcessPool.map(AttachFeaturetoSingleUserTrajectoryByPolarsMultiProccess, userList)

        ProcessPool.close()
        ProcessPool.join()
    # 输出所有用户附着了特征之后的轨迹为一个文件。
    elif outputType == 'merged':
        AttachFeaturetoAllUsersTrajectoryByPolars()
        # print('AttachFeaturetoTrajectory merged {} completed.'.format(datetime.datetime.now()))

    cc.PrintEndInfo(functionName='AttachFeaturetoTrajectory()', startTime=startTime)

# --- 输出其他格式 ---

def GenerateInteractionMatrix():
    """_summary_
    生成交互矩阵。
    """
    startTime = cc.PrintStartInfo(functionName='GenerateInteractionMatrix()')
    Trajectories = pd.read_csv(gAllUsersTrajectoryFeaturePath, 
                            #    index_col=0,
                               usecols=['latitude', 'grid', 'userID', 'longitude'])
    # 是否删除所有范围之外的地点。
    if gDeleteOutofBoundTrajectoryFlag == True:
        Trajectories = tbd.clean_outofbounds(Trajectories, gBounds, col=['longitude', 'latitude'])
    # 选择最终进行透视的列。'latitude'列只是作为最后 aggfunc='count' 的存在。
    # Trajectories = Trajectories[['grid', 'userID', 'latitude']]
    # InteractionMatrix = Trajectories.pivot_table(index='userID',columns='grid', 
    #                                              values='latitude', aggfunc='count').fillna(0).copy()
    # # 保存。
    # InteractionMatrix.to_csv(gOutputPath + 'InteractionMatrix.csv')

    Trajectories = pl.from_pandas(Trajectories[['grid', 'userID', 'latitude']])
    InteractionMatrix = Trajectories.pivot(index='userID', 
                                           on='grid', 
                                           values='latitude', 
                                           aggregate_function='len')
    InteractionMatrix.write_csv(gOutputPath + 'InteractionMatrix.csv')

    cc.PrintEndInfo(functionName='GenerateInteractionMatrix()', startTime=startTime)

# 将numpy.narray的3维数据保存为csv格式。
def np_3d_to_csv(data, 
                 path, 
                 datatype='float'):
    a2d = data.reshape(data.shape[0], -1)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(a2d)

# 从3维数据中读取numpy.narray格式。
def np_3d_read_csv(path='./Data/Output/StayMatrx/{}.csv',
                   shape=(-1, 128, 3),
                   datatype='float'):
    
    # 从csv文件读取2D数组
    with open(path, "r") as f:
        reader = csv.reader(f)
        a2d = np.array(list(reader)).astype(datatype)

    # 将2D数组转换为3D数组
    a = a2d.reshape(shape)
    # print(a.shape)
    return a

# 删除全为零的行。
def drop_all_0_rows(df):
    return df.drop(index=df[(df == 0).all(axis=1)].index)

# 生成特征矩阵时需要对所有的特征进行归一化。
from sklearn.preprocessing import MinMaxScaler


def SeriesToMatrix(user, data, interval='M', maxrow=128,
                   dropColunms=['stime', 'etime', 'stayid', 'lon', 'lat']):
    """_summary_
    将轨迹的序列形式转换为矩阵形式。
    传入转换之间必须将特征全部附着到轨迹上。
    Args:
        user (int): 用户ID
        data (pandas.DataFrame): 已经融合了特征的轨迹序列。
        interval (str, optional): 提取停留点的周期. Defaults to 'M'.
        maxrow (int, optional): _description_. Defaults to 128.

    Returns:
        numpy.narray : 返回numpy.narray同时，也保存为了csv格式。
    """
    
    stay = data.copy()
    # if user stay martix is empty, it will reture Empty DataFrame.
    # and don't save result.
    if stay.shape[0] == 0:
        print('------{} stay shape is zero.'.format(user))
        result = pd.DataFrame()
        FeatureThirdDimension = stay.shape[1] - len(dropColunms)
    else:
        pass
        # print('3 stay shape {}'.format(stay.shape))
        # print(stay.head(2))
        # print(stay.columns)

        # 获得时间戳。
        stay['stimestamp'] = stay['stime'].astype('int64') // 1e9
        # stay.head()
        # print('3.1 stay shape {}'.format(stay.shape))

        stayGroup = stay.groupby(pd.Grouper(key='stime', freq=interval))

        FeatureThirdDimension = stay.shape[1] - len(dropColunms)
        # 创建一个空的result矩阵。
        result = np.empty((0, maxrow, FeatureThirdDimension))

        # print((0, maxrow, FeatureThirdDimension))
        
        for g in stayGroup:
            # 取月份值。
            key = g[0].month
            # print(type(key))
            
            # 取所有特征量。
            # 之所以需要copy一次是因为
            df = g[1].copy()
            # delete unneccessary columns.
            df.drop(dropColunms, axis=1, inplace=True)
            # 删除全为零的行。
            df  = drop_all_0_rows(df)

            value = df.values
            # 因为需要由2维矩阵变为3维矩阵，所有需要变为numpy.narray类型。
            # value = f2.values
            
            # 之前再f1的时候已经处理了。这里就不再继续处理了。
            # 删除全为NaN的行。
            # value.dropna(axis=0, how='all', inplace=True)

            # 如果行数为0，也就是说没有轨迹点。那么就跳过。
            if value.shape[0] == 0:
                continue
            # 将轨迹填充为相同的形状。
            # 对于大于设置超参数的行数（2维时的行数），也就是interval下的最多stay数量，处理方式需要另外实现。
            if value.shape[0] > maxrow:
                continue
            else:
                # 将不足interval下最多stay数量的矩阵填充为maxrow（2维时的行数）的数值。
                value = np.pad(array=value, pad_width=((0,maxrow-value.shape[0]),(0,0)), mode='constant')

            # 将单个用户的所有interval下的轨迹组合起来。合并之后的结果是一个三维矩阵。
            result = np.concatenate((result, value[np.newaxis,:]), axis=0)
        
        # print(result.shape)

        # 保存。
        np_3d_to_csv(result, gSingleUserStayMatrixSavePath.format(user))

    # print('{} SeriesToMatrix have completed. FeatureThirdDimension is {}'.format(user, FeatureThirdDimension))
    return result, FeatureThirdDimension

def ColumnContainJudgement(df, columnName, difference=''):
    """_summary_
    判断Dataframe列中是否存在 columnName 的列名。
    Args:
        df (pandas.dataframe): 被判断的dataframe。
        columnName (string): 被判断是否存在的列名。
        difference (string): 区别不同打印位置的标识。
    Returns:
        boolean: 是否存在输入的列名。
    """
    result = df.columns[df.columns.str.contains(columnName)]
    if len(result) != 0:
        # print('{} True {}'.format(difference, result))
        return True
    else:
        print('{} False {}, shape is {}.'.format(difference, df.columns, df.shape))
        return False

def GenerateSingleUserStayMove(user):
    """_summary_
    生成单个用户的特征。在处理整个用户轨迹特征文件的时候非常耗时。所以推荐使用分别处理每个单个用户的轨迹特征。
    Args:
        user (_type_): _description_
    """

    startTime = cc.PrintStartDebug(functionName='GenerateSingleUserStayMove', 
                                  description='Start')
    # 读取轨迹。
    userTrajectory = pd.read_csv(gSingleUserTrajectoryFeaturePath.format(user), 
                                 index_col=0,
                                 parse_dates=['entireTime'])
    # print('\n 2 {} UserTrajectory shape is {}. \n'.format(user ,userTrajectory.shape))
    # print('\n ---2 {} UserTrajectory shape is {}. \n'.format(user ,userTrajectory.shape))
    columns = userTrajectory.columns
    # 首先判断轨迹是否为空。也就是用户的轨迹都在设置的区域之外。118, 132, 160三个用户在设置区域之外。
    if userTrajectory.shape[0] == 0:
        stay = pd.DataFrame(columns=['userID', 'stime', 'LONCOL', 'LATCOL', 'etime',
                                      'lon', 'lat', 'duration', 'stayid', 'grid', 
                                      'weekofyear', 'dayofweek', 'dayofyear','quarter', 'month', 
                                      'hour', '0.0', '1.0', '2.0', '3.0', 
                                      '4.0', '5.0', '6.0', '7.0', '8.0', 
                                      '9.0', '10.0', '11.0', '12.0', '13.0'])
        move = pd.DataFrame(columns=['userID', 'SLONCOL', 'SLATCOL', 'stime', 'slon', 
                                     'slat', 'etime', 'elon', 'elat', 'ELONCOL', 
                                     'ELATCOL', 'duration', 'moveid', 'grid', 'weekofyear', 
                                     'dayofweek', 'dayofyear', 'quarter', 'month', 'hour'])
    else:
        # 去掉范围之外的轨迹。
        if gDeleteOutofBoundTrajectoryFlag == True:
            userTrajectory = tbd.clean_outofbounds(userTrajectory, 
                                            gBounds, 
                                            col=['longitude', 'latitude'])

        stay, move = tbd.traj_stay_move(userTrajectory, 
                                    gGeoParameters,
                                    col=['userID', 'entireTime', 'longitude', 'latitude'], 
                                    activitytime=gActivityTime)
        
        # 设置的判断是否为stay点的时间超参数是30分钟，判断没有生成停留点数据。
        # 049, 120, 123, 137, 178 四个用户没有生成停留点。
        if stay.shape[0] == 0:
            stay = pd.DataFrame(columns=['userID', 'stime', 'LONCOL', 'LATCOL', 'etime',
                                      'lon', 'lat', 'duration', 'stayid', 'grid', 
                                      'weekofyear', 'dayofweek', 'dayofyear','quarter', 'month', 
                                      'hour', '0.0', '1.0', '2.0', '3.0', 
                                      '4.0', '5.0', '6.0', '7.0', '8.0', 
                                      '9.0', '10.0', '11.0', '12.0', '13.0'])
            ColumnContainJudgement(stay, 'grid', '{} stay'.format(user))
        else:
            # 生成grid。
            stay = stay.apply(cc.GenerateGrid, lonColName='LONCOL', latColName='LATCOL', axis=1)
            # 生成时间特征。时间戳的特征也会在后面获取。
            stay = stay.apply(GenerateTimeFeature, axis=1)


            # # 读取所有特征。
            # PoIFeature = pd.read_csv(gPoIFeatureSavePath, index_col=0)
            # PoIFeature['grid'] = PoIFeature.index
            # # 将通过PoI获得的特征以及其他特征和停留点特征合并。
            # # mmm
            # stay = stay.merge(PoIFeature, on='grid', how='left').fillna(0)

            PoIFeature = pl.read_csv(gPoIFeatureSavePath, has_header=True).lazy()
            PoIFeature = PoIFeature.rename({PoIFeature.collect_schema().names()[0]: 'grid'})
            PoIFeature = PoIFeature.with_columns(pl.col('grid').cast(pl.Int32))
            PoIFeature.collect()
            stay = pl.from_pandas(stay).lazy()
            stay = stay.join(PoIFeature,
                             on='grid', how='left').fill_nan(0)
            stay = stay.collect(type_coercion=True,
                                projection_pushdown=True)
            stay = stay.to_pandas()

        if move.shape[0] == 0:
            move = pd.DataFrame(columns=['userID', 'SLONCOL', 'SLATCOL', 'stime', 'slon', 
                                        'slat', 'etime', 'elon', 'elat', 'ELONCOL', 
                                        'ELATCOL', 'duration', 'moveid', 'grid', 'weekofyear', 
                                        'dayofweek', 'dayofyear', 'quarter', 'month', 'hour'])
            ColumnContainJudgement(move, 'grid', '{} move'.format(user))
        else:
            # 生成grid。
            move = move.apply(cc.GenerateGrid, lonColName='SLONCOL', latColName='SLATCOL', axis=1)
            # 生成时间特征。时间戳的特征也会在后面获取。
            move = move.apply(GenerateTimeFeature, axis=1)
            # move contain feature of start place and feature of end place.
            # so, feature of move need special process.
            # move = move.merge(PoIFeature, on='grid', how='left').fillna(0)
            # 读取所有特征。
            # PoIFeature = pd.read_csv(gPoIFeatureSavePath, index_col=0)
            # PoIFeature['grid'] = PoIFeature.index

    # save data.
    stay.to_csv(gSingleUserStaySavePath.format(user))
    move.to_csv(gSingleUserMoveSavePath.format(user))

    cc.PrintEndDebug(functionName='GenerateSingleUserStayMove', 
                    startTime=startTime, 
                    description='End')


def GenerateStayMoveByChunk(chunk):
    # startTime = cc.PrintStartInfo('GenerateStayMoveByChunk()')
    if gDeleteOutofBoundTrajectoryFlag == True:
        chunk = tbd.clean_outofbounds(chunk, gBounds, col=['longitude', 'latitude'])

    # user stay and move to decide sentence length .
    # , 'grid'
    stay, move = tbd.traj_stay_move(chunk, 
                                gGeoParameters,
                                col=['userID', 'entireTime', 'longitude', 'latitude'],
                                activitytime=gActivityTime)
    
    # PoIFeature = pd.read_csv(gPoIFeatureSavePath, index_col=0)
    # PoIFeature['grid'] = PoIFeature.index

    PoIFeature = pl.read_csv(gPoIFeatureSavePath, has_header=True).lazy()
    PoIFeature = PoIFeature.rename({PoIFeature.collect_schema().names()[0]: 'grid'})
    PoIFeature = PoIFeature.with_columns(pl.col('grid').cast(pl.Int32))
    PoIFeature.collect()
    
    # function will return an empty dataframe, when stay, move is empty.
    if stay.shape[0] != 0:
        # # 生成grid。
        stay = stay.apply(cc.GenerateGrid, lonColName='LONCOL', latColName='LATCOL', axis=1)
        # 需要生成时间特征。
        stay = stay.apply(GenerateTimeFeature, col='etime', axis=1)
        # # tbd.traj_stay_move() drop other feature. so must merge PoI feature again.
        # # 将通过PoI获得的特征以及其他特征和停留点特征合并。
        # stay = stay.merge(PoIFeature, on='grid', how='left').fillna(0)

        stay = pl.from_pandas(stay).lazy()
        stay = stay.with_columns(pl.col('grid').cast(pl.Int32))
        # print(stay.columns, PoIFeature.columns)
        stay = stay.join(PoIFeature,
                         on='grid', how='left').fill_nan(0)
        stay = stay.collect(type_coercion=True,
                            projection_pushdown=True)
        stay = stay.to_pandas()
    else:
        stay = pd.DataFrame()

    if move.shape[0] != 0:
        move = move.apply(cc.GenerateGrid, lonColName='SLONCOL', latColName='SLATCOL', axis=1)
        move = move.apply(GenerateTimeFeature, col='etime', axis=1)
        # move contain feature of start place and feature of end place.
        # so, feature of move need special process.
        # move = move.merge(PoIFeature, on='grid', how='left').fillna(0)

        move = pl.from_pandas(move).lazy()
        move = move.with_columns(pl.col('grid').cast(pl.Int32))
        # print(stay.columns, PoIFeature.columns)
        move = move.join(PoIFeature,
                         on='grid', how='left').fill_nan(0)
        move = move.collect(type_coercion=True,
                            projection_pushdown=True)
        move = move.to_pandas()
    else:
        move = pd.DataFrame()

    # cc.PrintEndInfo('GenerateStayMoveByChunk()', startTime=startTime)
    return stay, move

def GenerateStayMove(ProcessType = 'independent'):
    """_summary_
    生成特征矩阵。
    """
    startTime = cc.PrintStartInfo('GenerateStayMove()', description=ProcessType)
    # 对每个用户单独进行处理。
    if ProcessType == 'independent':
        logging.DEBUG("start GenerateStayMove independent.")
        userList = gUserList
        ProcessPool = multiprocessing.Pool()
        ProcessPool.map(GenerateSingleUserStayMove, userList)

        ProcessPool.close()
        ProcessPool.join()
        logging.DEBUG("end GenerateStayMove independent.")
    # 处理所有用户整个处于一个csv中。效率比较低。推荐使用independent模式。
    elif ProcessType == 'merged':
        # Trajectories = pd.read_csv(gAllUsersTrajectoryFeaturePath, 
        #                         index_col=0, parse_dates=['entireTime'])
        # if gDeleteOutofBoundTrajectoryFlag == True:
        #     Trajectories = tbd.clean_outofbounds(Trajectories, gBounds, col=['longitude', 'latitude'])
        
        # # 需要生成时间特征。
        # Trajectories = Trajectories.apply(GenerateTimeFeature, axis=1)

        # # 高度信息不能丢弃，也作为一种特征。
        # # 需要判断停留点。
        # # 需要的将地点的文字描述embedding之后也作为特征保存在特征矩阵中。
        
        # # user stay and move to decide sentence length .
        # stay, move = tbd.traj_stay_move(Trajectories, 
        #                             gGeoParameters,
        #                             col=['userID', 'entireTime', 'longitude', 'latitude', 'grid'],
        #                             activitytime=gActivityTime)

        chunksize = 100
        chunks = pd.read_csv(gAllUsersTrajectoryFeaturePath, 
                    index_col=0, parse_dates=['entireTime'],
                    date_format='%Y-%m-%d %H:%M:%S',
                    chunksize=chunksize)
        ProcessPool = multiprocessing.Pool()
        results = ProcessPool.map(GenerateStayMoveByChunk, chunks)

        ProcessPool.close()
        ProcessPool.join()

        cc.PrintEndInfo('GenerateStayMove() multiprocess completed.', startTime=startTime)

        stays = pd.DataFrame()
        moves = pd.DataFrame()
        for stay, move in results:
            # print("--- stay format :{}".format(type(stay)))
            # stays.append(stay)
            # moves.append(move)
            stays = pd.concat([stays, stay])
            moves = pd.concat([moves, move])
            
        # stays = pd.concat(stay)
        # moves = pd.concat(move)

        # print('Output all users stays shape is {}.'.format(stays.shape))

        stays.to_csv(gStaySavePath)
        moves.to_csv(gMoveSavePath)

    cc.PrintEndInfo('GenerateStayMove()', startTime=startTime)

def GenerateSingleUserFeatureMatrix(user, shareData, lock):
    # 读取所有特征。
    # has merge poi feature in generate stay.
    # so delete above code.
    # PoIFeature = pd.read_csv(gPoIFeatureSavePath, index_col=0)
    # PoIFeature['grid'] = PoIFeature.index

    stay = pd.read_csv(gSingleUserStaySavePath.format(user), index_col=0)
    stay['stime'] = pd.to_datetime(stay['stime'])

    # 将通过PoI获得的特征以及其他特征和停留点特征合并。
    # stay = stay.merge(PoIFeature, on='grid', how='left').fillna(0)
    # 生成矩阵并保存。
    with lock:
        _, shareData.dat = SeriesToMatrix(user=user, 
                                         data=stay, 
                                         interval='M', 
                                         maxrow=gMaxRow)
        # print('--- shareData.dat {}'.format(shareData.dat))

def GenerateFeatureMatrix(ProcessType = 'independent'):
    startTime = cc.PrintStartInfo('GenerateFeatureMatrix()')
    # 对每个用户单独进行处理。
    if ProcessType == 'independent':
        userList = gUserList
        ProcessPool = multiprocessing.Pool()
        ProcessManager = multiprocessing.Manager()
        Lock = ProcessManager.Lock()
        ShareData = ProcessManager.Namespace()
        ShareData.dat = None

        for user in userList:
            ProcessPool.apply_async(GenerateSingleUserFeatureMatrix, args=(user, ShareData, Lock))

        ProcessPool.close()
        ProcessPool.join()
        gFeatureThirdDimension = ShareData.dat
        # print('--- gFeatureThirdDimension {}'.format(gFeatureThirdDimension))

        # global gFeatureThirdDimension
        # gFeatureThirdDimension = ShareData.dat.shape[2]
        # print("GenerateFeatureMatrix gFeatureThirdDimension is {}".format(gFeatureThirdDimension))
    elif ProcessType == 'merged':
        pass
    cc.PrintEndInfo('GenerateFeatureMatrix()', startTime=startTime)

def CombineUsersMatrix(FeatureThirdDimension=28):
    """_summary_
    将多个用户的轨迹矩阵合并为一个整体的轨迹矩阵，用于transformer的训练。
    Args:
        FeatureThirdDimension (int, optional): 千万注意，当前面的特征变化之后，这个值也是需要随之变化的. Defaults to 28.

    Returns:
        _type_: _description_
    """

    # stay = pd.read_csv(gSingleUserStaySavePath.format(gUserList[0]), index_col=0)
    # FeatureThirdDimension = stay.shape[1] - len(dropColunms)
    # 18 gFeatureThirdDimension

    # print('FeatureThirdDimension {}, gFeatureThirdDimension {}'.format(FeatureThirdDimension, gFeatureThirdDimension))
    FeatureShape = (-1, gMaxRow, FeatureThirdDimension)
    # print('CombineUsersMatrix start. FeatureShape is {}'.format(FeatureShape))
    # 所有用户的轨迹特征存储。
    AllUsersTrajectoriesFeature = np.empty((0, gMaxRow, FeatureThirdDimension))

    for user in gUserList:
        try:
            # 如果所有用户中有些用户的轨迹并没有生成，就需要跳过。
            if os.path.exists(gSingleUserStayMatrixSavePath.format(user)) == False:
                continue

            userFeature = np_3d_read_csv(gSingleUserStayMatrixSavePath.format(user), shape=FeatureShape)
            # print(userFeature.shape)
            # print(AllUsersTrajectoriesFeature.shape)
            AllUsersTrajectoriesFeature = np.concatenate((AllUsersTrajectoriesFeature, userFeature), axis=0)
        except:
            print('Error {}.'.format(user))

    np_3d_to_csv(AllUsersTrajectoriesFeature, gAllUsersTrajectoriesFeatureMatrixSavePath)
    
    print('CombineUsersMatrix has completed.')
    return AllUsersTrajectoriesFeature 

if __name__ == '__main__':
    # 配置日志文件。
    log_dir = './logs'
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'AF.log')
    logging.basicConfig(filename=log_file, 
                        level=logging.DEBUG, 
                        format='%(asctime)s -%(levelname)s - %(message)s')
    
    GetParameters('./Parameters.json')
    startTime = datetime.datetime.now()

    # consume 0:25:15.510780. 
    if gRefreshDataFlag == True:
        gSaveUserTrajectoryFlag = True
        PreprocessTrajectory(userRange='all', outputType='merged')
        endTime2 = datetime.datetime.now()
        print("PreprocessTrajectory completed. {}".format(endTime2 - startTime))
    else:
        endTime2 = datetime.datetime.now()
        print("PreprocessTrajectory don't processing. {}".format(endTime2 - startTime))

    # consume 0:00:22.425468 .
    # 两种模式都需要处理一次，主要时候后面最终输出为不同的格式时需要不同的数据形状。
    # 生成交互矩阵需要使用所有用户在一个dataframe的形式。
    # 在生成轨迹特征的时候，单独处理一个dataframe效率太低，建议使用分别处理每个用户的形式。
    AttachFeaturetoTrajectory(outputType='independent')
    endTime30 = datetime.datetime.now()
    print("AttachFeaturetoTrajectory independent completed. {}".format(endTime30 - endTime2))
    
    # consume 0:00:35.126483 .
    AttachFeaturetoTrajectory(outputType='merged')
    endTime31 = datetime.datetime.now()
    print("AttachFeaturetoTrajectory merged completed. {}".format(endTime31 - endTime2))

    # # consume 0:00:24.995880 .
    # # 需要将区域外的地点都排除。
    gDeleteOutofBoundTrajectoryFlag = True
    GenerateInteractionMatrix()
    endTime4 = datetime.datetime.now()
    print("GenerateInteractionMatrix completed. {}".format(endTime4 - endTime31))

    # consume time: 0:38:29.876277 .
    # 建议使用对每个用户分别处理的形式。最后再进行合并效率比较高。
    # test gfg.gUserList = ['079', '047']
    gDeleteOutofBoundTrajectoryFlag = True
    GenerateStayMove(ProcessType='independent')
    endTime50 = datetime.datetime.now()
    # endTime4
    print("GenerateStayMove independent completed. {}".format(endTime50 - endTime4))
    
    # consume time: 0:59:01.930863
    GenerateStayMove(ProcessType='merged')
    endTime51 = datetime.datetime.now()
    print("GenerateStayMove merged completed. {}".format(endTime51 - endTime50))
    
    # consume time: 0:00:03.740401.
    GenerateFeatureMatrix(ProcessType='independent')
    endTime6 = datetime.datetime.now()
    print("GenerateFeatureMatrix completed. {}".format(endTime6 - endTime51))

    # consume time: 0:00:07.420286.
    CombineUsersMatrix(FeatureThirdDimension=28)
    endTime7 = datetime.datetime.now()
    print("CombineUsersMatrix completed. {}".format(endTime7 - endTime6))

    print("All completed. {}".format(endTime7 - startTime))