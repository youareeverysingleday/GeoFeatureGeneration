
# Author: youareeverysingleday
# contact: 
# CreationTime: 2024/01/15 11:29
# software: VSCode
# LastEditTime: 
# LastEditors: youareeverysingleday
# Description: generate geographic feature.

# This package can not run in jupyter, because package has used "mulitprocessing".

import pandas as pd
import numpy as np
import datetime
import time

import os
import sys
import math

import multiprocessing

import geopandas as gpd


def convertparams(params):
    # Convertparams from list to dict
    if (type(params) == list) | (type(params) == tuple):
        if len(params) == 4:
            lonStart, latStart, deltaLon, deltaLat = params
            theta = 0
            method = 'rect'
        elif len(params) == 5:
            lonStart, latStart, deltaLon, deltaLat, theta = params
            method = 'rect'
        elif len(params) == 6:  # pragma: no cover
            lonStart, latStart, deltaLon, deltaLat, theta, method = params  # pragma: no cover
        dicparams = dict()
        dicparams['slon'] = lonStart
        dicparams['slat'] = latStart
        dicparams['deltalon'] = deltaLon
        dicparams['deltalat'] = deltaLat
        dicparams['theta'] = theta
        dicparams['method'] = method
    else:
        dicparams = params
        if 'theta' not in dicparams:
            dicparams['theta'] = 0  # pragma: no cover
        if 'method' not in dicparams:
            dicparams['method'] = 'rect'  # pragma: no cover
    if dicparams['method'] not in ['rect', 'tri', 'hexa']:
        raise ValueError(
            'Method should be `rect`,`tri` or `hexa`')  # pragma: no cover
    return dicparams

def area_to_params(location, accuracy=500, method='rect'):
    '''
    Generate gridding params

    Parameters
    -------
    location : bounds(List) or shape(GeoDataFrame)
        Where to generate grids.
        If bounds, [lon1, lat1, lon2, lat2](WGS84), where lon1 , lat1 are the
        lower-left coordinates, lon2 , lat2 are the upper-right coordinates
        If shape, it should be GeoDataFrame
    accuracy : number
        Grid size (meter)
    method : str
        rect, tri or hexa


    Returns
    -------
    params : list or dict
        Gridding parameters. 
        See https://transbigdata.readthedocs.io/en/latest/grids.html 
        for detail information about gridding parameters.

    '''
    if (type(location) == list) | (type(location) == tuple):
        shape = ''
        bounds = location
    elif type(location) == gpd.geodataframe.GeoDataFrame:
        shape = location
        bounds = shape.unary_union.bounds
    lon1, lat1, lon2, lat2 = bounds
    if (lon1 > lon2) | (lat1 > lat2) | (abs(lat1) > 90) | (abs(lon1) > 180) | (
            abs(lat2) > 90) | (abs(lon2) > 180):
        raise Exception(   # pragma: no cover
            'Bounds error. The input bounds should be in the order '
            'of [lon1,lat1,lon2,lat2]. (lon1,lat1) is the lower left '
            'corner and (lon2,lat2) is the upper right corner.'
        )
    latStart = min(lat1, lat2)
    lonStart = min(lon1, lon2)
    deltaLon = accuracy * 360 / \
        (2 * math.pi * 6371004 * math.cos((lat1 + lat2) * math.pi / 360))
    deltaLat = accuracy * 360 / (2 * math.pi * 6371004)
    params = [lonStart, latStart, deltaLon, deltaLat]
    params = convertparams(params)
    params['gridsize'] = accuracy
    params['method'] = method

    # 获取最大行数和列数。
    params['maxlatcol'] = math.floor(abs(lat2 - lat1) / deltaLat)
    params['maxloncol'] = math.floor(abs(lon2 - lon1) / deltaLon)
    return params

