import os
import math
import datetime
import polars as pl

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
    print('Start function: {} ,pid: {} ,start at: {} .'.
          format(functionName, os.getpid(), startTime.strftime('%Y-%m-%d %H:%M:%S')))
    if description != '':
        print(description)
    return startTime

def PrintEndInfo(functionName, startTime, description=''):
    print('End function: {} ,pid: {} ,completed time: {} ,\n  \
          consume time: {} .'.format(functionName, os.getpid(),
                                     datetime.datetime.now(), 
                                     datetime.datetime.now() - startTime))
    if description != '':
        print(description)

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