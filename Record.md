# record


## problom

1. ~~出现了完全不在北京市的轨迹，用户ID为118、132、160。在将轨迹特征和PoI特征合并时会出现KeyError的报错。~~
   1. 118的活动轨迹主要在内蒙古，距离最近的城市是黑龙江的齐齐哈尔。132的活动轨迹主要在宁波市和杭州市。160的活动轨迹主要在柬埔寨的暹粒市。
   2. 在试验的时候pandas.dataframe merge空数据集是没有报错的。还不清楚在 GenerateGeographicFeature.py 中为什么报错。
      1. 原因找到了：因为在对用户轨迹进行处理的函数中 PreprocessSingleTrajectoryMerged() 和 PreprocessSingleTrajectoryIndependent() 都做了 tbd.clean_outofbounds 处理。也就是将所有指定范围之外的轨迹删除了。这个时候用户ID为118、132、160三个用户的轨迹都处理指定范围之外，导致生成的轨迹dataframe虽然保留了列名，但是具体数据为空。而当使用 df_sampling = df_sampling.apply(GenerateGrid, axis=1) 生成grid的时候，由于具体数据为空，pandas的apply函数并不会生成一个新的'grid'列。所以导致 AttachFeaturetoSingleUserTrajectory() 和 MergeUsersTrajectoryandPoIFeature() 函数在合并 PoIFeature 和 用户轨迹数据时报 KeyError 的报错。
   3. 解决方法：将tbd.clean_outofbounds 放到 df_sampling = df_sampling.apply(GenerateGrid, axis=1) 之后来执行。
