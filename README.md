# GeoFeatureGeneration

generate various geographic characteristic/feature from PoI or other origin.

This package can not run in jupyter, because package has used "mulitprocessing".

在处理基础数据时以 transbigdata 包中的内容作为基础。transbigdata 主要是对数据做了预处理，但是并没有将数据转化为可以输入模型的形式。同时 transbigdata 在处理时有些处理无法满足输入机器学习模型的要求，因此做出了改进。

这个包可以将数据处理为各种需要的格式输出。以满足多种模型对数据的需求。其中以统计型矩阵、类似于自然语言的矩阵和时序的形式为主。从而满足多种机器学习算法的需求。

| number | city           | Regional scope               | description                       |
| ------ | -------------- | ---------------------------- | --------------------------------- |
| 1      | 北京经纬度范围 | 115.7, 39.4, 117.4, 41.6     | 北京目前由北京大学提供的PoI数据 |
| 2      | 武汉经纬度范围 | 113.68, 29.97, 115.08, 31.37 | ......                            |

## publish information

| number | publish time | version | modify content                                                                                                            |
| ------ | ------------ | ------- | ------------------------------------------------------------------------------------------------------------------------- |
| 1      | 20240219     | 1.0.0   | can output matrix of trajectory.                                                                                          |
| 2      | 20240409     | 1.0.1   | output series of stay contain PoI feature.                                                                                |
| 3      | 20240625     | 1.0.2   | generate negative PoI feature of area.                                                                                    |
| 4      | 20241024     | 1.0.3   | because transbigdata package generate grid can't recover loncol and latcol, so use Cantor function to solve this problem. |
| 5  | 20241225   | 2.0.0  | separate the code of feature generate and feature attachment. when adding new feature, there is no need to rerun all code.                                                              |
|        |              |         |                                                                                                                           |
|        |              |         |                                                                                                                           |


## Function desrciption

the target is to process the data into a format that enters machine learning.

This package can concat multi vectorized features to one matrix.

![project flow chart](./Pictures/FlowChart.png "project flow chart")

## process of shape change of output data

在仅使用社会开源PoI的情况下，**最终保存为3维数据时的第三个维度形状为26**。也就是特征矩阵的列数为26。

需要注意的是grid是通过 康托 函数通过列号和行号生成的。

注意，只需要注意shape中的第二个维度的值即可，第一个维度值是和业务具体相关的。

