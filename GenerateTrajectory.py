import pandas as pd
# import polars as pl
import numpy as np
import transbigdata as tbd
import os
import multiprocessing
import torch
import torch.nn.functional as F
import CommonCode as cc


gBounds = [113.68, 29.97, 115.08, 31.37]
gAccuracy = 1000
gMethod = 'rect'
gGeoParameters = tbd.area_to_params(gBounds, accuracy = gAccuracy, method=gMethod)
gActivityTime = 1800
gSequeneceLength = 100

gAllGridMapping = cc.GenerateAllGridMapping(Bounds=gBounds, 
                                            mappingSavePath='./Data/Output/GridMapping/all_grid_mapping.csv')

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
        userTrajPath =  gUserTrajPath + '{}.csv'.format(ID)
        df = pd.read_csv(userTrajPath, encoding='gb18030')
        df = tbd.clean_outofbounds(df, bounds = gBounds, col = ['longitude', 'latitude'])

        if df.empty:
            print(f"ID {ID_map} DataFrame is empty after cleaning out of bounds.")
            return

        stay, move = tbd.traj_stay_move(df, 
                                        gGeoParameters,
                                        col=['ID', 'time', 'longitude', 'latitude'], 
                                        activitytime=gActivityTime)
        
        if stay.empty or move.empty:
            # 如果 stay 或 move 为空，则不进行后续处理。
            print(f"ID {ID_map} DataFrame is empty after generating stay and move.")
            return

        stay['loncol'], stay['latcol'] = tbd.GPS_to_grid(stay['lon'],stay['lat'], gGeoParameters)
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

        move['loncol'], move['latcol'] = tbd.GPS_to_grid(move['slon'],move['slat'], gGeoParameters)
        move = move.apply(cc.GenerateGrid, axis=1)
        move = move.merge(right=gAllGridMapping, on='grid', how='left').fillna(0)
        move = torch.tensor(move['grid_mapping'].values)
        move = pad_to_multiple(move, gSequeneceLength, pad_value=0)
        if move.shape[0] > gSequeneceLength:
            move = move.reshape(-1, gSequeneceLength)

        torch.save(stay, StaySavePath.format(ID_map))
        torch.save(move, MoveSavePath.format(ID_map))

    except Exception as e:
        print(f'Error processing user {ID} with ID_map {ID_map}: {e}')


def GenerateTrajectory():
    userList = next(os.walk(gUserTrajPath))[2]
    userList = [x.split('.')[0] for x in userList]

    users_pd = pd.DataFrame(userList, columns=['ID'])
    users_pd['ID_map'] = users_pd.index
    users_pd.to_csv('./Data/Output/UserIDMap/userID_map.csv', index=False)

    train_users = users_pd.sample(frac=0.8, random_state=42)
    test_users = users_pd.drop(train_users.index)

    for dataset_type, users, stay_path, move_path, all_stay_path in [
        ("train", train_users, gSingleUserTrainStaySavePath, gSingleUserTrainMoveSavePath, gAllTrainStaySavePath),
        ("test", test_users, gSingleUserTestStaySavePath, gSingleUserTestMoveSavePath, gAllTestStaySavePath)]:

        try:
            ProcessPool = multiprocessing.Pool()
            ProcessManager = multiprocessing.Manager()
            Lock = ProcessManager.Lock()
            ShareData = ProcessManager.Namespace()
            ShareData.dat = None

            for index, rows in users.iterrows():
                ID = rows['ID']
                ID_map = rows['ID_map']
                ProcessPool.apply_async(PreprocessSingleTrajectoryIndependent, args=(ID, ID_map, stay_path, move_path, ShareData, Lock))

            ProcessPool.close()
            ProcessPool.join()

            if ShareData.dat is not None:
                allStays = ShareData.dat.copy()
                allStays = torch.tensor(allStays['grid_mapping'].values)
                allStays = pad_to_multiple(allStays, gSequeneceLength, pad_value=0)
                if allStays.shape[0] > gSequeneceLength:
                    allStays = allStays.reshape(-1, gSequeneceLength)
                torch.save(allStays, all_stay_path)

        except Exception as e:
            print(f"{dataset_type} 数据处理时出现异常: {e}")

        finally:
            ProcessPool.terminate()
            ProcessManager.shutdown()
            print(f'{dataset_type.capitalize()} completed.')

gSingleUserTrainStaySavePath = "./Data/Output/Train/Stay/{}.pt"
gSingleUserTrainMoveSavePath = "./Data/Output/Train/Move/{}.pt"
gSingleUserTestStaySavePath = "./Data/Output/Test/Stay/{}.pt"
gSingleUserTestMoveSavePath = "./Data/Output/Test/Move/{}.pt"
gUserTrajPath =  './Data/Test/'
gAllTrainStaySavePath = './Data/Output/Train/train_all_stay.pt'
gAllTestStaySavePath = './Data/Output/Test/test_all_stay.pt'

if __name__ == '__main__':
    GenerateTrajectory()
    print('Complete.')