2. ~~直接的cantor配对函数只能应用在非负整数范围。很多坐标在计算格栅的时候为负值使用cantor配对函数出错。~~
   1. 参考:[https://www.bilibili.com/read/cv8399988/](https://www.bilibili.com/read/cv8399988/)
   2. 解决方法：将正整数和0折叠为自然数中的偶数，将负整数折叠为奇数。然后再使用cantor配对函数。
      folding function：

      $$
      f(n) = \left\{\begin{aligned}
            & 2n  & , \, & \text{if } n \geqslant 0\\
            & 2|n| - 1 = 2  & , \, & \text{otherwise}
            \end{aligned}\right.
      $$

      cantor pairing function: $z = \pi (x, y) = \frac{(x+y)(x+y+1)}{2} + y \, x,y\geqslant 0 \, ,x,y\in \mathbb{Z}. $
3. ~~tbd.traj_stay_move() 函数在生成 move['duration'] = ( move['etime'] - move['stime']).dt.total_seconds() 是没有像 生成stay['duration'] = (pd.to_datetime(stay['etime']) - pd.to_datetime(stay['stime'])).dt.total_seconds() 一样将 move['etime'] 和 move['stime'] 使用 pd.to_datetime() 方法转换。从而导致在 GenerateTimeFeature() 在生成时间的时候报错。~~
   1. 解决方法：修改transbigdata的源码。将transbigdata中的traj.py文件中的traj_stay_move()第729行修改为 move['duration'] = (pd.to_datetime((move['etime']) - pd.to_datetime((move['stime'])).dt.total_seconds() 。
4. ~~在GenerateSingleUserStayMove() 和 GenerateStayMoveByChunk() 方法使用过程中遇到了和1中一样的问题。也就是对于特定用户的 userTrajectory 是空的。导致没有生成grid列。~~
   1. 解决方法：判断读取的 userTrajectory 的形状是否没有内容。直接生成空的DataFrame来保存。GenerateStayMoveByChunk()可能由于多个用户共同的轨迹文件的体积大，所以没有出现上述症状。
5. ~~之前设置的北京的坐标范围[115.7, 39.4, 117.4, 41.6]有问题。上边界距离北京太远。~~
   1. 解决方法：现在设置为：gBounds = [115.4, 39.4, 117.55, 41.1]。经度越往东数值越大，是竖线。纬度越往北数值越大，是横线。参考[全国各省市经纬度范围](https://blog.csdn.net/esa72ya/article/details/114642127)，应该设置为：115.416827~117.508251，39.442078~41.058964。
6. ~~与问题1类似，在生成stay和move的时候，由于设置的判断stay时间间隔是30分钟，有些用户可能所有的停留时间都没有超过30分钟的情况。其中137、120、049、178、123生成的stay为空。所以导致合并特征的时候gird失败。~~
   1. 在生成stay的时候做判断，分别处理。
   2. **所有要做下采样或者缩小数据规模的操作都需要判断产生的数据为空了，从而导致合并数据失败！**
   3. 现在以下用户在生成数据的过程中所有的数据都被删除了。=132、-137、=118、-120、=160、-049、-178、-123。
7. ~~GenerateStayMove(ProcessType='merged')  -> GenerateStayMoveByChunk() -> stay = stay.apply(cc.GenerateGrid, lonColName='LONCOL', latColName='LATCOL', axis=1) 这段代码在对多个chunk 并没有执行生成 grid，直接导致后面的代码执行失败。~~
   1. 由于在生成stay的时候，有些轨迹并没有停留超过1800秒的点，所以导致生成的stay为空。直接导致stay.apply()报错。
8. ~~在132、137、118、120、160、123这个几个用户在 SeriesToMatrix 函数中生成的matrix的长度与其他的用户生成的长度不一样，好像没有经过数值化处理一样。132、137、118、120、160、123的长度为2944，而其他用户的矩阵长度是3584。~~
   1. 已经解决：是由于在 SeriesToMatrix() 函数中读取的stay数据为空导致的。原因是 GenerateSingleUserStayMove() 函数在 tbd.clean_outofbounds() 和 tbd.traj_stay_move() 会使得生成的stay的数据减少。所以导致 SeriesToMatrix() 读取的数据只有列名，没有数值数据。因此导致报错。
9. 在完整流程中，也就是执行完GenerateInteractionMatrix()之后再执行GenerateStayMove(ProcessType='independent')时， GenerateStayMove(ProcessType='independent') 处理第一个132号user的数据之后会停留非常长的时间。按道理应该是多任务并发处理多个用户的数据。此时CPU也是空闲的状态，内存也空余很大。但是当主程序从 GenerateStayMove(ProcessType='independent') 开始执行时，就会非常快的进入并发对多个user数据进行处理的操作。不清楚原因。
   1. 有以下几个建议，但并不能直接解决问题：
10. 需要增加的特征：
   1. 距离上一个点的距离。
   2. 距离上一个点的时间。
   3. 上一个点来到当前点的速度。
   4. 需要生成的特征中可以包含：来的方向和去的方向。
      1. 需要注意的是：来的方向是已知量，但去的方向是未知量。
         1. 最后一个停留点的去的方向是空值。
      2. 去的方向可以用作为标签来进行预测。预测之后再进行下一个停留点的预测。预测的方向可以作为缩小样本的限制条件。
      3. **定义一个函数来从stay中生成方向数据。**
         1. **注意需要判断id是否是同一个人的停留点。**
         2. **在算法中需要生成依据方向样本生成函数，或者按照方向对样本的惩罚系数！！！**
11. 生成包含userID的轨迹数据。
    1. 需要考虑userID和区域ID的融合方式。
       1. 已经试验多种融合方式。现在需要选择其中一个。
      

## next plan

1. ~~完成geo特征的合并，在输出数据结构的时候使用合并之后的Geo特征。~~
2. move的特征需要特殊处理。因为move包含起点和终点，有两个地理特征。
3. ~~需要统一的列名。不能在不同的函数中使用不同的列名。特别是在生成PoI特征和用户轨迹时，经纬度列的命名方式有的是全称，有的是简写。需要统一。~~
   1. 解决说明：已经统一。使用康托配对函数实现。
4. 输出图结构的数据。
5. ~~使用cantor函数来生成唯一的grid编号。~~
6. ~~需要可以灵活的给用户的轨迹添加特征。~~
   1. 需要添加速度特征。对于 stay 添加的速度特征是与前一个stay之间的速度。这是不是意味这需要添加的是和前一个stay的距离？
   2. 新生成的特征可以通过函数直接附加到轨迹携带的特征上，从而不用每次都重新运行。
   3. 解决说明：每次生成新的poi特征，然后和trajectory合并。
7. ~~在没有生成stay和move之前，是否需要给轨迹添加PoI特征？需要思考，因为 transbigdata.traj_stay_move() 函数会将除它选择的列都删除。~~
   1. ~~可以修改 transbigdata 的函数。~~
   2. 也可以自己编写函数来生成stay和move。
   3. 解决说明：这个影响不大。
8. ~~其中 AttachFeaturetoTrajectory() 的 elif outputType == 'merged': 部分代码非常耗时，需要改进。~~
   1. 还没有好的方法来提高速度。
   2. merge 中的 sort=True参数对数据进行排序，这可以加快合并的速度。但是将PoI和trajectory合并的时候，trajectory并不是按照grid进行顺序进行排列的；而是按照时间顺序进行排列的。
   3. join 需要合并的两个数据的index是需要合并比对的对象（join用于将两表按照索引列进行合并）；而trajectory不可能将grid作为index。理论上join会比merge快。
   4. concat用户堆叠，不能灵活的按指定列进行合并。
   5. 使用polars来解决这个问题。特别是解决merge速度慢的问题。
9.  每个地域的特征是随着用户和时间变化而变化的。比如用户在白天访问一个地域的医院，但是在晚上访问同一个地域的超市。由于时间的变化，同一个地域的特征表现是不一样的。同样的不同的用户也访问同一个不同特征。
   1. 需要通过一个模型来学习不同时间地域的不同特征表现。不同的人不同时间访问同一地域会生成该地域的不同特征。time2vec模型。如果没有明确用户的特制的情况下，用用户的轨迹来描述用户的特征。有明确用户特征的，直接用用户特征来区分用户。参考GETNext论文中的表述。
10. ~~**对于问题1, 4, 6 需要统一的解决方法。**~~
    1. 特别是在函数 GenerateSingleUserStayMove() 中填充了人工输入的列名。需要通过之前合并的数据来获取列名并填充这才合理。
    2. 另外对于所有的进行下采样或者缩小数据规模的操作都需要判断产生的数据为空了，而且需要做一个统一的处理。
11. ~~可以思考包含的PoI特征：兴趣点（POI, Point of Interest）数据的特征提取是地理信息处理和分析的重要环节。根据不同的应用场景，POI可以提取以下主要特征~~：
    1. 暂时放弃，因为
    2. 基本属性特征
      - 名称（Name）：POI的具体名称。
      - 类别（Category）：POI所属的功能类型，例如餐馆、学校、超市、医院等。
      - 地址（Address）：POI的详细地址信息。
      - 地理坐标（Location）：POI的经纬度坐标。
    3. 空间特征
      - 距离特征：与其他POI的距离，与用户当前位置的距离。
      - 分布特征：POI在空间中的密度或分布模式，例如聚集区还是分散区。
      - 邻域特征：POI周围的一定范围内其他POI的数量和类别。
    4. 时间特征
      - 开放时间（Opening Hours）：POI的开放时间范围。
      - 访问时间分布：用户访问该POI的时间统计，例如高峰时段。
      - 动态变化特征：POI的时序特性，例如随时间变化的客流量。
    5. 用户行为特征
      - 访问频率（Visit Frequency）：用户访问POI的次数。
      - 用户停留时间（Dwell Time）：用户在POI的平均停留时间。
      - 用户偏好（User Preference）：访问该POI的用户偏好，例如餐馆口味、活动类型。
    6. 社交特征
      - 评论数量（Review Count）：POI的评论或评价数量。
      - 评分（Rating）：用户对该POI的评分。
      - 分享行为（Sharing Behavior）：用户在社交媒体中对POI的提及或分享频次。
    7. 上下文特征
      - 天气特征：访问POI时的天气状况，例如晴天、雨天。
      - 节假日特征：访问是否发生在节假日。
      - 事件特征：POI附近是否有大型活动或事件发生。
    8. 行业特征
      - 经营规模：POI的占地面积或规模。
      - 收入水平：POI的平均收入水平（如餐馆的客单价）。
      - 行业类型：POI是否属于特定行业分类。
    9. 网络连接特征
      - 交通可达性：与交通设施的距离，例如地铁站、公交站。
      - 路径特征：用户从当前位置到达该POI的路径或通行方式。
      - 相邻POI连接：与其他POI的逻辑或物理连接，例如商场内的不同店铺。
    10. 视觉特征
      - 图片描述：POI的图片或视觉描述特征。
      - 地标性：POI是否具有标志性特征（如著名景点）。
      - 通过对这些特征的提取和分析，可以为推荐系统、城市规划、商圈分析等应用场景提供有效支持。
12. foursquare 数据处理参考：
    1. <https://www.kaggle.com/code/ryotayoshinobu/foursquare-lightgbm-baseline>
    2. 重点-<https://zhuanlan.zhihu.com/p/540416289>
    3. <https://github.com/hobbitlab/Foursquare-Location-Matching>
    4. <https://jishu.proginn.com/doc/7780647801f904d12>
13. ~~需要使用polars来完全替换pandas。因为polars速度确实快（至少缩短了2个数量级的时间）。~~
    1. 还不能完全替换，因为tranbigdata使用的是pandas。
    2. 但merge操作肯定需要替换的。
14. ~~生成地址携带的特征。因为单纯的poi特征没有表明方位信息，也就是说在东面的一个商场和西面的一个商场在poi特征上是一样的。但是他们距离用户的真实地址是不一样的。同时地址表明了地理上人文属性，比如国家、省份等。另外顺便也要将经纬度信息放入特征中，因为经纬度从另一个方面表明了相对的距离信息。同时经纬度有它的缺陷，明显的经纬度0-180之间有个突然的转换。所以只能作为特征一种。~~
    1. 使用stay中心经纬度作为特征。经纬度数值化的表示了方向和距离。
15. 代码改进建议：
   1. 使用logging来进行日志处理。示例代码如下：
      ```python
      import pandas as pd
      import geopandas as gpd
      import os
      import logging

      # 配置日志
      logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

      def load_data(file_path: str) -> pd.DataFrame:
         """
         加载数据
         """
         logging.info(f"正在加载数据：{file_path}")
         try:
            data = pd.read_csv(file_path)
            return data
         except Exception as e:
            logging.error(f"数据加载失败：{e}")
            raise

      def preprocess_data(data: pd.DataFrame) -> pd.DataFrame:
         """
         数据预处理
         """
         logging.info("开始数据预处理")
         # 示例：填充缺失值
         data = data.fillna(0)
         return data

      def generate_features(data: pd.DataFrame) -> pd.DataFrame:
         """
         特征生成
         """
         logging.info("开始生成特征")
         # 示例：创建一个新特征
         data['new_feature'] = data['some_column'] * 2
         return data

      def main():
         # 主流程
         file_path = "input.csv"
         output_path = "output.csv"

         data = load_data(file_path)
         data = preprocess_data(data)
         data = generate_features(data)
         data.to_csv(output_path, index=False)
         logging.info(f"处理完成，结果已保存到：{output_path}")

      if __name__ == "__main__":
         main()
      ```
   2. 使用gc来释放内存。
      ```python
      # 确保在转换时释放内存
      import gc

      polars_df = polars.from_pandas(pandas_df)
      del pandas_df
      gc.collect()
      ```
16. ~~完成foursquare的数据预处理。~~
    1. 放弃。foursquare不符合要求。


## 删除的代码

1. 用于将经纬度转换为文字地址在转换为embedding的过程。

    在函数 GetPekingUniversityPoIFeature() 删除的代码。
    ```python
    # --------------------这里添加从poi数据中获取的特征。-----------------------
        # 添加地址嵌入向量和经纬度。

        # 生成地址携带的特征。因为单纯的poi特征没有表明方位信息，也就是说在东面的一个商场和西面的一个商场在poi特征上是一样的。但是他们距离用户的真实地址是不一样的。
        # 同时地址表明了地理上人文属性，比如国家、省份等。
        # 另外顺便也要将经纬度信息放入特征中，因为经纬度从另一个方面表明了相对的距离信息。同时经纬度有它的缺陷，明显的经纬度0-180之间有个突然的转换。所以只能作为特征一种。

        # 步骤：
        # 1. 通过 grid 和 transbigdata 换算出格栅中心的经纬度。
        # 2. 通过 geopy 获得经纬度的地址。
        # 3. 通过 sentence_transformers 将地址向量化。
        # 4. 将经纬度和地址的向量化信息添加到poi特征中。

        # 注意，partofPoIFeature 目前的列里面是没有grid列的。grid是作为index存在的。
        geolocator = Nominatim(user_agent="http")
        geocoder = BaiduV3(api_key='your baidu AK', timeout=200)

        model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')

        # 注意，partofPoIFeature 目前的列里面是没有grid列的。grid是作为index存在的。
        partofPoIFeature = partofPoIFeature.apply(GetLongitudeLatitude, GeoParameters=gGeoParameters, 
                                                axis=1)
        
        # partofPoIFeature = partofPoIFeature.apply(GetAddressByOpensteetmap, geolocator=geolocator, 
        #                                           axis=1)
        # 不再使用地址的描述作为判断方位的
        # partofPoIFeature= partofPoIFeature.apply(GetAddressByApply, geolocator=geolocator, geocoder=geocoder, 
        #                                          axis=1)
        
        partofPoIFeature = partofPoIFeature.apply(GenerateAddressEmbedding, model=model, 
                                                axis=1)
        # -------------------------------------------
    ```

    因为使用到网络接口来将经纬度转换为地址，所以需要处理网络异常的情况。因为不再使用地址embedding作为判断方位的表示，所以删除如下代码：
    ```python
    def ProcessNetworkErrorApply(df, geolocator, geocoder, model, vectorLength=512):
        """_summary_
        处理网络错误导致的经纬度转地址错误的pandas apply函数。
        Args:
            df (pandas.DataFrame): 输出数据集。
            geolocator (_type_): openstreetmap的geolocator。
            geocoder (_type_): baiduv3的geocoder。
            model (_type_): 地址转为向量的模型。
            vectorLength (int, optional): 第一次处理PoI数据后embedding的长度. Defaults to 512.

        Returns:
            pandas.DataFrame: _description_
        """
        if df['address'] == 'networkerror':
            print('grid:{} error.'.format(df.name))
            try:
                location = geolocator.reverse(f"{df['latitude']}, {df['longitude']}")
                df['address'] = location.address
                
                embedding = model.encode(df['address'])
                embedding = pd.Series(embedding)
                df[-vectorLength:] = embedding
                time.sleep(1)
            except:
                try:
                    location = geocoder.reverse(f"{df['longitude']}, {df['latitude']}")
                    df['address'] = location.raw['formatted_address']
                    
                    embedding = model.encode(df['address'])
                    embedding = pd.Series(embedding)
                    df[-vectorLength:] = embedding
                    time.sleep(1)
                except:
                    df['address'] = 'networkerror'
                    print('grid {} both openstreetmap and baidu are network error.'.format(df.name))
            
        return df

    def ProcessNetworkError(PoIFeaturePath='./Data/Output/PoIFeature.csv',
                            PoIFeatureSavePath='./Data/Output/PoIFeature.csv'):
        """_summary_
        处理网络错误导致的经纬度转地址错误。
        这个函数不在main中运行，而是等main处理完成之后，再查漏补缺的。而且每天经纬度转地址是有次数限制的。
        注意保存的路径和读入的路径是不一样的。因为不能确定在处理经纬度转地址的过程中不出现错误。
        Args:
            PoIFeaturePath (str, optional): 第一次生成PoI特征时的路径. Defaults to './Data/Output/PoIFeature.csv'.
            PoIFeatureSavePath (str, optional): 处理网络故障之后保存PoI特征时的路径. Defaults to './Data/Output/PoIFeature2.csv'.
        """
        PoIFeature = pd.read_csv(PoIFeaturePath, index_col=0)
        geolocator = Nominatim(user_agent="http")
        geocoder = BaiduV3(api_key='your ak', timeout=200)
        model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')
        
        PoIFeature = PoIFeature.apply(ProcessNetworkErrorApply, geolocator=geolocator, geocoder=geocoder, 
                                    model=model, 
                                    vectorLength=512,
                                    axis=1)
        # 删除地址的文字列。
        PoIFeature.drop(columns=['address'], inplace=True)
        PoIFeature.to_csv(PoIFeatureSavePath)
        print("Completed.")
    ```