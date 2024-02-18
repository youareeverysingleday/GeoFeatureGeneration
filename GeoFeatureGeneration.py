
# Author: youareeverysingleday
# contact: 
# CreationTime: 2024/01/15 11:29
# software: VSCode
# LastEditTime: 
# LastEditors: youareeverysingleday
# Description: generate geographic feature.

# This package can not run in jupyter, because package has used "mulitprocessing".

# 使用了transbigdata中的部分对经纬度进行处理的代码。
# 由于最终的输出是需要输入机器学习模型的，所以对源码进行了修改再进行使用。

import pandas as pd
import numpy as np
import datetime
import time

import os
import sys
import math

import multiprocessing

import geopandas as gpd

import sklearn


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

    # 添加生成grid的代码.
    grid = loncol * maxloncol + latcol
    # print(loncol, latcol, maxloncol)
    return loncol, latcol, grid


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
        loncol, latcol, grid = GPS_to_grids_rect(lon, lat, params)
        return [loncol, latcol, grid]
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

def traj_stay_move(data, params,
                     col=['userID', 'dataTime', 'longitude', 'latitude', 'grid'],
                     activitytime=1800):
    '''
    Input trajectory data and gridding parameters, identify stay and move

    Parameters
    ----------------
    data : DataFrame
        trajectory data
    params : List
        gridding parameters
    col : List
        The column name, in the order of ['userID', 'dataTime', 
        'longitude', 'latitude', 'grid']
    activitytime : Number
        How much time to regard as activity

    Returns
    ----------------
    stay : DataFrame
        stay information
    move : DataFrame
        move information
    '''
    uid, timecol, lon, lat, grid = col
    # Identify stay
    data = data.sort_values(by=col[:2])
    stay = data.copy()
    stay = stay.rename(columns={lon: 'lon', lat: 'lat', timecol: 'stime'})
    stay['stime'] = pd.to_datetime(stay['stime'])
    # Number the status
    stay['status_id'] = ((stay['grid'] != stay['grid'].shift()) |
                         (stay[uid] != stay[uid].shift())).astype(int)
    stay.loc[stay[uid] != stay[uid].shift(-1),'status_id'] = 1

    stay['status_id'] = stay.groupby([uid])['status_id'].cumsum()
    stay = stay.drop_duplicates(
        subset=[uid, 'status_id'], keep='first').copy()

    stay['etime'] = stay['stime'].shift(-1)
    stay = stay[stay[uid] == stay[uid].shift(-1)].copy()
    # Remove the duration shorter than given activitytime
    stay['duration'] = (pd.to_datetime(stay['etime']) -
                        pd.to_datetime(stay['stime'])).dt.total_seconds()
    stay = stay[stay['duration'] >= activitytime].copy()
    stay = stay[[uid, 'stime', 'grid',
                 'etime', 'lon', 'lat', 'duration']]

    # Add the first and last two data points for each ID in the Stay dataset before conducting move detection, 
    # so that the movement patterns of individuals at the beginning and end of the study period can also be identified.
    first_data = data.drop_duplicates(subset=[uid],keep='first').copy()
    last_data = data.drop_duplicates(subset=[uid],keep='last').copy()
    first_data['stime'] = first_data[timecol]
    first_data['etime'] = first_data[timecol]
    first_data['duration'] = 0
    first_data['lon'] = first_data[lon]
    first_data['lat'] = first_data[lat]

    # first_data['LONCOL'], first_data['LATCOL'] = GPS_to_grid(
    #     first_data['lon'], first_data['lat'], params)
    # print('6')
    first_data = first_data[[uid, 'stime', 'grid',
                    'etime', 'lon', 'lat', 'duration']]

    last_data['stime'] = last_data[timecol]
    last_data['etime'] = last_data[timecol]
    last_data['duration'] = 0
    last_data['lon'] = last_data[lon]
    last_data['lat'] = last_data[lat]
    # last_data['LONCOL'], last_data['LATCOL'] = GPS_to_grid(
    #     last_data['lon'], last_data['lat'], params)
    last_data = last_data[[uid, 'stime', 'grid',
                    'etime', 'lon', 'lat', 'duration']]

    # Identify move
    move = pd.concat([first_data,stay,last_data],axis=0).sort_values(by=[uid,'stime'])

    move['stime_next'] = move['stime'].shift(-1)
    move['elon'] = move['lon'].shift(-1)
    move['elat'] = move['lat'].shift(-1)
    move['Egrid'] = move['grid'].shift(-1)
    # move['ELATCOL'] = move['LATCOL'].shift(-1)
    move[uid+'_next'] = move[uid].shift(-1)

    move = move[move[uid+'_next'] == move[uid]
                ].drop(['stime', 'duration', uid+'_next'], axis=1)
    move = move.rename(columns={'lon': 'slon',
                                'lat': 'slat',
                                'etime': 'stime',
                                'stime_next': 'etime',
                                'grid': 'Sgrid'
                                })
    move['duration'] = (
        move['etime'] - move['stime']).dt.total_seconds()
    
    move['moveid'] = range(len(move))
    stay['stayid'] = range(len(stay))

    return stay, move


