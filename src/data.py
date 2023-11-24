from utils.helpers import Dir
import pandas as pd
import numpy as np
from typing import List
from datetime import datetime


class Data:

    Dir = Dir.joinpath('data')

    def __init__(self):
        ...

    @staticmethod
    def load_file_names():
        return list(Data.Dir.rglob('*.txt'))

    def load_file(self):
        d = np.array(pd.read_csv(self.load_file_names()[0], sep='\t', header=None, skip_blank_lines=False)).flatten()
        nan_inds = np.arange(d.size, dtype='i')[pd.isnull(d)]
        d = np.delete(d, nan_inds)  # remove nan values
        return np.split(d, np.unique(nan_inds - np.arange(nan_inds.size))[:-1])


class Player:

    def __init__(self, lst: List[str]):
        ...


class Hero(Player):
    ...


class Hand:

    def __init__(self, lst: List[str]):

        fl = lst[0]  # first line

        self.Number = fl[fl.find('#'):fl.find(':')]
        self.Type = fl[fl.find(':') + 2:fl.find('(') - 1]
        self.Limits = self.find_limits(fl)
        self.List = lst
        self.Date = datetime.strptime(fl[fl.find('-') + 2:], '%Y/%m/%d %H:%M:%S')

        sl = lst[1]  # second line
        fa = sl.find('\'') + 1
        self.Table = sl[fa:sl.find('\'', fa)]
        self.MaxPlayers = int(sl[sl.find('\'', fa) + 2:sl.find('-')])
        self.Button = int(sl[sl.find('#') + 1])
        self.Players = self.find_players(lst[2:2 + self.MaxPlayers])
        self.NPlayers = len(self.Players)

    def __repr__(self):
        return f'Poker Hand {self.Number}: {self.Type} (${self.Limits[0]}/${self.Limits[1]}) - {self.Date}'

    @staticmethod
    def find_limits(fl: str):
        b, m, e = fl.find('(') + 2, fl.find('/'), fl.find(')')
        return np.array([fl[b:m], fl[m + 2: e]], dtype='float')

    @staticmethod
    def find_players(lst: List[str]) -> List[Player]:
        return []