def GPS_to_grids_rect(lon, lat, params, from_origin=False):
    '''
    Match the GPS data to the grids. The input is the columns of
    longitude, latitude, and the grids parameter. The Output is the grid ID.

    Parameters
    -------
    lon : Series
        The column of longitude
    lat : Series
        The column of latitude
    params : List
        Gridding parameters (lonStart, latStart, deltaLon, deltaLat) or
        (lonStart, latStart, deltaLon, deltaLat, theta).
        lonStart and latStart are the lower-left coordinates;
        deltaLon, deltaLat are the length and width of a single grid;
        theta is the angle of the grid, it will be 0 if not given.
        When Gridding parameters is given, accuracy will not be used.
    from_origin : bool
        If True, lonStart and latStart are the lower left of the first
        grid.
        If False, lonStart and latStart are the center of the first
        grid.

    Returns
    -------
    LONCOL : Series
        The index of the grid longitude. The two columns LONCOL and
        LATCOL together can specify a grid.
    LATCOL : Series
        The index of the grid latitude. The two columns LONCOL and
        LATCOL together can specify a grid.
    '''
    params = convertparams(params)
    lonStart = params['slon']
    latStart = params['slat']
    deltaLon = params['deltalon']
    deltaLat = params['deltalat']
    theta = params['theta']
    maxlatcol = params['maxlatcol']
    maxloncol = params['maxloncol']

    lon = pd.Series(lon)
    lat = pd.Series(lat)
    costheta = np.cos(theta * np.pi / 180)
    sintheta = np.sin(theta * np.pi / 180)
    R = np.array([[costheta * deltaLon, -sintheta * deltaLat],
                  [sintheta * deltaLon, costheta * deltaLat]])
    coords = np.array([lon, lat]).T
    if from_origin:
        coords = coords - (np.array([lonStart, latStart]))
    else:
        coords = coords - (np.array([lonStart, latStart]) - R[0, :] / 2 -
                           R[1, :] / 2)
    res = np.floor(np.dot(coords, np.linalg.inv(R)))
    loncol = res[:, 0].astype(int)
    latcol = res[:, 1].astype(int)
    if len(loncol) == 1:
        loncol = loncol[0]
        latcol = latcol[0]

    gridid = loncol * maxloncol + latcol
    # print(loncol, latcol, maxloncol)
    return loncol, latcol, gridid


def GPS_to_grid(lon, lat, params):
    '''
    Match the GPS data to the grids. The input is the columns of
    longitude, latitude, and the grids parameter. The Output is the grid ID.

    Parameters
    -------
    lon : Series
        The column of longitude
    lat : Series
        The column of latitude
    params : list or dict
        Gridding parameters. 
        See https://transbigdata.readthedocs.io/en/latest/grids.html 
        for detail information about gridding parameters.

    Returns
    -------

    `Rectangle grids`
    [LONCOL,LATCOL] : list
        The two columns LONCOL and LATCOL together can specify a grid.

    `Triangle and Hexagon grids`
    [loncol_1,loncol_2,loncol_3] : list
        The index of the grid latitude. The two columns LONCOL and
        LATCOL together can specify a grid.
    '''
    params = convertparams(params)
    method = params['method']
    if method == 'rect':
        loncol, latcol, gridid = GPS_to_grids_rect(lon, lat, params)
        return [loncol, latcol, gridid]
    # if method == 'tri':
    #     loncol_1, loncol_2, loncol_3 = GPS_to_grids_tri(lon, lat, params)
    #     return [loncol_1, loncol_2, loncol_3]
    # if method == 'hexa':
    #     loncol_1, loncol_2, loncol_3 = GPS_to_grids_hexa(lon, lat, params)
    #     return [loncol_1, loncol_2, loncol_3]


def clean_outofbounds(data, bounds, col=['Lng', 'Lat']):
    '''
    剔除范围之外的坐标。这种情况下也就是无法处理出差的情况。
    需要将出现在范围之外的情况做特别的处理。
    The input is the latitude and longitude coordinates of the lower
    left and upper right of the study area and exclude data that are
    outside the study area

    Parameters
    -------
    data : DataFrame
        Data
    bounds : List
        Latitude and longitude of the lower left and upper right of
        the study area, in the order of [lon1, lat1, lon2, lat2]
    col : List
        Column name of longitude and latitude

    Returns
    -------
    data1 : DataFrame
        Data within the scope of the study
    '''
    lon1, lat1, lon2, lat2 = bounds
    if (lon1 > lon2) | (lat1 > lat2) | (abs(lat1) > 90) | (
            abs(lon1) > 180) | (abs(lat2) > 90) | (abs(lon2) > 180):
        raise Exception(  # pragma: no cover
            'Bounds error. The input bounds should be in the order \
of [lon1,lat1,lon2,lat2]. (lon1,lat1) is the lower left corner and \
(lon2,lat2) is the upper right corner.')
    Lng, Lat = col
    data1 = data.copy()
    data1 = data1[(data1[Lng] > bounds[0]) & (data1[Lng] < bounds[2]) & (
        data1[Lat] > bounds[1]) & (data1[Lat] < bounds[3])]
    return data1

