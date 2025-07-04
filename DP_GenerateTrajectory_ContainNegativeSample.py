# 1. 生成的负样本的格式如下：
# sample format:
# {
#   'query': {
#       'region': [...],     # regionID 序列
#       'timestamp': [...],  # 时间戳序列
#       'features': [...],   # 每个位置的其他特征
#   },
#   'pos': {
#       'region': regionID_{t+1},
#       'timestamp': ts_{t+1},
#       'features': [...]
#   },
#   'neg': [
#       {'region': r₁, 'timestamp': ts₁, 'features': [...]},
#       {'region': r₂, 'timestamp': ts₂, 'features': [...]},
#       ...
#   ]
# }

# 2. 负样本的生成策略：Temporal-aware + In-batch + Geo-aware Hard Negatives
#   1. 时间感知的负样本（Time-aware Negative Sampling, TANS）：也就在时间上前后的样本作为负样本。采样出时间上接近但不是当前轨迹的地点作为负样本。
#       例如：给定用户在 t_i 时间访问了 regionA，负样本可以是 t_i±Δ 时间内访问的其他 regionB（不是真实轨迹）。
#   2. 空间相似但未访问的区域（Geo-aware Negative Sampling）：空间上距离相近的作为负样本。从空间上相近但用户从未访问过的区域中采样。
#   3. 然后随机采集几个其他区域作为负样本。

import pandas as pd
import numpy as np
import transbigdata as tbd
import os
import multiprocessing
import torch
import torch.nn.functional as F
import CommonCode as cc
import time
from tqdm import tqdm

gBounds = [113.68, 29.97, 115.08, 31.37]
gAccuracy = 1000
gMethod = 'rect'
gGeoParameters = tbd.area_to_params(gBounds, accuracy=gAccuracy, method=gMethod)
gActivityTime = 1800
gSequeneceLength = 100

gAllGridMapping = cc.GenerateAllGridMapping(
    Bounds=gBounds,
    mappingSavePath='./Data/Output/GridMapping/all_grid_mapping.csv'
)

gSingleUserTrainStaySavePath = "./Data/Output/Train/Stay/{}.pt"
gSingleUserTrainMoveSavePath = "./Data/Output/Train/Move/{}.pt"
gSingleUserTestStaySavePath = "./Data/Output/Test/Stay/{}.pt"
gSingleUserTestMoveSavePath = "./Data/Output/Test/Move/{}.pt"
gUserTrajPath = './Data/Output/Trajectories/'
gAllTrainStaySavePath = './Data/Output/Train/train_all_stay.pt'
gAllTestStaySavePath = './Data/Output/Test/test_all_stay.pt'


def GenerateTANS():
    """_summary_
    Temporal-aware Negative Sampling (TANS) for trajectory data.
    生成时间上的负样本。
    """
    pass

def GenerateGANS():
    """_summary_
    Geo-aware Negative Sampling (GANS) for trajectory data.
    生成空间上的负样本。
    """
    pass

def GenerateRNS():
    """_summary_
    Random Negative Sampling (RNS) for trajectory data.
    随机采样负样本。
    """
    pass

def pad_to_multiple(tensor: torch.Tensor, multiple: int, pad_value=0):
    if tensor.dim() != 1:
        raise ValueError("只支持 1D tensor")
    length = tensor.size(0)
    pad_len = (multiple - length % multiple) % multiple
    if pad_len == 0:
        return tensor
    else:
        return F.pad(tensor, (0, pad_len), value=pad_value)


