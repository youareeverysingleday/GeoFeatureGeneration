# record

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