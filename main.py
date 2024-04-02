
import GeoFeatureGeneration as gfg

if __name__ == '__main__':
    gfg.GetParameters('./Parameters.json')

    print(gfg.gGeoParameters)

    # consume 1 minter.
    # gfg.GetPoIFeature()

    # consume 18:49 . 
    # gfg.gSaveUserTrajectoryFlag=True
    # gfg.PreprocessTrajectory(userRange='all', outputType='merged')

    # consume 5:36 .
    # 两种模式都需要处理一次，主要时候后面最终输出为不同的格式时需要不同的数据形状。
    # 生成交互矩阵需要使用所有用户在一个dataframe的形式。
    # 在生成轨迹特征的时候，单独处理一个dataframe效率太低，建议使用分别处理每个用户的形式。
    # gfg.AttachFeaturetoTrajectory(outputType='independent')
    # gfg.AttachFeaturetoTrajectory(outputType='merged')

    # consume 1:26 .
    # 需要将区域外的地点都排除。
    # gfg.gDeleteOutofBoundTrajectoryFlag = True
    # gfg.GenerateInteractionMatrix()

    # consume 2:24:26 .
    # 建议使用对每个用户分别处理的形式。最后再进行合并效率比较高。
    # test gfg.gUserList = ['079', '047']
    # gfg.gDeleteOutofBoundTrajectoryFlag = True
    # gfg.GenerateStayMove(ProcessType='independent')

    # gfg.GenerateFeatureMatrix(ProcessType='independent')

    # gfg.CombineUsersMatrix()
