import pickle
from typing import Dict

from src.data import Hand, List, pd, Player, Data
from utils.helpers import load_pickle, remove_file
from src.action import *


class PlayerStats(pd.DataFrame):
    """ Statistics for a single player. """

    MainCols = ['Limits', 'NPlayers', 'Pot', 'Value', 'Position']
    StatDict = {'VPIP': 'Voluntarily Put $ In Pot',
                'PFR': 'Preflop Raise',
                'ATS': 'Attempt to Steal (Open raise from late position (CO, BUT, SB)',
                'FTS': 'Fold to Steal',
                '3b': '3-bet',
                'f3b': 'Fold to 3-bet',
                'c3b': 'Call 3-bet',
                'Cbet': 'Continuation Bet',
                'fCb': 'Fold to Cbet',
                'Dbet': 'Donk Bet',
                'WTS': 'Went to Showdown when on flop'}
    StatCols = list(StatDict)
    Cols = MainCols + StatCols

    def __init__(self, id_: str):

        super().__init__(data={col: [] for col in PlayerStats.Cols})
        self.ID = id_
        self.Name = None

    @property
    def ncols(self) -> int:
        return self.shape[1]

    @property
    def nrows(self) -> int:
        return self.shape[0]

    def __lt__(self, other: 'PlayerStats'):
        return self.nrows < other.nrows

    def add_line(self, vals):
        self.loc[self.shape[0]] = vals


class AllPlayerStats(dict):
    """ List of all PlayerStats. """

    FileName = Data.Dir.joinpath('player_stats.pickle')

    def __init__(self):
        super().__init__(self.load())

    @staticmethod
    def load() -> Dict[str, PlayerStats]:
        if AllPlayerStats.FileName.exists():
            return load_pickle(AllPlayerStats.FileName)
        return {}

    def save(self):
        remove_file(AllPlayerStats.FileName)
        with open(AllPlayerStats.FileName, 'wb') as f:
            pickle.dump(self, f)

    def create_player(self, pl: Player):
        self[pl.ID] = PlayerStats(pl.ID)

    def add_hand(self, hand: Hand):
        main = [hand.limit_str, hand.NPlayers, hand.Pot[-1]]

        self.add_preflop(hand)
        self.add_flop(hand)
        self.add_turn(hand)
        self.add_river(hand)

        for pl in hand.Players.values():
            if pl.ID not in self:
                self.create_player(pl)
            self[pl.ID].add_line(main + [pl.net, pl.Position] + pl.Stats)

    @staticmethod
    def add_preflop(hand: Hand):
        raised, reraised = False, False
        ats = False
        for act in hand.PreFlop.Actions:
            # default stats are for fold -> ignore folds and checks
            pos = hand.Players[act.PlayerID].Position
            st = hand.Players[act.PlayerID].Stats
            if isinstance(act, Raise):
                st.set_vpip()
                st.set_pfr()
                if not raised:
                    if pos in ['SB', 'CO', 'BUT']:
                        st.set_ats(True)
                        ats = True
                else:
                    st.set_3bet(True)
                    reraised = True
                    if ats and pos != 'BUT':
                        st.set_fts(False)
                raised = True
            elif isinstance(act, Fold):
                if ats and not reraised and pos != 'BUT':
                    st.set_fts(True)
                if raised and not reraised:
                    st.set_3bet(False)
                elif not raised and pos in ['SB', 'CO', 'BUT']:
                    st.set_ats(False)
                elif reraised and st.pfr:
                    st.set_f3b(True)
            elif isinstance(act, Call):
                st.set_vpip()
                if ats and not reraised and pos != 'BUT':
                    st.set_fts(False)
                if raised and not reraised:
                    st.set_3bet(False)
                elif reraised and st.pfr:
                    st.set_c3b(True)

    @staticmethod
    def add_flop(hand: Hand):
        ...

    @staticmethod
    def add_turn(hand: Hand):
        ...

    @staticmethod
    def add_river(hand: Hand):
        ...


class Stats(pd.DataFrame):
    """ Mean stats of all players. """

    FileName = Data.Dir.joinpath('stats.pickle')

    def __init__(self):
        super().__init__(data={'PlayerID': [], 'Name': [], 'NHands': []})
        self.PlayerStats = self.load()

    @staticmethod
    def load():
        if Stats.FileName.exists():
            return load_pickle(Stats.FileName)

    def save(self):
        """ save the dataframe as feather """

    def fill(self, lst: List[Hand]):
        """ loop over a list of Hands and calculate statistics."""