def OneDayMatrix(stay, 
                 col=['stime', 'grid', 'duration'],
                 interval='D'):
    data = stay.copy()
    data['jtime'] = data['stime'].shift(-1)

    

    if interval == 'D':
        

        pass
    elif interval == 'W':
        pass
    elif interval == 'M':
        pass
    elif interval == 'Q':
        pass
    elif interval == 'Y':
        pass

    
    data['judageTime'] = data['stime'].shift(-1)
    
    pass




# --- 辅助函数 --

def PrintStartInfo(functionName, description=''):
    startTime = datetime.datetime.now()
    print('Start function: {} ,\n  pid: {} ,\n  start at: {} .'.
          format(functionName, os.getpid(), startTime.strftime('%Y-%m-%d %H:%M:%S')))
    if description != '':
        print(description)
    
    return startTime

def PrintEndInfo(functionName, startTime, description=''):
    print('End function: {} ,\n  pid: {} ,\n  completed time: {} ,\n  \
          consume time: {} .'.format(functionName, os.getpid(),
                                     datetime.datetime.now(), 
                                     datetime.datetime.now() - startTime))
    if description != '':
        print(description)

# --- 全局变量设置 ---

#地理特征边界。
gBounds = [115.7, 39.4, 117.4, 41.6]
# 所有的地理参数。
gGeoParameters = area_to_params(gBounds, accuracy = 1000, method='rect')

# PoI特征输入目录。PoI文件夹的路径.
gPoIFolderPath = './Data/BeiJing/'
# 保存PoI特征的路径及文件名. Defaults to './Data/Output/PoIFeature.csv'.
gPoIFeatureSavePath = './Data/Output/MultipleFeatures/PoIFeature.csv'
gRenameColumns = {'名称':'name','大类':'category','中类':'class', '小类':'type', 
                    '省':'province', '市':'city', '区':'district', 'WGS84_经度':'longitude', 'WGS84_纬度':'latitude'}
gFileterColumne = ['名称', '大类', '中类', '小类', '省', '市', '区', 'WGS84_经度', 'WGS84_纬度']
gSelectedColumne = ['category', 'longitude', 'latitude']
gCategoryMapNumber = {'住宿服务':0, '商务住宅':1, '公共设施':2, '公司企业':3, '风景名胜':4, 
                    '金融保险服务':5, '政府机构及社会团体':6, '医疗保健服务':7, '生活服务':8, 
                    '餐饮服务':9, '科教文化服务':10, '购物服务':11, '体育休闲服务':12, '交通设施服务':13}




# 轨迹数据的存储目录。
gTrajectoryFolderPath = "./Data/Geolife Trajectories 1.3/Data/"

gUserList = next(os.walk(gTrajectoryFolderPath))[1]
# InputTrajectoryCsvSavePath = './Data/Output/Trajectories/{}.csv'
# 单个用户的保存目录。
gOutputProecessedTrajectory='./Data/Output/ProcessedTrajectories/{}.csv'
# 所有用户的保存目录。
gInputTrajectoryCsvSavePath = './Data/Output/Trajectories/{}.csv'
# 保存的输出的根目录。
gOutpuyPath='./Data/Output/'
# TrajectoriesBasePath = './Data/Geolife Trajectories 1.3/Data/'
# 轨迹采样间隔。
gSamplingIntervalRow = 0
# 是否独立保存每个用户的轨迹。
gSaveUserTrajectoryFlag = False

