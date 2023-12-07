from src.action import *


class Street:

    Cards = []
    Actions = []
    LastLine = 0

    def __init__(self, hand, lst):

        lst_ = lst[hand.AtLine:]
        if self.exists(lst_):
            self.Cards = self.find_cards(lst_[0])
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
        return lst[0].startswith(f'*** {self.__class__.__name__.upper()}')

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

    def find_cards(self, s):
        return s[14:-1].split()


class PreFlop(Street):

    def exists(self, lst):
        return True

    def find_cards(self, s):
        return []


class Flop(Street):
    ...


class Turn(Street):

    def find_cards(self, s):
        return [s[-3:-1]]


class River(Street):

    def find_cards(self, s):
        return [s[-3:-1]]