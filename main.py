from src.data import *


if __name__ == '__main__':

    d = Data()
    x = Hand(d.load_file()[0])
    h = x.Players['Hero']