# 在处理轨迹数据时，是否将所有范围之外的经纬度都删除。
# 1. 按照推荐系统的一般做法，会将没有出现在物品列表中的物品删除。
# 2. 而且在没有剔除范围外的地点时会产生大量编号为负数的grid。所以最后
# 考虑上述两个原因，先把范围之外的地点在最后生成轨迹特征时 GenerateInteractionMatrix() 删除。
gDeleteOutofBoundTrajectoryFlag = False
        

# --- 获取PoI特征 ---

def GeneratePoIFeature(FilePath, fileParameters, GeoParameters, gSharedData, lock):
    """_summary_
    对单个用户进行处理，生成PoI特征。使用multiprocessing进行处理。
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

    # print('Filepath {}'.format(FilePath))
    # 读取数据。
    df = pd.read_csv(FilePath, encoding='gb18030')
    
    # 将列名修改为英文。
    df = df[FileterColumne].rename(columns=renameColumns)
    # 选取要用的列。
    df = df[SelectedColumne].copy()
    # print('{}'.format(GeoParameters))
    # 剔除范围之外的坐标。
    # 在没有剔除范围之外的坐标时，会计算为负值的grid。
    # 注意这里计算的是地域特征，也就是说不能存在负值的。
    # 可以存在负值，也就是说明这个地方在区域之外，但是有特征。最重要的是负数表明了一种语义。
    # print('1')
    df = clean_outofbounds(df, bounds = gBounds, col = ['longitude', 'latitude'])
    # print('2')
    # 将特征由中文全部转化为数值。
    df['category'] = df['category'].map(CategoryMapNumber)
    # 生成区域ID。
    _, _, df['grid'] = GPS_to_grid(df['longitude'],df['latitude'], GeoParameters)
    # print('3')
    # 选取最终进行聚合的列。
    df = df[['category', 'grid']].copy()
    # print(df.head(3))
    # 创建一个空列，用于在生成透视表时存储值。
    df['temp'] = 0
    # print('4')
    # print(df.head(3))
    df = df.pivot_table(index='grid',columns='category', values='temp', aggfunc='count').fillna(0)
    # print(df.head(3))

    with lock:
        # 按列名拼接。也就是列名相同的会自动对应，缺少的列填空值。
        # 此时的index是grid，后面还需要聚合操作的，所以不能忽略。
        gSharedData.dat = pd.concat([gSharedData.dat, df]).fillna(0.0)

def GetPoIFeature():
    """_summary_
    生成PoI特征。
    Returns:
        _type_: _description_
    """
    startTime = PrintStartInfo(functionName='GetPoIFeature()')
    # 检测POI特征的路径是否存在。不存在则返回。
    if os.path.exists(gPoIFolderPath) ==False:
        print('{} is not exist.'.format(gPoIFolderPath))
        return None

    AllFilesName = os.listdir(gPoIFolderPath)
    # selected_columns = ['名称', '大类', '中类', '小类', '省', '市', '区', 'WGS84_经度', 'WGS84_纬度']
    
    gMultiProcessingPool = multiprocessing.Pool()
    gMultiProcessingManager = multiprocessing.Manager()
    gMultiProcessinglock = gMultiProcessingManager.Lock()
    gSharedData = gMultiProcessingManager.Namespace()
    
    # 文件相关参数。
    fileParameters = {'renameColumns':gRenameColumns, 'FileterColumne':gFileterColumne, 'SelectedColumne':gSelectedColumne,
                      'CategoryMapNumber':gCategoryMapNumber}
    # 地理特征参数。
    gGeoParameters = area_to_params(gBounds, accuracy = 1000, method='rect')
    
    maxloncol = gGeoParameters['maxloncol']
    maxlatcol = gGeoParameters['maxlatcol']
    
    # 通过类别生成列名。
    columnName = list(gCategoryMapNumber.values())
    gSharedData.dat = pd.DataFrame(columns=columnName)

    for fn in AllFilesName:
        FilePath = (gPoIFolderPath + "{}").format(fn)
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
    if os.path.exists(gPoIFeatureSavePath) == True:
        print('{} is exist, will overwrite.'.format(gPoIFeatureSavePath))
    
    gSharedData.dat.to_csv(gPoIFeatureSavePath)
    PrintEndInfo(functionName='GetPoIFeature()', startTime=startTime)


# --- 读取轨迹数据 ---


def GetEntireTime(df):
    # 先拼成完整的时间。
    df['entireTime'] = \
        pd.Timestamp(datetime.datetime.strptime((df['date'] + ' ' + df['time']),'%Y-%m-%d %H:%M:%S'))
    return df

def GenerateTimeFeature(df, col='entireTime'):
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
    # gTrajectoryFolderPath = "./Data/Geolife Trajectories 1.3/Data/"
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
    if gDeleteOutofBoundTrajectoryFlag == True:
        # Delete out of bounds .
        df = clean_outofbounds(df, bounds = gBounds, col = ['lng', 'lat'])
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
    print ('Total GPS points: ' + str(df_sampling.shape[0]))

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
    _, _, df_sampling['grid'] = GPS_to_grid(df_sampling['longitude'], df_sampling['latitude'], gGeoParameters)
    df_sampling['userID'] = user

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
    # gTrajectoryFolderPath = "./Data/Geolife Trajectories 1.3/Data/"
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
    if gDeleteOutofBoundTrajectoryFlag == True:
        # Delete out of bounds .
        df = clean_outofbounds(df, bounds = gBounds, col = ['lng', 'lat'])
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
    print ('Total GPS points: ' + str(df_sampling.shape[0]))

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
    _, _, df_sampling['grid'] = GPS_to_grid(df_sampling['longitude'], df_sampling['latitude'], gGeoParameters)
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
        saveLcoation = (gOutpuyPath + 'Trajectory_{}.csv').format(userRange)
    # 处理输入的多个用户的轨迹。
    elif userRange == 'multi':
        if len(userList) == 0:
            print('ERROR, userRange {}, input userlist is NULL.'.format(userRange))
            return
        saveLcoation = (gOutpuyPath + 'Trajectory_{}.csv').format(userRange)
    # 处理输入的单个用户的轨迹。
    elif userRange == 'single':
        if len(userList) == 0:
            print('ERROR, userRange {}, input userlist is NULL.'.format(userRange))
            return
        # user = userList[0]
        saveLcoation = (gOutpuyPath + 'Trajectory_{}_{}.csv').format(userRange, userList[0])

    # 每个用户输出各自处理好的轨迹数据。
    if outputType == 'independent':
        gSaveUserTrajectoryFlag = True

        ProcessPool = multiprocessing.Pool()
        result = ProcessPool.map(PreprocessSingleTrajectoryIndependent, userList)
    # 将所有用户的轨迹数据合并成为一个文件输出。
    elif outputType == 'merged':
        startTime = PrintStartInfo(functionName='PreprocessTrajectory')
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
        print('ProcessSharedData.dat shape {}'.format(ProcessSharedData.dat.shape))
        
        # 保存。
        ProcessSharedData.dat.to_csv(saveLcoation)
        PrintEndInfo(functionName='PreprocessTrajectory', startTime=startTime)
        # return MultiTrajectorys_pd

# --- 合并特征 ---

# 暂时外部特征只有PoI特征，后期还会有其他的特征需要处理。
def CombineRegionFeatures(FeaturesFolderPath='./Data/Output/MultipleFeatures/', 
                          FeatureSavePath='./Data/Output/Feature.csv'):
    pass

# --- 将特征附着到轨迹上 ---

# 单个用户轨迹附着了特征之后的保存路径。
gSingleUserTrajectoryFeaturePath = './Data/Output/TrajectoryFeature/{}.csv'
# 所有用户的轨迹附着了特征之后的保存路径。
gAllUsersTrajectoryFeaturePath = './Data/Output/usersTrajectory.csv'

# 所有合并之后的特征。
# gFeaturePath = './Data/Output/Feature.csv'
# 暂时只有PoI特征。所以直接指向PoI特征。
gFeaturePath = './Data/Output/MultipleFeatures/PoIFeature.csv'

def AttachFeaturetoSingleUserTrajectory(user):
    """_summary_
    将特征附着到单个用户的轨迹上。在multiprocessing中使用。
    Args:
        user (_type_): 用户ID。
    """
    PoIFeature = pd.read_csv(gFeaturePath, index_col=0)
    PoIFeature['grid'] = PoIFeature.index
    
    userTrajectory = pd.read_csv(gOutputProecessedTrajectory.format(user), index_col=0)

    userTrajectory = userTrajectory.merge(PoIFeature, 
                                          on='grid', how='left').fillna(0)

    userTrajectory.to_csv(gSingleUserTrajectoryFeaturePath.format(user))


def AttachFeaturetoTrajectory(outputType='merged'):
    """_summary_
    将特征附着到所有用户的轨迹上。
    Args:
        outputType (str, optional): _description_. Defaults to 'merged'.
    """
    startTime = PrintStartInfo(functionName='AttachFeaturetoTrajectory()')

    # 输出每个用户各自的附着了特征之后的轨迹。
    if outputType == 'independent':
        userList = gUserList
        ProcessPool = multiprocessing.Pool()
        ProcessPool.map(AttachFeaturetoSingleUserTrajectory, userList)
    # 输出所有用户附着了特征之后的轨迹为一个文件。
    elif outputType == 'merged':
        usersTrajectory = pd.read_csv(gOutpuyPath + 'Trajectory_all.csv', index_col=0)
        PoIFeature = pd.read_csv(gFeaturePath, index_col=0)
        # 将index列赋值给一个新的grid列。
        PoIFeature['grid'] = PoIFeature.index

        usersTrajectory = usersTrajectory.merge(PoIFeature, 
                                                on='grid', how='left').fillna(0)

        usersTrajectory.to_csv(gAllUsersTrajectoryFeaturePath)
    PrintEndInfo(functionName='AttachFeaturetoTrajectory()', startTime=startTime)

# --- 输出其他格式 ---

# 交互矩阵保存的路径。
gInteractionMatrixSavePath = './Data/Output/InteractionMatrix.csv'

def GenerateInteractionMatrix():
    """_summary_
    生成交互矩阵。
    """
    startTime = PrintStartInfo(functionName='GenerateInteractionMatrix()')
    Trajectories = pd.read_csv(gAllUsersTrajectoryFeaturePath, index_col=0)
    # 是否删除所有范围之外的地点。
    if gDeleteOutofBoundTrajectoryFlag == True:
        Trajectories = clean_outofbounds(Trajectories, gBounds, col=['longitude', 'latitude'])
    # 选择最终进行透视的列。'latitude'列只是作为最后 aggfunc='count' 的存在。
    Trajectories = Trajectories[['grid', 'userID', 'latitude']]
    InteractionMatrix = Trajectories.pivot_table(index='userID',columns='grid', 
                                                 values='latitude', aggfunc='count').fillna(0).copy()
    # 保存。
    InteractionMatrix.to_csv(gOutpuyPath + 'InteractionMatrix.csv')
    PrintEndInfo(functionName='GenerateInteractionMatrix()', startTime=startTime)

# 将numpy.narray的3维数据保存为csv格式。
def np_3d_to_csv(data, 
                 path, 
                 datatype='float'):
    import csv
    a2d = data.reshape(data.shape[0], -1)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(a2d)

# 从3维数据中读取numpy.narray格式。
def np_3d_read_csv(path='./Data/Output/StayMatrx/{}.csv',
                   shape=(-1, 128, 3),
                   datatype='float'):
    import csv
    # 从csv文件读取2D数组
    with open(path, "r") as f:
        reader = csv.reader(f)
        a2d = np.array(list(reader)).astype(datatype)

    # 将2D数组转换为3D数组
    a = a2d.reshape(shape)
    print(a.shape)

# 删除全为零的行。
def drop_all_0_rows(df):
    return df.drop(index=df[(df == 0).all(axis=1)].index)

# 生成特征矩阵时需要对所有的特征进行归一化。
from sklearn.preprocessing import MinMaxScaler
gStaySavePath = './Data/Output/Stay.csv'
gMoveSavePath = './Data/Output/Move.csv'

gSingleUserStaySavePath = './Data/Output/Stay/{}.csv'
gSingleUserMoveSavePath = './Data/Output/Move/{}.csv'

# import dask.dataframe as dd

def SeriesToMatrix(user, data, interval='M', maxrow=128):
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
    # print(stay.head(2))
    # print(stay.columns)
    # 获得时间戳。
    stay['stimestamp'] = stay['stime'].astype('int64') // 1e9
    # stay.head()

    stayGroup = stay.groupby(pd.Grouper(key='stime', freq=interval))
    # 创建一个空的result矩阵。
    result = np.empty((0, maxrow, stay.shape[1]))
    
    for g in stayGroup:
        # 取月份值。
        key = g[0].month
        # print(type(key))
        
        # 取所有特征量。
        # 之所以需要copy一次是因为
        df = g[1].copy()
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
    
    print(result.shape)
    if result.shape[0] == 0:
        # 178 user trajectory is 0.
        print('------{} shape is zero.'.format(user))
    else:
        # 保存。
        np_3d_to_csv(result, gSingleUserStayMatrixSavePath.format(user))

    print('{} SeriesToMatrix have completed.'.format(user))
    return result

def GenerateSingleUserStayMove(user):
    """_summary_
    生成单个用户的特征。在处理整个用户轨迹特征文件的时候非常耗时。所以推荐使用分别处理每个单个用户的轨迹特征。
    Args:
        user (_type_): _description_
    """
    # 读取轨迹。
    userTrajectory = pd.read_csv(gSingleUserTrajectoryFeaturePath.format(user), 
                                 index_col=0,
                                 parse_dates=['entireTime'])
    
    
    # 去掉范围之外的轨迹。
    if gDeleteOutofBoundTrajectoryFlag == True:
        userTrajectory = clean_outofbounds(userTrajectory, 
                                         gBounds, 
                                         col=['longitude', 'latitude'])
    
    # 生成时间特征。时间戳的特征也会在后面获取。
    userTrajectory = userTrajectory.apply(GenerateTimeFeature, axis=1)

    stay, move = traj_stay_move(userTrajectory, 
                                gGeoParameters,
                                col=['userID', 'entireTime', 'longitude', 'latitude'])

    stay.to_csv(gSingleUserStaySavePath.format(user))
    move.to_csv(gSingleUserMoveSavePath.format(user))

    print('{} feature has completed.'.format(user))

gSingleUserStayMatrixSavePath = './Data/Output/StayMatrix/{}.csv'


def GenerateStayMove(ProcessType = 'independent'):
    """_summary_
    生成特征矩阵。
    """
    startTime = PrintStartInfo('GenerateStayMove()')
    # 对每个用户单独进行处理。
    if ProcessType == 'independent':
        userList = gUserList
        ProcessPool = multiprocessing.Pool()
        ProcessPool.map(GenerateSingleUserStayMove, userList)
    # 处理所有用户整个处于一个csv中。效率比较低。推荐使用independent模式。
    elif ProcessType == 'merged':
        Trajectories = pd.read_csv(gAllUsersTrajectoryFeaturePath, 
                                index_col=0, parse_dates=['entireTime'])
        if gDeleteOutofBoundTrajectoryFlag == True:
            Trajectories = clean_outofbounds(Trajectories, gBounds, col=['longitude', 'latitude'])
        
        # 需要生成时间特征。
        Trajectories = Trajectories.apply(GenerateTimeFeature, axis=1)

        # 高度信息不能丢弃，也作为一种特征。
        # 需要判断停留点。
        # 需要的将地点的文字描述embedding之后也作为特征保存在特征矩阵中。
        
        # user stay and move to decide sentence length .
        stay, move = traj_stay_move(Trajectories, 
                                    gGeoParameters,
                                    col=['userID', 'entireTime', 'longitude', 'latitude'])

        stay.to_csv(gStaySavePath)
        move.to_csv(gMoveSavePath)

    PrintEndInfo('GenerateStayMove()', startTime=startTime)

def GenerateSingleUserFeatureMatrix(user):
    # 读取所有特征。
    PoIFeature = pd.read_csv(gFeaturePath, index_col=0)
    PoIFeature['grid'] = PoIFeature.index

    stay = pd.read_csv(gSingleUserStaySavePath.format(user), index_col=0)
    stay['stime'] = pd.to_datetime(stay['stime'])

    # 将通过PoI获得的特征以及其他特征和停留点特征合并。
    stay = stay.merge(PoIFeature, on='grid', how='left').fillna(0)

    SeriesToMatrix(user=user, data=stay, interval='M', maxrow=128)

def GenerateFeatureMatrix(ProcessType = 'independent'):
    startTime = PrintStartInfo('GenerateFeatureMatrix()')
    # 对每个用户单独进行处理。
    if ProcessType == 'independent':
        userList = gUserList
        ProcessPool = multiprocessing.Pool()
        ProcessPool.map(GenerateSingleUserFeatureMatrix, userList)
    elif ProcessType == 'merged':
        pass

    PrintEndInfo('GenerateFeatureMatrix()', startTime=startTime)

    