
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
    longitude, latitude, and the grids parameter. The output is the grid ID.

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
    longitude, latitude, and the grids parameter. The output is the grid ID.

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



# ------------------------------------------------------------------


def SampleTrajectory(user, samplingIntervalRow=0, FolderPath = "./Data/Geolife Trajectories 1.3/Data/"):
    """_summary_
    对轨迹数据进行采样。

    可以根据

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
