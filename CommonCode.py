import os
import math
import datetime
import time
import polars as pl
import pandas as pd
import logging
import json
import transbigdata as tbd

## 小工具

def findAllFile(base):
    for root, ds, fs in os.walk(base):
        for f in fs:
            fullname = os.path.join(root, f)
            yield fullname, root

def AddStringIncolumn(df, columnName, content):
    df[columnName] = '{}{}'.format(content, df[columnName])
    return df

def PrintStartInfo(functionName, description=''):
    startTime = datetime.datetime.now()
    logging.INFO("Start {} {} pid:{} ,start at:{}".format(functionName, description, os.getpid(), startTime.strftime('%Y-%m-%d %H:%M:%S')))
    return startTime

def PrintEndInfo(functionName, startTime, description=''):
    logging.INFO("End {} {} pid:{} ,completed at:{}, consume time: {}".format(functionName, description, os.getpid(),
                                     datetime.datetime.now(), 
                                     datetime.datetime.now() - startTime))

def PrintStartDebug(functionName, description=''):
    startTime = datetime.datetime.now()
    logging.DEBUG("Start {} {} pid:{} ,start at:{}".format(functionName, description, os.getpid(), startTime.strftime('%Y-%m-%d %H:%M:%S')))
    return startTime

def PrintEndDebug(functionName, startTime, description=''):
    logging.DEBUG("End {} {} pid:{} ,completed at:{}, consume time: {}".format(functionName, description, os.getpid(),
                                     datetime.datetime.now(), 
                                     datetime.datetime.now() - startTime))


class JSONConfig:
    """_summary_
    对在parameters.json中存储的全局变量进行操作。
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self._load_json()

    def _load_json(self):
        """加载 JSON 文件"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save(self):
        """保存数据到 JSON 文件"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get(self, key, default=None):
        """获取 JSON 变量"""
        return self.data.get(key, default)

    def set(self, key, value):
        """设置 JSON 变量并保存"""
        self.data[key] = value
        self.save()

    def delete(self, key):
        """删除 JSON 变量并保存"""
        if key in self.data:
            del self.data[key]
            self.save()

def CantorPairingFunction(x, y):
    """_summary_
    先对x,y使用折叠函数，然后再计算2个数的cantor配对函数的值。
    Args:
        x (int): 整数。
        y (int): 整数。

    Returns:
        int: 返回cantor配对数。
    """
    if x >= 0:
        x = 2 * x
    else:
        x = 2 * abs(x) - 1
    
    if y >= 0:
        y = 2 * y
    else:
        y = 2 * abs(y) - 1

    return ((x + y) * (x + y + 1) // 2 + y)

def CantorPairingInverseFunction(z):
    """_summary_
    先计算cantor配对函数反函数，然后x,y使用折叠反函数。
    Args:
        z (int): 两个数的cantor配对数值。

    Returns:
        x (int): 整数。
        y (int): 整数。
    """
    if z < 0 :
        print('CantorPairingInverseFunction input z is out of range.')
        return 0, 0
    
    w = (math.sqrt(8 * z + 1) - 1) // 2
    t = w * (w + 1) // 2
    y = z - t
    x = w - y
    
    if x % 2 == 0:
        x = x / 2
    else:
        x = -((x + 1) / 2)
    
    if y % 2 == 0:
        y = y / 2
    else:
        y = -((y + 1) / 2)

    return int(x), int(y)

def GenerateGrid(df, lonColName='loncol', latColName='latcol'):
    """_summary_
    将 康托 配对函数应用到dataframe上，生成grid。
    Args:
        df (pandas.DataFrame): _description_

    Returns:
        pandas.DataFrame: _description_
    """
    df['grid'] = CantorPairingFunction(df[lonColName], df[latColName])
    return df

def RecoverLoncolLatcol(df):
    """_summary_
    将 康托 配对函数的反函数应用到dataframe上，生成行号和列号。
    Args:
        df (pandas.DataFrame): _description_

    Returns:
        pandas.DataFrame: _description_
    """
    df['loncol'], df['latcol']= CantorPairingInverseFunction(df['grid'])
    return df

def CantorPairingFunctionInPolars(row):
    """_summary_
    使用polars来实现康托尔函数。
    Args:
        row (_type_): _description_

    Returns:
        _type_: _description_
    """
    if row['loncol'] >= 0:
        x = 2 * row['loncol']
    else:
        x = 2 * abs(row['loncol']) - 1
    
    if row['latcol'] >= 0:
        y = 2 * row['latcol']
    else:
        y = 2 * abs(row['latcol']) - 1

    return ((x + y) * (x + y + 1) // 2 + y)


def CantorPairingInverseFunctionInPolars(row):
    """_summary_
    使用polars来实现康托尔函数的反函数。注意返回的值是2行。
    Args:
        row (_type_): _description_

    Returns:
        _type_: _description_
    """
    z = row['grid']
    if z < 0 :
        print('CantorPairingInverseFunction input z is out of range.')
        return 0, 0
    
    w = (math.sqrt(8 * z + 1) - 1) // 2
    t = w * (w + 1) // 2
    y = z - t
    x = w - y
    
    if x % 2 == 0:
        x = x / 2
    else:
        x = -((x + 1) / 2)
    
    if y % 2 == 0:
        y = y / 2
    else:
        y = -((y + 1) / 2)

    return {'loncol':int(x), 'latcol':int(y)}

def GenerateGridInPolars(df, lonColName='loncol', latColName='latcol'):
    """_summary_
    将 康托 配对函数应用到dataframe上，生成grid。
    Args:
        df (polars.DataFrame): _description_

    Returns:
        polars.DataFrame: _description_
    """
    df = df.with_columns(
        pl.struct([lonColName, latColName]).map_elements(CantorPairingFunctionInPolars, return_dtype=pl.Int64).alias("grid")
    )
    return df

def RecoverLoncolLatcolInPolars(df):
    """_summary_
    将 康托 配对函数的反函数应用到dataframe上，生成行号和列号。
    Args:
        df (polars.DataFrame): _description_

    Returns:
        polars.DataFrame: _description_
    """
    df = df.with_columns(
        pl.struct(["grid"])
        .map_elements(CantorPairingInverseFunction, return_dtype=pl.Struct({"loncol": pl.Int64, "latcol": pl.Int64}))
        .alias("new_columns")
    )
    df = df.unnest("new_columns")
    return df


def MeasureTime(task_name, func, *args, **kwargs):
    """_summary_
    用于计算任务运行的时间。
    Args:
        task_name (_type_): _description_
        func (_type_): _description_

    Returns:
        _type_: _description_
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    elapsed_time = time.time() - start_time
    logging.INFO(f"{task_name} consume time: {elapsed_time:.2f} s.")
    return result


