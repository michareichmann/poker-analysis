CURRENCY = '$'


class Action:

    def __init__(self, pid, value=0.):

        self.PlayerID = pid
        self.Value = value

    def __repr__(self):
        return f'{self.PlayerID} {self.__class__.__name__.lower()}s'

    @property
    def value_str(self):
        return f'{CURRENCY}{self.Value:.2f}'


class Fold(Action):
    ...


class Call(Action):

    def __repr__(self):
        return f'{super().__repr__()} {self.value_str}'


class Raise(Action):

    def __repr__(self):
        return f'{super().__repr__()} to {self.value_str}'


class Bet(Action):

    def __repr__(self):
        return f'{super().__repr__()} {self.value_str}'


class Check(Action):
    ...
