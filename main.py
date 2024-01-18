
import GeoFeatureGeneration as gfg

# 步骤：
# 1. 生成PoI特征。
# 2. 如果有其他的特征，那么生成其他的特征。
# 3. 合并所有特征。
# 4. 将用户轨迹处理完成。
# 5. 将特征与用户轨迹合并。
# 6. 生成所需要的格式。


if __name__ == '__main__':
    # consume 1 minute.
    # gfg.GetPoIFeature()

    # consume 18:49 . 
    # gfg.gSaveUserTrajectoryFlag=True
    # gfg.PreprocessTrajectory(userRange='all', outputType='merged')

    # consume 5:36 .
    # gfg.AttachFeaturetoTrajectory(outputType='independent')
    # gfg.AttachFeaturetoTrajectory(outputType='merged')

    # consume 1:26 .
    gfg.gDeleteOutofBoundTrajectoryFlag = True
    gfg.GenerateInteractionMatrix()