| number | name           | shape       | description                                                                                           | columns name                                                                                                                                                                                                                                                                              |
| ------ | -------------- | ----------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1      | PoIFeture      | (9062, 15)  | 只包含社会特征的PoI特征。                                                                             | 列名称：['0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', '9.0', '10.0', '11.0', '12.0', '13.0', 'grid']。                                                                                                                                                                  |
| 2      | UserTrajectory | (28307, 22) | 将轨迹中的基本信息和PoI特征合并之后的特征。                                                           | 列名称：['latitude', 'longitude', 'alt', 'entireTime', 'loncol', 'latcol', 'grid', 'userID', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', '9.0', '10.0', '11.0', '12.0', '13.0']。                                                                                      |
| 3      | stay           | (55, 9)     | 由 tbd.traj_stay_move() 函数通过 UserTrajectory 生成的停留点特征。注意move 的特征和stay的形状不一样。 | 列名称：[uid, 'stime', 'LONCOL', 'LATCOL', 'etime', 'lon', 'lat', 'duration', 'stayid']。                                                                                                                                                                                                 |
| 4      | stay           | (55, 10)    | 添加了gird之后的stay。                                                                                | 列名称：[uid, 'stime', 'LONCOL', 'LATCOL', 'etime', 'lon', 'lat', 'duration', 'stayid', 'grid']。                                                                                                                                                                                         |
| 5      | stay           | (86, 16)    | 将时间'stime'列有 GenerateTimeFeature() 函数生成了6个时间特征。                                       | 列名称：[uid, 'stime', 'LONCOL', 'LATCOL', 'etime', 'lon', 'lat', 'duration', 'stayid', 'grid', 'weekofyear', 'dayofweek', 'dayofyear', 'quarter', 'month', 'hour']。                                                                                                                     |
| 6      | stay           | (86, 30)    | 将stay和PoI特征合并之后生成的特征。                                                                   | 列名称：[uid, 'stime', 'LONCOL', 'LATCOL', 'etime', 'lon', 'lat', 'duration', 'stayid', 'grid', 'weekofyear', 'dayofweek', 'dayofyear', 'quarter', 'month', 'hour', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', '9.0', '10.0', '11.0', '12.0', '13.0']。               |
| 7      | stay           | (86, 31)    | 由'stime'生成了'stimestamp'类之后的特征。                                                             | 列名称：[uid, 'stime', 'LONCOL', 'LATCOL', 'etime', 'lon', 'lat', 'duration', 'stayid', 'grid', 'weekofyear', 'dayofweek', 'dayofyear', 'quarter', 'month', 'hour', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', '9.0', '10.0', '11.0', '12.0', '13.0', 'stimestamp']。 |
| 8      | stay           | (86, 26)    | 删除了['stime', 'etime', 'stayid', 'lon', 'lat']之后的特征。此为最终输出的特征。                      | 列名称：[uid, 'LONCOL', 'LATCOL', 'duration', 'grid', 'weekofyear', 'dayofweek', 'dayofyear', 'quarter', 'month', 'hour', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', '9.0', '10.0', '11.0', '12.0', '13.0', 'stimestamp']。                                           |

[输出的日志详见](#log-of-changes-in-data-shape)。

### output data structure

1. netural time series. completed.
2. interaction matrxi. completed.
3. similar netural language matrix. completed.
4. graph structure. to be implemented.
5. Negative sample structure applied to contrastive learning.

| num | format             | describe                                                         |
| --- | ------------------ | ---------------------------------------------------------------- |
| 1   | statistical matrix | mainly used for collaborative filtering or matrix factorization. |
| 2   | language matrix    | mainly used for deep learning.                                   |
| 3   | time series        | mainly used for LSTM or others.                                  |
| 4   |                    |                                                                  |
| 5   |contrastive learning | used to improve accuracy@topk.                                  |

对比学习格式说明和示例：
```json
{
  'user': userID_q,
  'query': {
      'region': [...],
      'timestamp': [...],
      'features': [...],
  },
  'pos': {
      'user': userID_q,
      'region': regionID_t+1,
      'timestamp': ts_t+1,
      'features': [...]
  },
  'neg': [
      {'user': userID_1, 'region': r₁, 'timestamp': ts₁, 'features': [...]},
      {'user': userID_2, 'region': r₂, 'timestamp': ts₂, 'features': [...]},
  ]
}
```

```json
{
  "userID": 1,
  "query": {
    "region": ["wx4g0g1", "wx4g0g2", "wx4g0g3"],
    "timestamp": ["2025-01-28 08:00:00", "2025-01-28 08:10:00", "2025-01-28 08:20:00"],
    "features": [[0.1, 0.2], [0.3, 0.2], [0.4, 0.5]]
  },
  "pos": {
    "region": "wx4g0g4",
    "timestamp": "2025-01-28 08:30:00",
    "features": [0.5, 0.6]
  },
  "neg": [
    {
      "region": "wx4g0ga",
      "timestamp": "2025-01-28 08:30:00",
      "features": [0.1, 0.1]
    },
    {
      "region": "wx4g0gb",
      "timestamp": "2025-01-28 08:35:00",
      "features": [0.3, 0.4]
    }
  ]
}
{
  "userID": 1,
  "query": {
    "region": ["wx4g0g2", "wx4g0g3", "wx4g0g4"],
    "timestamp": ["2025-01-28 08:10:00", "2025-01-28 08:20:00", "2025-01-28 08:30:00"],
    "features": [[0.3, 0.2], [0.4, 0.5], [0.5, 0.6]]
  },
  "pos": {
    "region": "wx4g0g5",
    "timestamp": "2025-01-28 08:40:00",
    "features": [0.6, 0.7]
  },
  "neg": [
    {
      "region": "wx4g0gc",
      "timestamp": "2025-01-28 08:40:00",
      "features": [0.2, 0.2]
    }
  ]
}
{
  "userID": 1,
  "query": {
    "region": ["wx4g0g3", "wx4g0g4", "wx4g0g5"],
    "timestamp": ["2025-01-28 08:20:00", "2025-01-28 08:30:00", "2025-01-28 08:40:00"],
    "features": [[0.4, 0.5], [0.5, 0.6], [0.6, 0.7]]
  },
  "pos": {
    "region": "wx4g0g6",
    "timestamp": "2025-01-28 08:50:00",
    "features": [0.7, 0.8]
  },
  "neg": [
    {
      "region": "wx4g0gd",
      "timestamp": "2025-01-28 08:50:00",
      "features": [0.3, 0.3]
    }
  ]
}
{
  "userID": 2,
  "query": {
    "region": ["wx4g0h1", "wx4g0h2", "wx4g0h3"],
    "timestamp": ["2025-01-28 09:00:00", "2025-01-28 09:10:00", "2025-01-28 09:20:00"],
    "features": [[0.2, 0.3], [0.4, 0.5], [0.5, 0.6]]
  },
  "pos": {
    "region": "wx4g0h4",
    "timestamp": "2025-01-28 09:30:00",
    "features": [0.6, 0.7]
  },
  "neg": [
    {
      "region": "wx4g0hf",
      "timestamp": "2025-01-28 09:30:00",
      "features": [0.1, 0.2]
    }
  ]
}
```


## File structure

```bash
.
├─ README.md
├─ Record.md # 处理记录。现在存放的主要是删除的部分代码。
├─ CommonCode.py # 公用代码。
├─ GenerateGeographicFeature.py # 特征生成。
├─ AttachFeature.py # 特征附着到轨迹上。
├─ DP_GenerateTrajectory_ContainNegativeSample.py # 对比学习所需要的样本格式。
├─ DP_GenerateTrajectory.json # 不包含对比学习内容的轨迹生成。
├─ DP_GroupandSaveByID.json # 将输入的plt文件转换为按照用户ID存放的csv格式。
├─ Parameters.json
├─ Foursquare # Foursquare 数据，但是明显不符合连续轨迹的要求。
├─ Pictures
│  ├─ FlowChart.png # 流程图。
│  └─ FlowChart.vsd # 流程图。
├─ PreviousVersion
│  ├─ GenerateGeographicFeature_v1.0.3.py # 弃用。
│  └─ GeoFeatureGeneration_v1.py # 弃用。
├─ Data
│  ├─ Foursquare # 20241214发布的 Foursquare PoI 特征数据。
│  |   └─ ...
│  ├─ BeiJing
│  │   └─ Data
│  │       ├─ AccommodationServices.csv
│  │       ├─ BusinessResidence.csv
│  │       ├─ CommunalFacilities.csv
│  │       ├─ Corporation.csv
│  │       ├─ FamousScenery.csv
│  │       ├─ FinancialandInsuranceServices.csv
│  │       ├─ GovernmentAgenciesandSocialOrganizations.csv
│  │       ├─ HealthCareServices.csv
│  │       ├─ LifeService.csv
│  │       ├─ Restaurant.csv
│  │       ├─ ScienceEducationandCulturalServices.csv
│  │       ├─ Shopping.csv
│  │       ├─ SportsLeisureServices.csv
│  │       └─ TransportationFacilitiesServices.csv
│  ├─ Geolife Trajectories 1.3
│  │   └─ Data
│  │       ├─ 000
│  |       │  └─ Trajectory
│  │       ├─ 001
│  |       │  └─ Trajectory
│  │       ├─ 002
│  |       │  └─ Trajectory
│  │       ├─ 003
│  |       │  └─ Trajectory
│  |       ...
│  │       ├─ 180
│  |       │  └─ Trajectory
│  |       └─ 181
│  |          └─ Trajectory
│  └─ Output
│      └─ MultipleFeatures
└─ Test
```

## Package dependence

| num | package                | version |
| --- | ---------------------- | ------- |
| 1   | pandas                 | 2.2.3   |
| 2   | numpy                  | 2.0.2   |
| 3   | multiprocessing/python | python >=3.9   |
| 4   | geopandas              |         |
| 5   | json                   |         |
| 6   | datetime               |         |
| 7   | transbigdata           |  0.5.3  |
| 8   | polars              | 1.19.0  |
|     |                        |         |
|     |                        |         |
|     |                        |         |

## Test dataset

| num | data name             | source                                                                                                                                       |
| --- | --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Microsoft GeoLife 1.3 | [Geolife GPS trajectory dataset – User Guide](https://www.microsoft.com/en-us/research/publication/geolife-gps-trajectory-dataset-user-guide/) |
| 2   | BeiJing PoI feature   | Geographic  Data Sharing Infrastructure, College of Urban and  Environmental Science, Peking University (http://geodata.pku.edu.cn)          |
| 3   |                       |                                                                                                                                              |
| 4   |                       |                                                                                                                                              |
| 5   |                       |                                                                                                                                              |
| 6   |                       |                                                                                                                                              |

## appendix

### Log of changes in data shape

生成地理特征代码中的打印，用于观测生成过程中的数据的形状变化情况打印。

```log
GPU00:/workspace/codespace/GeoFeatureGeneration$ /bin/python3 /workspace/codespace/GeoFeatureGeneration/GenerateGeographicFeature.py
Start function: GetSocialPoIFeature() ,pid: 68720 ,start at: 2024-10-28 17:51:25 .
./Data/Output/MultipleFeatures/SocialFeature.csv is exist, will overwrite.
End function: GetSocialPoIFeature() ,pid: 68720 ,completed time: 2024-10-28 17:52:55.877729 ,
            consume time: 0:01:30.502298 .
./Data/Output/PoIFeature.csv is exist, it will overwrite.

 Output PoI feature shape is (9062, 14). columns Index([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0,
       13.0],
      dtype='float64').

GetPoIFeature completed. 0:01:30.612127
Start function: PreprocessTrajectory ,pid: 68720 ,start at: 2024-10-28 17:52:55 .

 Output all user trajectory shape is (1679880, 8). in this time, hast attach PoI feature.

End function: PreprocessTrajectory ,pid: 68720 ,completed time: 2024-10-28 17:58:06.391858 ,
            consume time: 0:05:10.404230 .
PreprocessTrajectory completed. 0:05:10.451671
Start function: AttachFeaturetoTrajectory() ,pid: 68720 ,start at: 2024-10-28 17:58:06 .

 1 007 PoIFeature shape is (9062, 15). columns Index(['0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', '9.0',
       '10.0', '11.0', '12.0', '13.0', 'grid'],
      dtype='object').

 1 002 PoIFeature shape is (9062, 15). columns Index(['0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', '9.0',
       '10.0', '11.0', '12.0', '13.0', 'grid'],
      dtype='object').

 1 005 PoIFeature shape is (9062, 15). columns Index(['0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', '9.0',
       '10.0', '11.0', '12.0', '13.0', 'grid'],
      dtype='object').

 1 006 PoIFeature shape is (9062, 15). columns Index(['0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', '9.0',
       '10.0', '11.0', '12.0', '13.0', 'grid'],
      dtype='object').

 1 004 PoIFeature shape is (9062, 15). columns Index(['0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', '9.0',
       '10.0', '11.0', '12.0', '13.0', 'grid'],
      dtype='object').

 1 008 PoIFeature shape is (9062, 15). columns Index(['0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', '9.0',
       '10.0', '11.0', '12.0', '13.0', 'grid'],
      dtype='object').

 1 003 PoIFeature shape is (9062, 15). columns Index(['0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', '9.0',
       '10.0', '11.0', '12.0', '13.0', 'grid'],
      dtype='object').

 1 009 PoIFeature shape is (9062, 15). columns Index(['0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', '9.0',
       '10.0', '11.0', '12.0', '13.0', 'grid'],
      dtype='object').

 1 001 PoIFeature shape is (9062, 15). columns Index(['0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', '9.0',
       '10.0', '11.0', '12.0', '13.0', 'grid'],
      dtype='object').

 1 000 PoIFeature shape is (9062, 15). columns Index(['0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', '9.0',
       '10.0', '11.0', '12.0', '13.0', 'grid'],
      dtype='object').

 1 006 UserTrajectory shape is (28307, 22). columns Index(['latitude', 'longitude', 'alt', 'entireTime', 'loncol', 'latcol',
       'grid', 'userID', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0',
       '7.0', '8.0', '9.0', '10.0', '11.0', '12.0', '13.0'],
      dtype='object').

 1 008 UserTrajectory shape is (77876, 22). columns Index(['latitude', 'longitude', 'alt', 'entireTime', 'loncol', 'latcol',
       'grid', 'userID', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0',
       '7.0', '8.0', '9.0', '10.0', '11.0', '12.0', '13.0'],
      dtype='object').

 1 009 UserTrajectory shape is (84567, 22). columns Index(['latitude', 'longitude', 'alt', 'entireTime', 'loncol', 'latcol',
       'grid', 'userID', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0',
       '7.0', '8.0', '9.0', '10.0', '11.0', '12.0', '13.0'],
      dtype='object').

 1 007 UserTrajectory shape is (87163, 22). columns Index(['latitude', 'longitude', 'alt', 'entireTime', 'loncol', 'latcol',
       'grid', 'userID', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0',
       '7.0', '8.0', '9.0', '10.0', '11.0', '12.0', '13.0'],
      dtype='object').

 1 005 UserTrajectory shape is (101187, 22). columns Index(['latitude', 'longitude', 'alt', 'entireTime', 'loncol', 'latcol',
       'grid', 'userID', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0',
       '7.0', '8.0', '9.0', '10.0', '11.0', '12.0', '13.0'],
      dtype='object').

 1 001 UserTrajectory shape is (108536, 22). columns Index(['latitude', 'longitude', 'alt', 'entireTime', 'loncol', 'latcol',
       'grid', 'userID', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0',
       '7.0', '8.0', '9.0', '10.0', '11.0', '12.0', '13.0'],
      dtype='object').

 1 000 UserTrajectory shape is (157482, 22). columns Index(['latitude', 'longitude', 'alt', 'entireTime', 'loncol', 'latcol',
       'grid', 'userID', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0',
       '7.0', '8.0', '9.0', '10.0', '11.0', '12.0', '13.0'],
      dtype='object').

 1 002 UserTrajectory shape is (223401, 22). columns Index(['latitude', 'longitude', 'alt', 'entireTime', 'loncol', 'latcol',
       'grid', 'userID', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0',
       '7.0', '8.0', '9.0', '10.0', '11.0', '12.0', '13.0'],
      dtype='object').

 1 004 UserTrajectory shape is (393368, 22). columns Index(['latitude', 'longitude', 'alt', 'entireTime', 'loncol', 'latcol',
       'grid', 'userID', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0',
       '7.0', '8.0', '9.0', '10.0', '11.0', '12.0', '13.0'],
      dtype='object').

 1 003 UserTrajectory shape is (417993, 22). columns Index(['latitude', 'longitude', 'alt', 'entireTime', 'loncol', 'latcol',
       'grid', 'userID', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0', '6.0',
       '7.0', '8.0', '9.0', '10.0', '11.0', '12.0', '13.0'],
      dtype='object').

End function: AttachFeaturetoTrajectory() ,pid: 68720 ,completed time: 2024-10-28 17:58:12.830981 ,
            consume time: 0:00:06.391711 .
AttachFeaturetoTrajectory independent completed. 0:00:06.393024
Start function: AttachFeaturetoTrajectory() ,pid: 68720 ,start at: 2024-10-28 17:58:12 .

 User trajectory feature shape is (1679880, 22) after attach PoI feature. 

End function: AttachFeaturetoTrajectory() ,pid: 68720 ,completed time: 2024-10-28 18:06:53.067720 ,
            consume time: 0:08:40.235459 .
AttachFeaturetoTrajectory merged completed. 0:08:46.848839
Start function: GenerateInteractionMatrix() ,pid: 68720 ,start at: 2024-10-28 18:06:53 .
End function: GenerateInteractionMatrix() ,pid: 68720 ,completed time: 2024-10-28 18:06:57.168352 ,
            consume time: 0:00:03.880209 .
GenerateInteractionMatrix completed. 0:00:03.896630
Start function: GenerateStayMove() ,pid: 68720 ,start at: 2024-10-28 18:06:57 .

 2 006 UserTrajectory shape is (28307, 22). 

 2 006 stay shape is (55, 9). 

 2 008 UserTrajectory shape is (77876, 22). 

 2 009 UserTrajectory shape is (84567, 22). 

 2 007 UserTrajectory shape is (87163, 22). 

 2.1 006 stay shape is (55, 10). 

 2 005 UserTrajectory shape is (101187, 22). 

 2 001 UserTrajectory shape is (108536, 22). 

 2 008 stay shape is (86, 9). 

 2 009 stay shape is (107, 9). 

 2 007 stay shape is (180, 9). 

 2.1 008 stay shape is (86, 10). 

 2 001 stay shape is (140, 9). 

 2 005 stay shape is (209, 9). 

 2.1 009 stay shape is (107, 10). 

 2 000 UserTrajectory shape is (157482, 22). 

 2.1 007 stay shape is (180, 10). 

 2.2 006 stay shape is (55, 16). 

2 Output single user stay shape is (55, 30).
006 feature has completed.

 2.1 001 stay shape is (140, 10). 

 2 002 UserTrajectory shape is (223401, 22). 

 2 000 stay shape is (497, 9). 

 2.1 005 stay shape is (209, 10). 

 2 002 stay shape is (348, 9). 

 2.2 008 stay shape is (86, 16). 

2 Output single user stay shape is (86, 30).
008 feature has completed.

 2 004 UserTrajectory shape is (393368, 22). 

 2.2 009 stay shape is (107, 16). 

2 Output single user stay shape is (107, 30).
009 feature has completed.

 2 003 UserTrajectory shape is (417993, 22). 

 2.1 000 stay shape is (497, 10). 

 2.1 002 stay shape is (348, 10). 

 2 004 stay shape is (1218, 9). 

 2.2 001 stay shape is (140, 16). 

2 Output single user stay shape is (140, 30).
001 feature has completed.

 2.2 007 stay shape is (180, 16). 

 2 003 stay shape is (1038, 9). 

2 Output single user stay shape is (180, 30).
007 feature has completed.

 2.2 005 stay shape is (209, 16). 

2 Output single user stay shape is (209, 30).
005 feature has completed.

 2.1 004 stay shape is (1218, 10). 

 2.1 003 stay shape is (1038, 10). 

 2.2 002 stay shape is (348, 16). 

2 Output single user stay shape is (348, 30).
002 feature has completed.

 2.2 000 stay shape is (497, 16). 

2 Output single user stay shape is (497, 30).
000 feature has completed.

 2.2 003 stay shape is (1038, 16). 

2 Output single user stay shape is (1038, 30).
003 feature has completed.

 2.2 004 stay shape is (1218, 16). 

2 Output single user stay shape is (1218, 30).
004 feature has completed.
End function: GenerateStayMove() ,pid: 68720 ,completed time: 2024-10-28 18:07:10.691792 ,
            consume time: 0:00:13.507059 .
Start function: GenerateStayMove() ,pid: 68720 ,start at: 2024-10-28 18:07:10 .
End function: GenerateStayMove() multiprocess completed. ,pid: 68720 ,completed time: 2024-10-28 18:07:20.424794 ,
            consume time: 0:00:09.731688 .
Output all users stays shape is (3902, 30).
End function: GenerateStayMove() ,pid: 68720 ,completed time: 2024-10-28 18:07:20.616948 ,
            consume time: 0:00:09.923833 .
GenerateStayMove completed. 0:00:23.434017
Start function: GenerateFeatureMatrix() ,pid: 68720 ,start at: 2024-10-28 18:07:20 .
3 stay shape (140, 30)
3.1 stay shape (140, 31)
001 SeriesToMatrix have completed. FeatureThirdDimension is 26
--- shareData.dat 26
3 stay shape (86, 30)
3.1 stay shape (86, 31)
008 SeriesToMatrix have completed. FeatureThirdDimension is 26
--- shareData.dat 26
3 stay shape (497, 30)
3.1 stay shape (497, 31)
000 SeriesToMatrix have completed. FeatureThirdDimension is 26
--- shareData.dat 26
3 stay shape (209, 30)
3.1 stay shape (209, 31)
005 SeriesToMatrix have completed. FeatureThirdDimension is 26
--- shareData.dat 26
3 stay shape (55, 30)
3.1 stay shape (55, 31)
006 SeriesToMatrix have completed. FeatureThirdDimension is 26
--- shareData.dat 26
3 stay shape (348, 30)
3.1 stay shape (348, 31)
002 SeriesToMatrix have completed. FeatureThirdDimension is 26
--- shareData.dat 26
3 stay shape (107, 30)
3.1 stay shape (107, 31)
009 SeriesToMatrix have completed. FeatureThirdDimension is 26
--- shareData.dat 26
3 stay shape (180, 30)
3.1 stay shape (180, 31)
007 SeriesToMatrix have completed. FeatureThirdDimension is 26
--- shareData.dat 26
3 stay shape (1218, 30)
3.1 stay shape (1218, 31)
004 SeriesToMatrix have completed. FeatureThirdDimension is 26
--- shareData.dat 26
3 stay shape (1038, 30)
3.1 stay shape (1038, 31)
003 SeriesToMatrix have completed. FeatureThirdDimension is 26
--- shareData.dat 26
--- gFeatureThirdDimension 26
End function: GenerateFeatureMatrix() ,pid: 68720 ,completed time: 2024-10-28 18:07:21.625091 ,
            consume time: 0:00:01.006364 .
GenerateFeatureMatrix completed. 0:00:01.033304
--ooo- gFeatureThirdDimension 0
FeatureThirdDimension 26, gFeatureThirdDimension 0
CombineUsersMatrix has completed.
CombineUsersMatrix completed. 0:00:00.150205
All completed. 0:15:56.426793
```