def special_outofbounds(data, bounds, col=['Lng', 'Lat']):
    """_summary_
    特别处理在地理范围之外的区域。
    Args:
        data (_type_): _description_
        bounds (_type_): _description_
        col (list, optional): _description_. Defaults to ['Lng', 'Lat'].

    Raises:
        Exception: _description_
    """
    lon1, lat1, lon2, lat2 = bounds
    if (lon1 > lon2) | (lat1 > lat2) | (abs(lat1) > 90) | (
            abs(lon1) > 180) | (abs(lat2) > 90) | (abs(lon2) > 180):
        raise Exception(  # pragma: no cover
            'Bounds error. The input bounds should be in the order \
of [lon1,lat1,lon2,lat2]. (lon1,lat1) is the lower left corner and \
(lon2,lat2) is the upper right corner.')
    Lng, Lat = col
    data1 = data.copy()
    data1 = data1[(data1[Lng] > bounds[0]) & (data1[Lng] < bounds[2]) & (
        data1[Lat] > bounds[1]) & (data1[Lat] < bounds[3])]
    return data1


# --- 辅助函数 --

def PrintStartInfo(functionName, description=''):
    startTime = datetime.datetime.now()
    print('Start function: {} ,\npid: {} ,\nstart at: {} .'.format(functionName, os.getpid(), startTime.strftime('%Y-%m-%d %H:%M:%S')))
    if description != '':
        print(description)
    
    return startTime

def PrintEndInfo(functionName, startTime, description=''):
    print('End function: {} ,\npid: {} ,\ncompleted time: {} ,\nconsume time: {} .'.format(functionName, os.getpid(), 
                                                                                    datetime.datetime.now(), 
                                                                                    datetime.datetime.now() - startTime))
    if description != '':
        print(description)

# --- 全局变量设置 ---

#地理特征边界。
gBounds = [115.7, 39.4, 117.4, 41.6]
# 所有的地理参数。
gGeoParameters = area_to_params(gBounds, accuracy = 1000, method='rect')

# PoI特征输入目录。
gPoIFolderPath = './Data/BeiJing/'
# 保存PoI特征的路径及文件名. Defaults to './Data/Output/PoIFeature.csv'.
gPoIMatrixSavePath = './Data/Output/MultipleFeatures/PoIFeature.csv'
gRenameColumns = {'名称':'name','大类':'category','中类':'class', '小类':'type', 
                    '省':'province', '市':'city', '区':'district', 'WGS84_经度':'longitude', 'WGS84_纬度':'latitude'}
gFileterColumne = ['名称', '大类', '中类', '小类', '省', '市', '区', 'WGS84_经度', 'WGS84_纬度']
gSelectedColumne = ['category', 'longitude', 'latitude']
gCategoryMapNumber = {'餐饮服务':0, '商务住宅':1, '公共设施':2, '公司企业':3, '风景名胜':4, 
                    '金融保险服务':5, '政府机构及社会团体':6, '医疗保健服务':7, '生活服务':8, 
                    '餐饮服务':9, '科教文化服务':10, '购物服务':11, '体育休闲服务':12, '交通设施服务':13}


# 轨迹数据的存储目录。
gTrajectoryFolderPath = "./Data/Geolife Trajectories 1.3/Data/"
# InputTrajectoryCsvSavePath = './Data/output/Trajectories/{}.csv'
# 单个用户的保存目录。
gOutputProecessedTrajectory='./Data/output/ProcessedTrajectories/{}.csv'
# 所有用户的保存目录。
gInputTrajectoryCsvSavePath = './Data/output/Trajectories/{}.csv'
# 保存的输出的根目录。
gSavePath='./Data/output/'
# TrajectoriesBasePath = './Data/Geolife Trajectories 1.3/Data/'
        

# --- 获取PoI特征 ---

