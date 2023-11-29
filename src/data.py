from utils.helpers import Dir, print_table, colored
import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime
from src.street import *


POSITIONS = ['UTG1', 'UTG2', 'UTG3', 'MP1', 'MP2', 'MP3', 'CO', 'BUT', 'SB', 'BB']


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

    def __init__(self, s: str):

        cp = s.find(':')
        bp = s.find('(')

        self.ID = s[cp + 2:bp - 1]
        self.Seat = int(s[cp - 1])
        self.Position = None
        self.Chips = float(s[bp + 2:s.find(' ', bp)])

        self.HoleCards: List[str] = []

        self.Ante = 0.
        self.SB = 0.
        self.BB = 0.
        self.Investment = 0.
        self.Value = 0.

    def __repr__(self):
        return f'Player {self.ID} ({self.Position})'

    @property
    def committment(self):
        return self.Ante + self.SB + self.BB + self.Investment

    @property
    def value_str(self):
        v = self.Value - self.committment
        return colored(f'{CURRENCY}{v:.2f}', 'red' if v < 0 else None if v == 0 else 'green')

    def set_ante(self, v: float):
        self.Ante = v

    def set_small_blind(self, v: float):
        self.SB = v

    def set_big_blind(self, v: float):
        self.BB = v

    def set_hole_cards(self, s: List[str]):
        self.HoleCards = s

    def set_value(self, v: float):
        self.Value = v


class Hero(Player):
    ...


def make_player(s: str):
    return Hero(s) if 'Hero' in s else Player(s)


class Hand:

    def __init__(self, lst: List[str]):

        self.AtLine = 0
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
        self.Players = self.find_players(lst)
        self.NPlayers = len(self.Players)
        self.find_positions()
        self.add_blinds_and_ante(lst)
        self.add_hole_cards(lst)

        self.Pot = [sum(pl.committment for pl in self.Players.values())]

        self.PreFlop = PreFlop(self, lst)
        self.Flop = Flop(self, lst)
        self.Turn = Turn(self, lst)
        self.River = River(self, lst)

        self.Board = self.Flop + self.Turn + self.River

        self.Rake = 0.
        self.Jackpot = 0.

        self.summarise(lst)

    def __repr__(self):
        return f'Poker Hand {self.Number}: {self.Type} (${self.Limits[0]}/${self.Limits[1]}) - {self.Date}'

    @property
    def pot(self):
        return sum(pl.committment for pl in self.Players.values())

    def find_positions(self):
        for pos, pl in zip(np.roll(POSITIONS[-self.NPlayers:], self.Button + 1), self.Players.values()):
            pl.Position = pos

    @staticmethod
    def find_limits(fl: str):
        b, m, e = fl.find('(') + 2, fl.find('/'), fl.find(')')
        return np.array([fl[b:m], fl[m + 2: e]], dtype='float')

    def find_players(self, lst: List[str]) -> Dict[str, Player]:
        players = [make_player(s) for s in lst[2:2 + self.MaxPlayers] if 'Seat' in s]
        return {pl.ID: pl for pl in players}

    def add_blinds_and_ante(self, lst):
        first_line = 2 + self.NPlayers
        self.AtLine = next(i for i in range(first_line, 2 * self.NPlayers + 5) if lst[i] == '*** HOLE CARDS ***')
        for s in lst[first_line:self.AtLine]:
            i, v = s[:s.find(':')], float(s[s.find(CURRENCY) + 1:])
            if 'ante' in s:
                self.Players[i].set_ante(v)
            elif 'small blind' in s:
                self.Players[i].set_small_blind(v)
            elif 'big blind' in s:
                self.Players[i].set_big_blind(v)

    def add_hole_cards(self, lst):
        fl = self.AtLine + 1
        for s in lst[fl:fl + self.NPlayers]:
            pos = s.find('[')
            if pos == -1:
                continue
            i, v = s[s.find('to') + 3:pos - 1], s[pos + 1:-1].split()
            self.Players[i].set_hole_cards(v)
        self.AtLine += self.NPlayers

    def summarise(self, lst):
        s = lst[self.AtLine + 1]
        self.Players[s[:s.find(' ')]].set_value(float(s[s.find(CURRENCY) + 1:s.find('from') - 1]))
        data = lst[self.AtLine + 3].split('|')
        self.Rake = float(data[1][data[1].find(CURRENCY) + 1:])
        self.Jackpot = float(data[2][data[2].find(CURRENCY) + 1:])
        for s, pl in zip(lst[self.AtLine + 5:], self.Players.values()):
            if '[' in s:
                pl.set_hole_cards(s[s.find('[') + 1:s.find(']')].split())

    def show_players(self):
        header = ['ID', 'Position', 'Hand', '\b' * 5 + 'Value']
        rows = [[pl.ID, pl.Position, f'[{" ".join(pl.HoleCards)}]', pl.value_str] for pl in self.Players.values()]
        print_table(rows, header, form=['l', 'l', 'l', 'r'])
