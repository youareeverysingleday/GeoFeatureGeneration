import sys

import GeoFeatureGeneration as gfg

# 步骤：
# 1. 生成PoI特征。
# 2. 如果有其他的特征，那么生成其他的特征。
# 3. 合并所有特征。
# 4. 将用户轨迹处理完成。
# 5. 将特征与用户轨迹合并。
# 6. 生成所需要的格式。
# 
# 
# 
# 

if __name__ == '__main__':
    gfg.PrintStartInfo(functionName='test')
    