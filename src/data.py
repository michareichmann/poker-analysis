from utils.helpers import Dir, print_table, colored, info
from utils.classes import PBAR, update_pbar
import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime
from src.street import *
from zipfile import ZipFile, ZipInfo


POSITIONS = ['UTG1', 'UTG2', 'UTG3', 'MP1', 'MP2', 'MP3', 'CO', 'BUT', 'SB', 'BB']


class Data:

    Dir = Dir.joinpath('data')

    def __init__(self):

        self.Hands = self.load_hands()

    @staticmethod
    def find_zip_files():
        return [ZipFile(p) for p in Data.Dir.glob('*.zip')]

    @staticmethod
    def read_zip_file(f: ZipFile):
        d = np.concatenate([Data.get(f, zf) for zf in f.filelist]).flatten()
        nan_inds = np.arange(d.size, dtype='i')[pd.isnull(d)]
        d = np.delete(d, nan_inds)  # remove nan values
        return np.split(d, np.unique(nan_inds - np.arange(nan_inds.size))[:-1])

    @staticmethod
    @update_pbar
    def get(f: ZipFile, zf: ZipInfo):
        return pd.read_csv(f.open(zf), sep='\t', header=None, skip_blank_lines=False)

    def load_hands(self):
        f = self.find_zip_files()[0]
        info('Reading zip files ...')
        PBAR.start(len(f.filelist))
        return sorted([Hand(data) for data in self.read_zip_file(f)])


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
        self.Straddle = 0.
        self.Investment = 0.
        self.Value = 0.
        self.IsAllIn = False

    def __repr__(self):
        return f'Player {self.ID} ({self.Position})'

    def __lt__(self, other: 'Player'):
        p0, p1 = [range(len(POSITIONS))[POSITIONS.index(p)] for p in [self.Position, other.Position]]
        return p0 <= p1

    @property
    def committment(self):
        return self.Ante + self.SB + self.BB + self.Straddle + self.Investment

    @property
    def net_str(self):
        v = self.net
        return colored(f'{CURRENCY}{v:.2f}', 'red' if v < 0 else None if v == 0 else 'green')

    @property
    def net(self):
        return self.Value - self.committment

    def set_ante(self, v: float):
        self.Ante = v

    def set_small_blind(self, v: float):
        self.SB = v

    def set_big_blind(self, v: float):
        self.BB = v

    def set_straddle(self, v: float):
        self.Straddle = v

    def set_hole_cards(self, s: List[str]):
        self.HoleCards = s

    def add_value(self, v: float):
        self.Value += v

    def push_all_in(self):
        self.IsAllIn = True


class Hero(Player):
    ...


def make_player(s: str):
    return Hero(s) if 'Hero' in s else Player(s)


class Hand:

    def __init__(self, lst: List[str]):

        self.NLines = len(lst)
        self.AtLine = 0

        fl = lst[0]  # first line

        self.Number = fl[fl.find('#'):fl.find(':')]
        self.Type = fl[fl.find(':') + 2:fl.find('(') - 1]
        self.Limits = self.find_limits(fl)
        self.Date = datetime.strptime(fl[fl.find('-') + 2:], '%Y/%m/%d %H:%M:%S')

        sl = lst[1]  # second line
        fa = sl.find('\'') + 1
        self.Table = sl[fa:sl.find('\'', fa)]
        self.MaxPlayers = int(sl[sl.find('\'', fa) + 2:sl.find('-')])
        self.Button = 0
        self.Players = self.find_players(lst)
        self.NPlayers = len(self.Players)
        self.add_blinds_and_ante(lst)
        self.find_positions()
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

    def __lt__(self, other: 'Hand'):
        return self.Number < other.Number

    @property
    def pot(self):
        return sum(pl.committment for pl in self.Players.values())

    def find_positions(self):
        for pos, pl in zip(np.roll(POSITIONS[-self.NPlayers:], self.Button + 3), self.Players.values()):
            pl.Position = pos

    @staticmethod
    def find_limits(fl: str):
        b, m, e = fl.find('(') + 2, fl.find('/'), fl.find(')')
        return np.array([fl[b:m], fl[m + 2: e]], dtype='float')

    def find_players(self, lst: List[str]) -> Dict[str, Player]:
        players = [make_player(s) for s in lst[2:2 + self.MaxPlayers] if 'Seat' in s]
        return {pl.ID: pl for pl in players}

    def add_blinds_and_ante(self, lst):
        for i in range(2 + self.NPlayers, self.NLines):
            s = lst[i]
            if s.startswith('*'):
                self.AtLine = i
                break

            id_ = s[:s.find(':')]
            pos = s.find(' and')
            if pos != -1:
                s = s[:pos]
                self.Players[id_].push_all_in()
            v = float(s[s.find(CURRENCY) + 1:])

            if 'ante' in s:
                self.Players[id_].set_ante(v)
            elif 'small blind' in s:
                self.Button = list(self.Players).index(id_) - 1
                self.Button += self.NPlayers if self.Button < 0 else 0
                self.Players[id_].set_small_blind(v)
            elif 'big blind' in s:
                self.Players[id_].set_big_blind(v)
            elif 'straddle' in s:
                self.Players[id_].set_straddle(v)

    def add_hole_cards(self, lst):
        fl = self.AtLine + 1
        for s in lst[fl:fl + self.NPlayers]:
            pos = s.find('[')
            if pos == -1:
                continue
            i, v = s[s.find('to') + 3:pos - 1], s[pos + 1:-1].split()
            self.Players[i].set_hole_cards(v)
        self.AtLine += self.NPlayers + 1

    def summarise(self, lst):
        self.AtLine += 1
        if self.River.MultiDeal:
            for s in lst[self.AtLine:self.AtLine + len(self.River.Cards) * 2:2]:
                self.Players[s[:s.find(' ')]].add_value(float(s[s.find(CURRENCY) + 1:s.find('from') - 1]))
                self.AtLine += 2
        else:
            s = lst[self.AtLine]
            while 'collected' in s:
                self.Players[s[:s.find(' ')]].add_value(float(s[s.find(CURRENCY) + 1:s.find('from') - 1]))
                self.AtLine += 1
                s = lst[self.AtLine]
            self.AtLine += 1
        data = lst[self.AtLine].split('|')
        self.Rake = float(data[1][data[1].find(CURRENCY) + 1:])
        self.Jackpot = float(data[2][data[2].find(CURRENCY) + 1:])
        for s, pl in zip(lst[self.AtLine + 2:], self.Players.values()):
            if '[' in s:
                pl.set_hole_cards(s[s.find('[') + 1:s.find(']')].split())

    def show_players(self):
        header = ['ID', 'Position', 'Hand', '\b' * 5 + 'Value']
        rows = [[pl.ID, pl.Position, f'[{" ".join(pl.HoleCards)}]', pl.net_str] for pl in sorted(self.Players.values())]
        print_table(rows, header, form=['l', 'l', 'l', 'r'])

    def print_actions(self):
        for s in self.Streets:
            print_small_banner(f'{s}: {s.card_str}', color='green')
            print(f'{s.action_str}\n')