def GeneratePoIFeature(FilePath, fileParameters, GeoParameters, gSharedData, lock):
    """_summary_
    生成PoI特征。
    Args:
        FilePath (_type_): _description_
        fileParameters (_type_): _description_
        GeoParameters (_type_): _description_
        gSharedData (_type_): _description_
        lock (_type_): _description_
    """
    renameColumns = fileParameters['renameColumns']
    FileterColumne = fileParameters['FileterColumne']
    SelectedColumne = fileParameters['SelectedColumne']
    CategoryMapNumber = fileParameters['CategoryMapNumber']

    # 读取数据。
    df = pd.read_csv(FilePath, encoding='gb18030')
    
    # 将列名修改为英文。
    df = df[FileterColumne].rename(columns=renameColumns)
    # 选取要用的列。
    df = df[SelectedColumne].copy()
    # 剔除范围之外的坐标。
    # 在没有剔除范围之外的坐标时，会计算为负值的grid。
    # 注意这里计算的是地域特征，也就是说不能存在负值的。
    # 可以存在负值，也就是说明这个地方在区域之外，但是有特征。最重要的是负数表明了一种语义。
    df = clean_outofbounds(df, bounds = GeoParameters, col = ['longitude', 'latitude'])

    # 将特征由中文全部转化为数值。
    df['category'] = df['category'].map(CategoryMapNumber)
    # 生成区域ID。
    _, _, df['gridID'] = GPS_to_grid(df['longitude'],df['latitude'], GeoParameters)
    # 选取最终进行聚合的列。
    df = df[['category', 'gridID']].copy()
    # print(df.head(3))
    # 创建一个空列，用于在生成透视表时存储值。
    df['temp'] = 0
    print(df.head(3))
    df = df.pivot_table(index='gridID',columns='category', values='temp', aggfunc='count').fillna(0)
    print(df.head(3))

    with lock:
        # 按列名拼接。也就是列名相同的会自动对应，缺少的列填空值。
        # 此时的index是gridID，后面还需要聚合操作的，所以不能忽略。
        gSharedData.dat = pd.concat([gSharedData.dat, df]).fillna(0.0)

def GetPoIFeature(PoIFolderPath='./Data/BeiJing/', 
                  PoIMatrixSavePath='./Data/Output/MultipleFeatures/PoIFeature.csv', 
                  Bounds=[115.7, 39.4, 117.4, 41.6],
                  renameColumns={'名称':'name','大类':'category','中类':'class', '小类':'type',
                                 '省':'province', '市':'city', '区':'district', 'WGS84_经度':'longitude', 'WGS84_纬度':'latitude'},
                  FileterColumne=['名称', '大类', '中类', '小类', '省', '市', '区', 'WGS84_经度', 'WGS84_纬度'],
                  SelectedColumne=['category', 'longitude', 'latitude'],
                  CategoryMapNumber={'餐饮服务':0, '商务住宅':1, '公共设施':2, '公司企业':3, '风景名胜':4, 
                                     '金融保险服务':5, '政府机构及社会团体':6, '医疗保健服务':7, '生活服务':8, 
                                     '餐饮服务':9, '科教文化服务':10, '购物服务':11, '体育休闲服务':12, '交通设施服务':13}):

    """_summary_
    通过文件获取PoI的特征。
    Args:
        PoIFolderPath (str, optional): PoI文件夹的路径. Defaults to './Data/BeiJing/'.
        PoIMatrixSavePath (str, optional): 保存PoI特征的路径及文件名. Defaults to './Data/Output/PoIFeature.csv'.
        Bounds (list, optional): 传入的区域边界. Defaults to [115.7, 39.4, 117.4, 41.6].
        renameColumns (dict, optional): 对于中文而言，需要修改为英文. Defaults to {'名称':'name','大类':'category','中类':'class', '小类':'type',
                                 '省':'province', '市':'city', '区':'district', 'WGS84_经度':'longitude', 'WGS84_纬度':'latitude'}.
        FileterColumne (list, optional): 选择有用的列，对于不用的列丢弃. Defaults to ['名称', '大类', '中类', '小类', '省', 
                '市', '区', 'WGS84_经度', 'WGS84_纬度'].
        SelectedColumne (list, optional): 生成特征的时候可能需要多种类型的特征，不仅仅是经纬度特征。
                在使用语言模型的时候也需要描述性特征可以描述跨区域的特征，所以这里要进行选择. Defaults to ['category', 'longitude', 'latitude'].
                也就是在必要的时候需要所有的列['name', 'category', 'class','type','province', 'city', 'district','longitude', 'latitude']。
                目前只选择了3列。
        CategoryMapNumber (dict, optional): 中文类别需要映射为数字. Defaults to {'餐饮服务':0, '商务住宅':1, '公共设施':2, '公司企业':3, '风景名胜':4, 
                                     '金融保险服务':5, '政府机构及社会团体':6, '医疗保健服务':7, '生活服务':8, 
                                     '餐饮服务':9, '科教文化服务':10, '购物服务':11, '体育休闲服务':12, '交通设施服务':13}.
    
        
    Returns:
        _type_: _description_
    """
    startTime = PrintStartInfo(functionName='GetPoIFeature()')
    # 检测POI特征的路径是否存在。不存在则返回。
    if os.path.exists(PoIFolderPath) ==False:
        print('{} is not exist.'.format(PoIFolderPath))
        return None

    AllFilesName = os.listdir(PoIFolderPath)
    # selected_columns = ['名称', '大类', '中类', '小类', '省', '市', '区', 'WGS84_经度', 'WGS84_纬度']
    
    gMultiProcessingPool = multiprocessing.Pool()
    gMultiProcessingManager = multiprocessing.Manager()
    gMultiProcessinglock = gMultiProcessingManager.Lock()
    gSharedData = gMultiProcessingManager.Namespace()
    
    # 文件相关参数。
    fileParameters = {'renameColumns':renameColumns, 'FileterColumne':FileterColumne, 'SelectedColumne':SelectedColumne,
                      'CategoryMapNumber':CategoryMapNumber}
    # 地理特征参数。
    # GeoParameters = area_to_params(gBounds, accuracy = 1000, method='rect')
    
    maxloncol = gGeoParameters['maxloncol']
    maxlatcol = gGeoParameters['maxlatcol']
    
    # 通过类别生成列名。
    columnName = list(CategoryMapNumber.values())
    gSharedData.dat = pd.DataFrame(columns=columnName)

    for fn in AllFilesName:
        FilePath = (PoIFolderPath + "{}").format(fn)
        # 多进程处理。
        gMultiProcessingPool.apply_async(GeneratePoIFeature, 
                                         args=(FilePath, fileParameters, gGeoParameters, gSharedData, gMultiProcessinglock))
    
    gMultiProcessingPool.close()
    gMultiProcessingPool.join()
    
    # 如果存在重复的index，那么将其按行相加合并。
    gSharedData.dat = gSharedData.dat.groupby(level=0).sum()

    # # 创建包含所有grid和特征的dataframe。
    # RegionFeature = pd.DataFrame()

    # 如果PoI特征文件已经存在，那么发出提示，并且之后将会覆盖。
    if os.path.exists(PoIMatrixSavePath) == True:
        print('{} is exist, will overwrite.'.format(PoIMatrixSavePath))

    gSharedData.dat.to_csv(PoIMatrixSavePath)
    PrintEndInfo(functionName='GetPoIFeature()', startTime=startTime)


