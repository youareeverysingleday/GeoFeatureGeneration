import pandas as pd
import numpy as np
import transbigdata as tbd
import os
import math
import multiprocessing
import json
import datetime

import CommonCode as cc
import time

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
    

def GenerateSinglePekingUniversityPoIFeature(FilePath, fileParameters, GeoParameters, gSharedData, lock):
    """_summary_
    对北京大学开源的PoI数据类别进行处理，生成PoI特征。使用multiprocessing进行处理。
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
    df = tbd.clean_outofbounds(df, bounds = gBounds, col = ['longitude', 'latitude'])
    # print('2')
    # 将特征由中文全部转化为数值。
    df['category'] = df['category'].map(CategoryMapNumber)
    # 生成区域ID。
    df['loncol'], df['latcol'] = tbd.GPS_to_grid(df['longitude'],df['latitude'], GeoParameters)
    df = df.apply(cc.GenerateGrid, axis=1)
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
        # 按列名拼接。也就是列名相同的会自动对应，缺少的列填0值。
        # 此时的index是grid，后面还需要聚合操作的，所以不能忽略。
        gSharedData.dat = pd.concat([gSharedData.dat, df]).fillna(0.0)

def GetAddress(df, geolocator):
    # 由于获取经纬度对应的地址需要通过互联网访问，可能API受到了限制，所以需要单独进行处理。
    try:
        # 获取地址。
        location = geolocator.reverse(f"{df['latitude']}, {df['longitude']}")
        df['address'] = location.address
    except:
        df['address'] = 'networkerror'
        print('grid {} network error.'.format(df.name))
        time.sleep(1)
    return df

def GenerateAddressEmbedding(df, model, vectorLength=512):

    if df['address'] == 'networkerror':
        embedding = pd.Series(data=[0]*vectorLength)
    else:
        embedding = model.encode(df['address'])
        embedding = pd.Series(embedding)
        df = pd.concat([df, embedding], axis=0)

        return df

def GetLongitudeLatitude(df, GeoParameters):
    """_summary_
    生成经纬度。
    Args:
        df (_type_): _description_

    Returns:
        _type_: _description_
    """

    loncol, latcol = CantorPairingInverseFunction(df.name)
    longitude, latitude = tbd.grid_to_centre([loncol, latcol], GeoParameters)
    df['longitude'] = longitude
    df['latitude'] = latitude

    return df

def GetPekingUniversityPoIFeature():
    """_summary_
    生成PoI特征。
    Returns:
        _type_: _description_
    """
    startTime = cc.PrintStartInfo(functionName='GetSocialPoIFeature()')
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
        
    # maxloncol = gGeoParameters['maxloncol']
    # maxlatcol = gGeoParameters['maxlatcol']
    
    # 通过类别生成列名。
    columnName = list(gCategoryMapNumber.values())
    gSharedData.dat = pd.DataFrame(columns=columnName)

    for fn in AllFilesName:
        FilePath = (gPoIFolderPath + "{}").format(fn)
        # 多进程处理。
        gMultiProcessingPool.apply_async(GenerateSinglePekingUniversityPoIFeature, 
                                         args=(FilePath, fileParameters, gGeoParameters, gSharedData, gMultiProcessinglock))
    
    gMultiProcessingPool.close()
    gMultiProcessingPool.join()
    
    # 如果存在重复的index，那么将其按行相加合并。
    gSharedData.dat = gSharedData.dat.groupby(level=0).sum()

    # # 创建包含所有grid和特征的dataframe。
    # RegionFeature = pd.DataFrame()

    # 如果PoI特征文件已经存在，那么发出提示，并且之后将会覆盖。
    if os.path.exists(gPoISocialFeatureSavePath) == True:
        print('{} is exist, will overwrite.'.format(gPoISocialFeatureSavePath))
    
    # 将这部分PoI特征复制一份并返回。
    partofPoIFeature = gSharedData.dat.copy()

    # print('partofPoIFeature index {} , cols {}'.format(partofPoIFeature.index, partofPoIFeature.columns))
    

    # --------------------这里添加从poi数据中获取的特征。-----------------------
    # 添加地址嵌入向量和经纬度。
    """_summary_
    生成地址携带的特征。因为单纯的poi特征没有表明方位信息，也就是说在东面的一个商场和西面的一个商场在poi特征上是一样的。但是他们距离用户的真实地址是不一样的。
    同时地址表明了地理上人文属性，比如国家、省份等。
    另外顺便也要将经纬度信息放入特征中，因为经纬度从另一个方面表明了相对的距离信息。同时经纬度有它的缺陷，明显的经纬度0-180之间有个突然的转换。所以只能作为特征一种。

    步骤：
    1. 通过 grid 和 transbigdata 换算出格栅中心的经纬度。
    2. 通过 geopy 获得经纬度的地址。
    3. 通过 sentence_transformers 将地址向量化。
    4. 将经纬度和地址的向量化信息添加到poi特征中。
    """
    # 注意，partofPoIFeature 目前的列里面是没有grid列的。grid是作为index存在的。
    geolocator = Nominatim(user_agent="http")
    model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')

    # 注意，partofPoIFeature 目前的列里面是没有grid列的。grid是作为index存在的。
    partofPoIFeature = partofPoIFeature.apply(GetLongitudeLatitude, GeoParameters=gGeoParameters, 
                                              axis=1)
    
    partofPoIFeature = partofPoIFeature.apply(GetAddress, geolocator=geolocator, 
                                              axis=1)
    
    partofPoIFeature = partofPoIFeature.apply(GenerateAddressEmbedding, model=model, 
                                              axis=1)
    # -------------------------------------------

    # 保存。
    gSharedData.dat.to_csv(gPoISocialFeatureSavePath)
    
    cc.PrintEndInfo(functionName='GetSocialPoIFeature()', startTime=startTime)

    return partofPoIFeature

## 生成负面特征
def DropInforNegativePoI(FolderPath='./data/origin', sep='\|\+\+\|'):
    """_summary_
    去掉隐私数据处理。
    Args:
        FolderPath (str, optional): 数据文件存储文件夹. Defaults to './data/origin'.
        sep (str, optional): 分隔符. Defaults to '\|\+\+\|'.

    Returns:
        pandas.DataFrame: 返回脱敏之后的数据。
    """
    NegativeFeature = pd.DataFrame()
    for fullname, _ in cc.findAllFile(FolderPath):
        temp = pd.read_table(fullname, 
                            sep=sep, 
                            names=['ID', 'category', 'subcategory', 'longitude', 'latitude'], 
                            dtype={'ID':str, 'category':str, 'subcategory':str}, engine='python')
        NegativeFeature = pd.concat([NegativeFeature, temp], ignore_index=True)

    # print(NegativeFeature.shape)
    print('NegativeFeature memory usage is {} MB.'.format(NegativeFeature.memory_usage().sum()/(1024.0 ** 2)))
    # 按照ID去重。
    NegativeFeature.drop_duplicates(subset='ID', keep='first', inplace=True)
    # print(NegativeFeature.shape)
    # 将索引列替代为ID列。
    NegativeFeature.reset_index(inplace=True)
    # 删除原ID列和subcategory列。
    NegativeFeature.drop(labels=['ID', 'subcategory'], axis=1, inplace=True)
    NegativeFeature.rename(columns={'index':'ID'}, inplace=True)

    # 将category使用其他的值替代。生成类别替代的映射表。
    # t11 = pd.DataFrame(t1.groupby(by='category').groups.keys()).reset_index()
    CatrgoryMaping = pd.DataFrame(NegativeFeature.groupby(by='category').groups.keys()).reset_index()
    CatrgoryMaping.columns = ['icategory', 'category']
    # 保存一份对应关系表。
    CatrgoryMaping.to_csv('./data/categoryMaping.csv')

    # 将类别映射为新的类别。
    NegativeFeature = NegativeFeature.join(CatrgoryMaping.set_index('category'), on='category', 
                                        how='left', lsuffix='_left', rsuffix='_right')
    NegativeFeature.drop(labels=['category'], axis=1, inplace=True)
    # 原始数据(912974, 5)，在转换类型的过程中有2483个空值。直接删除空值。
    print(NegativeFeature['icategory'].isnull().sum())
    print(NegativeFeature.shape)
    NegativeFeature.dropna(inplace=True)
    # 删除经纬度中非数字的行。
    NegativeFeature['longitude'] = pd.to_numeric(NegativeFeature['longitude'], errors='coerce')
    NegativeFeature['latitude'] = pd.to_numeric(NegativeFeature['latitude'], errors='coerce')
    print(NegativeFeature.shape)

    # 将icategory的类型强制转化为int型。
    NegativeFeature['icategory'] = NegativeFeature['icategory'].astype(np.int16)
    NegativeFeature['longitude'] = NegativeFeature['longitude'].astype(np.float16)
    NegativeFeature['latitude'] = NegativeFeature['latitude'].astype(np.float16)

    # 重新定义一个category列，因为icategory是整型，不便于转化为字符串的同时赋值给原列。
    NegativeFeature['category'] = ''

    # 单纯的数字不适合做分类名称，所以前面加一个标识nf_。表示nagetive feature的意思。
    NegativeFeature = NegativeFeature.apply(cc.AddStringIncolumn, columnName='icategory', content='nf_', axis=1)
    NegativeFeature['category'] = NegativeFeature['icategory']
    NegativeFeature.drop(labels=['icategory'], axis=1, inplace=True)

    print(NegativeFeature.shape)
    # NegativeFeature.head(3)
    # "gPoIDropInforNegativelFeatureSavePath":"./Data/Output/Temp/DropInforNegativeFeature.csv",
    NegativeFeature.to_csv(gPoIDropInforNegativelFeatureSavePath)
    return NegativeFeature

# NegativeFeature = DropInforNegativeFeature(FolderPath='./data/origin', sep='\|\+\+\|')
# NegativeFeature.head(3)

def PreprocessNegativeFeature(FolderPath='./data/origin', sep='\|\+\+\|'):

    if os.path.exists(FolderPath) == False:
        print('Origin data of negative Feature  is not exist.')
        return None

    NegativeFeature = DropInforNegativePoI(FolderPath='./data/origin', sep='\|\+\+\|')
    NegativeFeature['loncol'], NegativeFeature['latcol'] = tbd.GPS_to_grid(NegativeFeature['longitude'], NegativeFeature['latitude'], gGeoParameters)
    NegativeFeature = NegativeFeature.apply(cc.GenerateGrid, axis=1)
    
    NegativeFeature = tbd.clean_outofbounds(NegativeFeature, bounds = gBounds, col = ['longitude', 'latitude'])

    print(NegativeFeature.shape)

    df = NegativeFeature[['category', 'grid']].copy()
    print(df.shape)
    df['temp'] = 0
    df = df.pivot_table(index='grid',columns='category', values='temp', aggfunc='count').fillna(0)
    print(df.shape)

    if os.path.exists(gPoINegativelFeatureSavePath) == True:
        print('{} is exist, will overwrite.'.format(gPoINegativelFeatureSavePath))

    df.to_csv(gPoINegativelFeatureSavePath)
    # df.sample(3)
    return df

## 合并所有的PoI特征

# 合并生成PoI特征。
def CombineMultiPoIFeatures(FeaturesFolderPath='./Data/Output/MultipleFeatures/', 
                          FeatureSavePath='./Data/Output/PoIFeature.csv',
                          OthersFeatureFlag = False):
    """_summary_
    目前只有2个PoI特征，将其合并之后保存。
    两个输入参数没有使用，而是通过全局变量从json文件中读取的。
    
    由于现在只有两种PoI特征数据，所以处理对于两种特征数据的处理比较原始。
    按道理应该对所有的PoI特征都遍历。
    Args:
        FeaturesFolderPath (str, optional): _description_. Defaults to './Data/Output/MultipleFeatures/'.
        FeatureSavePath (str, optional): _description_. Defaults to './Data/Output/PoIFeature.csv'.
        OthersFeatureFlag (bool, optional): 是否包含除了社会PoI之外的的特征数据。默认是没有. Defaults to False.
    """
    # 先获取北京大学提供的PoI特征。
    PartofPoIFeature = GetPekingUniversityPoIFeature()
    
    # 创建一个空的合并所有PoI特征的DataFrame。
    PoIFeature = pd.DataFrame()
    
    # 很多情况下有些特征是没有的。所以不需要进行下面if判断对应的步骤。
    if OthersFeatureFlag == True:
        NegativeFeature = pd.DataFrame()
        # 如果存在则直接读取。默认是存在的。
        if os.path.exists(gPoINegativelFeatureSavePath) == True:
            # 第一列是grid作为index列。
            NegativeFeature = pd.read_csv(gPoINegativelFeatureSavePath, index_col=0)
        else:
            NegativeFeature = PreprocessNegativeFeature()
        # 按区域编号进行拼接，也就是按行进行拼接。缺少的行填0。
        PoIFeature = pd.concat([NegativeFeature, PartofPoIFeature], axis=0).fillna(0.0)
    else:
        PoIFeature = PartofPoIFeature.copy()

    if os.path.exists(gPoIFeatureSavePath) == True:
        print('{} is exist, it will overwrite.'.format(gPoIFeatureSavePath))
    
    # print('\n Output PoI feature shape is {}. columns {}.\n'.format(PoIFeature.shape, PoIFeature.columns))
    PoIFeature.to_csv(gPoIFeatureSavePath)


def CombineFeatures(ExistPoIFeature, NewPoIFeature):
    
    PoIFeature = pd.DataFrame()
    PoIFeature = pd.concat([ExistPoIFeature, NewPoIFeature], axis=0).fillna(0.0)
    PoIFeature.to_csv(gPoIFeatureSavePath)


if __name__ == '__main__':
    startTime = datetime.datetime.now()
    GetParameters('./Parameters.json')
    # print(gfg.gGeoParameters)
    CombineMultiPoIFeatures(OthersFeatureFlag=False)
    endTime1 = datetime.datetime.now()
    print("GetPoIFeature completed. {}".format(endTime1 - startTime))