from src.data import Hand, List, pd


class PlayerStats(pd.DataFrame):
    """ Statistics for a single player. """

    MainCols = ['Limits', 'Value', 'Pot', 'Position', 'NPlayers']
    StatDict = {'AF': 'Agression Faction',
                'WTS': 'Went to Showdown',
                'PFR': 'Preflop Raise',
                'ATS': 'Attempt to Steal',
                '3b': '3-bet',
                'f3b/c3b': 'Fold to 3-bet / Call 3-bet',
                'Cbet': 'Continuation Bet',
                'fCb': 'Fold to Cbet',
                'Dbet': 'Donk Bet'}
    StatCols = list(StatDict)
    Cols = MainCols + StatCols

    def __init__(self, id_: int):

        self.ID = id_
        self.Name = None
        super().__init__(data={col: [] for col in PlayerStats.Cols})


class Stats(pd.DataFrame):
    """ All stats. """

    PlayerIDs = []

    def __init__(self):
        super().__init__(data={'PlayerID': [], 'Name': [], 'NHands': []})

    def save(self):
        """ save the dataframe as feather """

    def fill(self, lst: List[Hand]):
        """ loop over a list of Hands and calculate statistics."""