# --- 读取轨迹数据 ---

def GetSingleUserTrajectory(user, samplingIntervalRow=0, 
                            FolderPath = "../Data/Geolife Trajectories 1.3/Data/"):
    """_summary_
    从原始文件中获取单个用户的轨迹数据。
    Args:
        user (int): 用户编号。也就是Trajectories文件中用户文件夹的名字。
        samplingIntervalRow (int, optional): 
            参考中认为“每隔1-5秒记录一次数据，这种情况太频繁了。将它减少到每分钟”。目前不这样处理。
            使用原始数据的间隔. Defaults to 0.
        FolderPath (str, optional): 
            默认轨迹文件存储的路径. Defaults to "../Data/Geolife Trajectories 1.3/Data/".

    Returns:
        Pandas.DataFrame: 单个用户的所有时间上的轨迹数据集合。
    """
    userdata = FolderPath + '/{}/Trajectory/'.format(user)

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
    
    if samplingIntervalRow != 0:
        # 每隔1~5秒记录一次数据，这种情况太频繁了。将它减少到每分钟
        df_sampling = df.iloc[::samplingIntervalRow, :] #每隔12行取一次
        df_sampling.head(5)  #查看前5行
    else:
        # 如果不进行抽样的动作，那么直接复制。
        df_sampling = df.copy()
    
    # df.shape()：
    print ('Total GPS points: ' + str(df_sampling.shape[0]))  
    return df_sampling

def GetEntireTime(df):
    # 先拼成完整的时间。
    df['entireTime'] = \
        pd.Timestamp(datetime.datetime.strptime((df['date'] + ' ' + df['time']),'%Y-%m-%d %H:%M:%S'))
    return df

# --- 轨迹预处理 ---

