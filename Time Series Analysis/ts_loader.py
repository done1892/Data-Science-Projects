from torch.utils.data import Dataset
from utils import *
import torch


class Time_Series_Data(Dataset):

    def __init__(self, train_x, train_y):
        self.X = train_x
        self.y = train_y

    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, item):
        x_t = self.X[item]
        y_t = self.y[item]
        return x_t, y_t