class JSONConfig:
    """_summary_
    对在parameters.json中存储的全局变量进行操作。
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self._load_json()

    def _load_json(self):
        """加载 JSON 文件"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save(self):
        """保存数据到 JSON 文件"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get(self, key, default=None):
        """获取 JSON 变量"""
        return self.data.get(key, default)

    def set(self, key, value):
        """设置 JSON 变量并保存"""
        self.data[key] = value
        self.save()

    def delete(self, key):
        """删除 JSON 变量并保存"""
        if key in self.data:
            del self.data[key]
            self.save()
            
def GenerateAllGridMapping(Bounds, 
                           mappingColumnName = 'grid_mapping',
                           mappingSavePath='./Data/Output/all_grid_mapping.csv'):
    """_summary_
    按照地图信息将所有区域grid映射到一个合理范围。
    Args:
        Bounds (_type_): transbigdata 所需的区域范围参数。
        mappingColumnName (str, optional): 映射生成列的列名. Defaults to 'grid_mapping'.
        mappingSavePath (str, optional): 映射保存路径. Defaults to './Data/Output/all_grid_mapping.csv'.

    Returns:
        _type_: _description_
    """
    GeoParameters = tbd.area_to_params(Bounds, accuracy = 1000, method='rect')
    n_lon = int((Bounds[2] - Bounds[0]) / GeoParameters['deltalon'])
    n_lat = int((Bounds[3] - Bounds[1]) / GeoParameters['deltalat'])

    # 获取所有栅格编号 [LONCOL, LATCOL]
    loncols = list(range(n_lon))
    latcols = list(range(n_lat))
    # 生成所有loncol , latcol。
    all_grid_df = pd.DataFrame([[lon, lat] for lon in loncols for lat in latcols], columns=['loncol', 'latcol'])
    # 生成grid。
    all_grid_df = all_grid_df.apply(GenerateGrid , lonColName='loncol', latColName='latcol', axis=1)

    GridColumnData = pd.DataFrame(all_grid_df.loc[:, 'grid'])
    # 生成列名。这一步不能删除，没有添加列名，就是一个series，后面就无法重新排序了。
    GridColumnData.columns = ['grid']
    # 去重之后共计9396个区域，数量没有变化。
    Grid_duplicated = GridColumnData.drop_duplicates()
    # 重新排序。查看前10个样本，感觉实际也没有做任何操作。可能已经排过序了。
    Grid_duplicated = Grid_duplicated.sort_values(by='grid', ascending=True)
    # 重置Index。
    Grid_duplicated = Grid_duplicated.reset_index(drop=True)
    # 将index 定义为新的映射列名。
    Grid_duplicated[mappingColumnName] = Grid_duplicated.index
    # 将映射全部加1，因为需要将0作为异常值赋值给未知区域对应的映射。
    # 将0作为异常值赋值给未知区域对应的映射的这个步骤在ReadDataTransformtoTensor()函数中完成。
    Grid_duplicated[mappingColumnName] += 1
    # 保留对应关系。将所有去重之后的已有停留点的包含grid的dataframe保留下来。
    Grid_duplicated.to_csv(mappingSavePath)
    return Grid_duplicated