def ProcessSingleUserTrajectory(user):
    """_summary_
    对单个用户的轨迹信息进行处理。
    主要完成2个操作：1. 将时间特征各自单独分离出来；2. 将经纬度和区域ID对应起来。
    Args:
        SingleUserTrajectory (DataFrame): 输入单个用户的轨迹信息。
        user (_type_): _description_
        OutputProecessedTrajectory (_type_): _description_
    """

    SingleUserTrajectory = pd.read_csv(gInputTrajectoryCsvSavePath.format(user))
    # SingleUserTrajectory_pd = pd.read_csv(InputTrajectoryCsvSavePath.format(user))
    # # 如果不存在，那么重新读取。
    # if os.path.exists(InputTrajectoryCsvSavePath.format(user))==False:

    #     SingleUserTrajectory_pd = GetSingleUserTrajectory(user)
    #     SingleUserTrajectory_pd['index'] = SingleUserTrajectory_pd.index
    #     # 将所有用户的轨迹转换为CSV之后缓存下来。
    #     SingleUserTrajectory_pd.to_csv(InputTrajectoryCsvSavePath.format(user))
    # else:
    #     SingleUserTrajectory_pd = pd.read_csv(InputTrajectoryCsvSavePath.format(user))

    # 首先把数据中需要的列都做出来。
    SingleUserTrajectory = SingleUserTrajectory.apply(GetEntireTime, axis=1)
    SingleUserTrajectory['weekofyear'] = SingleUserTrajectory['entireTime'].dt.weekofyear
    # 一周中的星期几。
    SingleUserTrajectory['dayofweek'] = SingleUserTrajectory['entireTime'].dt.dayofweek
    # 一年中的第几天。
    SingleUserTrajectory['dayofyear'] = SingleUserTrajectory['entireTime'].dt.dayofyear
    # 一年中的第几个季度。
    SingleUserTrajectory['quarter'] = SingleUserTrajectory['entireTime'].dt.quarter
    # SingleUserTrajectory_pd['weekday_name'] = SingleUserTrajectory_pd['entireTime'].dt.weekday_name
    # 一年中的第几个月。
    SingleUserTrajectory['month'] = SingleUserTrajectory['entireTime'].dt.month
    # 第几年。这个没有必要。
    # SingleUserTrajectory_pd['year'] = SingleUserTrajectory_pd['entireTime'].dt.year
    # 一天中的第几个小时。
    SingleUserTrajectory['hour'] = SingleUserTrajectory['entireTime'].dt.hour
    SingleUserTrajectory['halfhour'] = SingleUserTrajectory['entireTime'].dt.floor(freq='30Min')
    SingleUserTrajectory.rename(columns={'lat': 'latitude', 'lng': 'longitude'}, inplace=True)

    # 生成区域ID。
    _, _, SingleUserTrajectory['gridID'] = GPS_to_grid(SingleUserTrajectory['longitude'],SingleUserTrajectory['latitude'], gGeoParameters)

    # # 然后把数据中的坐标对应为区域ID。
    # SingleUserTrajectory = SingleUserTrajectory.apply(CalculateNodeIDFromLatLong, latitudeRangeList=latitudeRangeList, 
    #                         longitudeRangeList=longitudeRangeList, totalColumn=totalColumn, axis=1)
    SingleUserTrajectory.to_csv(gOutputProecessedTrajectory.format(user))
    return SingleUserTrajectory

