import pandas as pd
import polars as pl
import numpy as np
import transbigdata as tbd
import os
# display polars' progress bar.
# os.environ['POLARS_VERBOSE'] = '1'
import math
import multiprocessing
import json
import datetime

import csv

import CommonCode as cc

gParameters = cc.JSONConfig('./Parameters.json')
gGeoParameters = tbd.area_to_params(gParameters.get('gBounds'), accuracy = 1000, method='rect')

FolderPath = './Data/Geolif Trajectories 1.4/'
FilePath = './Data/Geolif Trajectories 1.4/1.csv'
columns = ['ID', 'time', 'ID2', 'longitude', 'latitude', 'geohash', 'epoch0', 'epoch1']
df = pd.read_csv(FilePath, encoding='gb18030', header=0)
df = tbd.clean_outofbounds(df, bounds = gParameters.get('gBounds'), col = ['longitude', 'latitude'])