def PreprocessSingleTrajectoryIndependent(ID, ID_map,
                                          StaySavePath,
                                          MoveSavePath,
                                          ShareData, Lock):
    try:
        # 断点判断：是否已经处理过
        if os.path.exists(StaySavePath.format(ID_map)) and os.path.exists(MoveSavePath.format(ID_map)):
            print(f"ID {ID} 已存在，跳过。")
            return

        userTrajPath = gUserTrajPath + '{}.csv'.format(ID)
        df = pd.read_csv(userTrajPath, encoding='gb18030')
        df = tbd.clean_outofbounds(df, bounds=gBounds, col=['longitude', 'latitude'])

        if df.empty:
            print(f"ID {ID} 清洗后为空，跳过。")
            return

        stay, move = tbd.traj_stay_move(df, gGeoParameters,
                                        col=['ID', 'time', 'longitude', 'latitude'],
                                        activitytime=gActivityTime)

        if stay.empty or move.empty:
            print(f"ID {ID} stay 或 move 为空，跳过。")
            return

        # Stay 数据处理
        stay['loncol'], stay['latcol'] = tbd.GPS_to_grid(stay['lon'], stay['lat'], gGeoParameters)
        stay = stay.apply(cc.GenerateGrid, axis=1)
        stay = stay.merge(right=gAllGridMapping, on='grid', how='left').fillna(0)

        with Lock:
            if ShareData.dat is None:
                ShareData.dat = stay[['grid_mapping']].copy()
            else:
                ShareData.dat = pd.concat([ShareData.dat, stay[['grid_mapping']]], ignore_index=True)

        stay = torch.tensor(stay['grid_mapping'].values)
        stay = pad_to_multiple(stay, gSequeneceLength, pad_value=0)
        if stay.shape[0] > gSequeneceLength:
            stay = stay.reshape(-1, gSequeneceLength)

        # Move 数据处理
        move['loncol'], move['latcol'] = tbd.GPS_to_grid(move['slon'], move['slat'], gGeoParameters)
        move = move.apply(cc.GenerateGrid, axis=1)
        move = move.merge(right=gAllGridMapping, on='grid', how='left').fillna(0)
        move = torch.tensor(move['grid_mapping'].values)
        move = pad_to_multiple(move, gSequeneceLength, pad_value=0)
        if move.shape[0] > gSequeneceLength:
            move = move.reshape(-1, gSequeneceLength)

        torch.save(stay, StaySavePath.format(ID_map))
        torch.save(move, MoveSavePath.format(ID_map))
        print(f"完成处理 ID {ID}")

    except Exception as e:
        print(f'处理用户 {ID} 出错: {e}')

def GenerateTrajectory():
    start_time = time.time()

    userList = next(os.walk(gUserTrajPath))[2]
    userList = [x.split('.')[0] for x in userList]

    users_pd = pd.DataFrame(userList, columns=['ID'])
    users_pd['ID_map'] = users_pd.index
    users_pd.to_csv('./Data/Output/UserIDMap/userID_map.csv', index=False)

    train_users = users_pd.sample(frac=0.8, random_state=42)
    test_users = users_pd.drop(train_users.index)

    # 将资源管理放循环外
    ProcessManager = multiprocessing.Manager()
    Lock = ProcessManager.Lock()
    ShareData = ProcessManager.Namespace()
    ShareData.dat = None

    for dataset_type, users, stay_path, move_path, all_stay_path in [
        ("train", train_users, gSingleUserTrainStaySavePath, gSingleUserTrainMoveSavePath, gAllTrainStaySavePath),
        ("test", test_users, gSingleUserTestStaySavePath, gSingleUserTestMoveSavePath, gAllTestStaySavePath)]:

        print(f"\n--- 开始处理 {dataset_type} 数据集，共 {len(users)} 个用户 ---")
        ProcessPool = multiprocessing.Pool()
        
        with tqdm(total=len(users), desc=f"{dataset_type.capitalize()} Progress") as pbar:
        
            for index, row in users.iterrows():
                ID = row['ID']
                ID_map = row['ID_map']
                
                # 检查是否已处理（断点恢复）
                stay_exists = os.path.exists(stay_path.format(ID_map))
                move_exists = os.path.exists(move_path.format(ID_map))
                if stay_exists and move_exists:
                    pbar.update(1)
                    continue
                def callback(_): pbar.update(1)
                
                ProcessPool.apply_async(PreprocessSingleTrajectoryIndependent,
                                        args=(ID, ID_map, stay_path, move_path, ShareData, Lock),
                                        callback=callback)

        ProcessPool.close()
        ProcessPool.join()

        if ShareData.dat is not None:
            allStays = ShareData.dat.copy()
            allStays = torch.tensor(allStays['grid_mapping'].values)
            allStays = pad_to_multiple(allStays, gSequeneceLength, pad_value=0)
            if allStays.shape[0] > gSequeneceLength:
                allStays = allStays.reshape(-1, gSequeneceLength)
            torch.save(allStays, all_stay_path)

        ShareData.dat = None
        print(f"{dataset_type} 数据处理完成。")

    ProcessManager.shutdown()
    print(f"全部数据处理完成，总耗时 {time.time() - start_time:.2f} 秒")