def PreprocessTrajectory(userRange, 
                         outputType,
                         userList=[], 
                         InputTrajectoryCsvSavePath = '../Data/output/Trajectories/{}.csv', 
                         savePath='../Data/output/',
                         TrajectoriesBasePath = '../Data/Geolife Trajectories 1.3/Data/'):
    """_summary_

    Args:
        userRange (string): 只有3个值可供选择：single, multi, all。
                        当range为all时，不需要用到userList。直接从TrajectoriesBasePath目录下读取所有的user轨迹。
        userList (list): 需要读取的用户列表。需要和range配合使用，如果只读取一个用户的，那么userList中只有一个元素。
                        如果读取多个用户的，那么userList中会有多个用户。
                        如果读取全部用户的，那么userList中会有所有用户的ID。
        savePath (str, optional): 生成的csv文件的保存路径. Defaults to '../Data/output/'.
        TrajectoriesBasePath (str, optional): 读取输入的用户轨迹目录. Defaults to '../Data/Geolife Trajectories 1.3/Data/'.
    """
    saveLcoation = ''
    if userRange == 'all':
        userList = next(os.walk(TrajectoriesBasePath))[1]
        saveLcoation = (savePath + 'Trajectory_{}.csv').format(userRange)
    elif userRange == 'multi':
        if len(userList) == 0:
            print('ERROR, userRange {}, input userlist is NULL.'.format(userRange))
            return
        saveLcoation = (savePath + 'Trajectory_{}.csv').format(userRange)
    elif userRange == 'single':
        if len(userList) == 0:
            print('ERROR, userRange {}, input userlist is NULL.'.format(userRange))
            return
        # user = userList[0]
        saveLcoation = (savePath + 'Trajectory_{}_{}.csv').format(userRange, userList[0])

    if outputType == 'independent':

        ProcessPool = multiprocessing.Pool()
        result = ProcessPool.map(ProcessSingleUserTrajectory, userList)

        # for user in userList:
        #     # 首先进行声明。
        #     SingleUserTrajectory_pd = pd.DataFrame()
        #     # 前面是否已经将轨迹转换为了CSV格式。如果没有转换，那么重新转换一次。如果已经转换了，那么就不再转换。
        #     if os.path.exists(InputTrajectoryCsvSavePath.format(user))==False:
        #         SingleUserTrajectory_pd = GetSingleUserTrajectory(user)
        #         SingleUserTrajectory_pd['index'] = SingleUserTrajectory_pd.index
        #         # 将所有用户的轨迹转换为CSV之后缓存下来。
        #         SingleUserTrajectory_pd.to_csv(InputTrajectoryCsvSavePath.format(user))
        #     else:
        #         SingleUserTrajectory_pd = pd.read_csv(InputTrajectoryCsvSavePath.format(user))

        pass
    elif outputType == 'merged':
        startTime = PrintStartInfo(functionName='PreprocessTrajectory')
        i = 0
        MultiTrajectorys_pd = None
        for user in userList:
            # print(user)
            SingleUserTrajectory_pd = GetSingleUserTrajectory(user)
            SingleUserTrajectory_pd['userID'] = user

            if i == 0:
                MultiTrajectorys_pd = SingleUserTrajectory_pd.copy()
            else:
                MultiTrajectorys_pd = pd.concat([MultiTrajectorys_pd, SingleUserTrajectory_pd])
                # print(MultiTrajectorys_pd.shape)
            i += 1
        # print('get time.')
        # (MultiTrajectorys_pd['date'] + ' ' + MultiTrajectorys_pd['time']),'%Y-%m-%d %H:%M:%S'
        MultiTrajectorys_pd['entireTime'] = pd.to_datetime((MultiTrajectorys_pd['date'] + ' ' + MultiTrajectorys_pd['time']), format='%Y-%m-%d %H:%M:%S')
        # MultiTrajectorys_pd = MultiTrajectorys_pd.apply(GetEntireTime, axis=1)
        MultiTrajectorys_pd = MultiTrajectorys_pd.drop(labels=['date', 'time'], axis=1)
        # print('save dataframe.')
        MultiTrajectorys_pd.to_csv(saveLcoation)
        PrintEndInfo(functionName='PreprocessTrajectory', startTime=startTime)
        return MultiTrajectorys_pd
    



# --- 合并特征 ---

def CombineRegionFeatures(FeaturesFolderPath='./Data/Output/MultipleFeatures/', 
                          FeatureSavePath='./Data/Output/Feature.csv'):
    pass

# --- 将特征附着到轨迹上 ---

from enum import Enum

class OutputType(Enum):
    # 每个用户各自存储各自的轨迹特征文件。
    DesperateTrajectory = 0
    # 所有用户的轨迹和成为一个文件。
    CombineTrajectory = 1

    # 将所有用户的轨迹融合成为一个矩阵的文件。
    # 这个需要很多参数。
    TrajectoryMatrix = 2
    # 输入用户和地域的交互矩阵。
    InteractionMatrix = 3



def attachFeaturetoTrajectory(featurePath='', trajectoryFolderPath='', outputType=''):
    """_summary_

    Args:
        featurePath (str, optional): _description_. Defaults to ''.
        trajectoryFolderPath (str, optional): _description_. Defaults to ''.
        outputType (str, optional): 输出附着了特征的轨迹数据. Defaults to ''.
    """
    pass