from src.action import *


class Street:

    Cards = []
    Actions = []
    LastLine = 0
    MaxRuns = 4

    def __init__(self, hand, lst):

        self.MultiDeal = False

        lst_ = lst[hand.AtLine:]
        if self.exists(lst_):
            self.Cards = self.find_all_cards(lst_)
            self.LastLine = next(i for i in range(1, len(lst_)) if lst_[i][:3] == '***')
            self.Actions = self.find_actions(hand, lst_[:self.LastLine])
        hand.AtLine += self.LastLine

    def __add__(self, other: 'Street'):
        return self.Cards + (other.Cards if isinstance(other, Street) else other)

    def __radd__(self, other: 'Street'):
        return (other.Cards if isinstance(other, Street) else other) + self.Cards

    def __repr__(self):
        return f'[{" ".join(self.Cards)}]' if self.Cards else f'There is no {self.__class__.__name__.lower()}'

    def exists(self, lst):
        if lst[0].startswith(f'*** {self.__class__.__name__.upper()}'):
            return True
        if lst[0].startswith(f'*** FIRST {self.__class__.__name__.upper()}'):
            self.MultiDeal = True
            return True
        return False

    @staticmethod
    def find_actions(hand, lst):
        ret = []
        for s in lst:
            i, v = s[:s.find(':')], 0
            if 'fold' in s:
                ret.append(Fold(i))
            elif 'checks' in s:
                ret.append(Check(i))
            elif 'Uncalled' in s:
                v = float(s[s.find(CURRENCY) + 1:s.find(')')])
                hand.Pot[-1] -= v
                hand.Players[s[s.find('to') + 3:]].Investment -= v
                break
            for word, action in [('call', Call), ('bets', Bet), ('raise', Raise)]:
                if word in s:
                    pos = s.find(' and')
                    if pos != -1:
                        hand.Players[i].push_all_in()
                    start = s.find('to') + 4 if word == 'raise' else s.find(CURRENCY) + 1
                    v = float(s[start:] if pos == -1 else s[start:pos])
                    ret.append(action(i, v))
                    hand.Players[i].Investment += v
                    hand.Pot.append(v + hand.Pot[-1])
                    break
        return ret

    def find_all_cards(self, lst):
        if not self.MultiDeal:
            return self.find_cards(lst[0])
        return sum([self.find_cards(line) for line in filter(lambda x: self.__class__.__name__.upper() in x, lst[:2 * Street.MaxRuns])], start=[])

    def find_cards(self, s):
        return s[-9:-1].split()


class PreFlop(Street):

    def exists(self, lst):
        return True

    def find_cards(self, s):
        return []

    def __repr__(self):
        return '\n'.join(f'{a!r}' for a in self.Actions)


class Flop(Street):
    ...


class Turn(Street):

    def find_cards(self, s):
        return [s[-3:-1]]


class River(Street):

    def __init__(self, hand, lst):
        super().__init__(hand, lst)
        if self.MultiDeal:
            hand.AtLine += len(hand.Flop.Cards) // 3 + len(hand.Turn.Cards) + len(self.Cards) - 3

    def find_cards(self, s):
        return [s[-3:-1]]
