#!/usr/bin/env python3
# quarto.py
# Author: Quentin Lurkin
# Version: March 29, 2018

import argparse
import socket
import sys
import random
from random import randint
import json

from lib import game


class QuartoState(game.GameState):
    '''Class representing a state for the Quarto game.'''

    def __init__(self, initialstate=None):
        self.__player = 0
        random.seed()
        if initialstate is None:
            pieces = []
            for shape in ['round', 'square']:
                for color in ['dark', 'light']:
                    for height in ['low', 'high']:
                        for filling in ['empty', 'full']:
                            pieces.append({
                                'shape': shape,
                                'color': color,
                                'height': height,
                                'filling': filling
                            })
            initialstate = {
                'board': [None] * 16,
                'remainingPieces': pieces,
                'pieceToPlay': None,
                'quartoAnnounced': False
            }

        super().__init__(initialstate)

    def setPlayer(self, player):
        self.__player = player

    def applymove(self, move):
        # {pos: 8, quarto: true, nextPiece: 2}
        state = self._state['visible']
        # first step, place the piece that has been chosen by other player
        if state['pieceToPlay'] is not None:
            try:
                if state['board'][move['pos']] is not None:
                    raise game.InvalidMoveException('The position is not free')
                # state remaining piece = list of the remaining pieces
                state['board'][move['pos']] = state['remainingPieces'][state['pieceToPlay']]
                del (state['remainingPieces'][state['pieceToPlay']])
            except game.InvalidMoveException as e:
                raise e
            except:
                raise game.InvalidMoveException("Your move should contain a \"pos\" key in range(16)")

        # choose a piece player to will have to play
        try:
            state['pieceToPlay'] = move['nextPiece']
        except:
            raise game.InvalidMoveException("You must specify the next piece to play")

        if 'quarto' in move:
            state['quartoAnnounced'] = move['quarto']
            winner = self.winner()
            if winner is None or winner == -1:
                raise game.InvalidMoveException("There is no Quarto !")
        else:
            state['quartoAnnounced'] = False

    def _same(self, feature, elems):

        try:
            elems = list(map(lambda piece: piece[feature], elems))
        except:
            return False
        print('SAME:\nelems: {}\nfeature: {}'.format(elems, feature))
        return all(e == elems[0] for e in elems)

    def _quarto(self, elems):
        return self._same('shape', elems) or self._same('color', elems) or self._same('filling', elems) or self._same(
            'height', elems)

    def winner(self):
        state = self._state['visible']
        board = state['board']
        player = self.__player

        # 00 01 02 03
        # 04 05 06 07
        # 08 09 10 11
        # 12 13 14 15

        if state['quartoAnnounced']:
            # Check horizontal and vertical lines
            for i in range(4):
                if self._quarto([board[4 * i + e] for e in range(4)]):
                    return player
                if self._quarto([board[4 * e + i] for e in range(4)]):
                    return player
            # Check diagonals
            if self._quarto([board[5 * e] for e in range(4)]):
                return player
            if self._quarto([board[3 + 3 * e] for e in range(4)]):
                return player
        return None if board.count(None) == 0 else -1

    def displayPiece(self, piece):
        if piece is None:
            return " " * 6
        bracket = ('(', ')') if piece['shape'] == "round" else ('[', ']')
        filling = 'E' if piece['filling'] == 'empty' else 'F'
        color = 'L' if piece['color'] == 'light' else 'D'
        format = ' {}{}{}{} ' if piece['height'] == 'low' else '{0}{0}{1}{2}{3}{3}'
        return format.format(bracket[0], filling, color, bracket[1])

    def prettyprint(self):
        state = self._state['visible']
        for row in range(4):
            print('|', end="")
            for col in range(4):
                print(self.displayPiece(state['board'][row * 4 + col]), end="|")
            print()

        print(", ".join([self.displayPiece(piece) for piece in state['remainingPieces']]))


class QuartoServer(game.GameServer):
    '''Class representing a server for the Quarto game.'''

    def __init__(self, verbose=False):
        super().__init__('Quarto', 2, QuartoState(), verbose=verbose)

    def applymove(self, move):
        try:
            move = json.loads(move)
        except:
            raise game.InvalidMoveException('A valid move must be a valid JSON string')
        else:
            self._state.setPlayer(self.currentplayer)
            self._state.applymove(move)


class QuartoAI(game.GameClient):
    '''Class representing a client for the Quarto game.'''

    def __init__(self, name, server, verbose=False):
        super().__init__(server, QuartoState, verbose=verbose)
        self.__name = name

    def _handle(self, message):
        pass

    def _nextmove(self, state):
        def _read(board):
            dicoRead = {}
            for i in range(len(board)):
                dicoRead[i] = board[i]
            return dicoRead

        visible = state._state['visible']
        move = {}

        remainingPieces = visible['remainingPieces']
        x = len(remainingPieces)
        piecetoplay = visible['pieceToPlay']

        """boardfeature = {"rows": {1: [0, 1, 2, 3], 2: [4, 5, 6, 7], 3: [8, 9, 10, 11], 4: [12, 13, 14, 15]},
                        "colons": {'a': [0, 4, 8, 12], 'b': [1, 5, 9, 13], 'c': [2, 6, 10, 14], 'd': [3, 7, 11, 15]},
                        "diagonals": {"A": [0, 5, 10, 15], 'B': [3, 6, 9, 12]}
                        }"""

        boardfeature = {0: {"row": {1: [1, 2, 3]}, "colons": {1: [4, 8, 12]}, "diagonals": {1: [5, 10, 15]}},
                        1: {"row": {1: [0, 2, 3]}, "colons": {2: [5, 9, 13]}, "diagonals": None},
                        2: {"row": {1: [0, 1, 3]}, "colons": {3: [6, 10, 14]}, "diagonals": None},
                        3: {"row": {1: [0, 1, 2]}, "colons": {4: [7, 11, 15]}, "diagonals": {2: [6, 9, 12]}},
                        4: {"row": {2: [5, 6, 7]}, "colons": {1: [0, 8, 12]}, "diagonals": None},
                        5: {"row": {2: [4, 6, 7]}, "colons": {2: [1, 9, 13]}, "diagonals": {1: [0, 10, 15]}},
                        6: {"row": {2: [4, 5, 7]}, "colons": {3: [2, 10, 14]}, "diagonals": {2: [3, 9, 12]}},
                        7: {"row": {2: [4, 5, 6]}, "colons": {4: [3, 11, 15]}, "diagonals": None},
                        8: {"row": {3: [9, 10, 11]}, "colons": {1: [0, 4, 12]}, "diagonals": None},
                        9: {"row": {3: [8, 10, 11]}, "colons": {2: [1, 5, 13]}, "diagonals": {2: [3, 6, 12]}},
                        10: {"row": {3: [8, 9, 11]}, "colons": {3: [2, 6, 14]}, "diagonals": {1: [0, 5, 15]}},
                        11: {"row": {3: [8, 9, 10]}, "colons": {4: [3, 7, 15]}, "diagonals": None},
                        12: {"row": {4: [13, 14, 15]}, "colons": {1: [0, 4, 8]}, "diagonals": {2: [3, 6, 9]}},
                        13: {"row": {4: [12, 14, 15]}, "colons": {2: [1, 5, 9]}, "diagonals": None},
                        14: {"row": {4: [12, 13, 15]}, "colons": {3: [2, 6, 10]}, "diagonals": None},
                        15: {"row": {4: [12, 13, 14]}, "colons": {4: [3, 7, 11]}, "diagonals": {1: [0, 5, 10]}}
                        }

        # select next piece to play if you are first to play
        if visible['pieceToPlay'] is None:
            move['nextPiece'] = randint(0, x - 1)

        # select a free position
        if visible['pieceToPlay'] is not None:
            # first turn of the game, AI places the first piece on the game
            if x == 16:
                move['pos'] = randint(0, 15)
                move['nextPiece'] = randint(0, x - 1)
                '''move['pos'] = visible['board'].index(None)'''
            # second turn of the game
            if x == 15:
                posPiece = 0

                def nbrcara(para):
                    # for i in remainingPieces[int(str(piecetoplay))]:
                    for data in para.values():
                        if data is not None:
                            print(_read(visible['board']))
                            print(data)
                            print(remainingPieces[int(str(piecetoplay))])
                            keys_a = set(data.values())
                            keys_b = set(remainingPieces[int(str(piecetoplay))].values())
                            intersection = keys_a & keys_b
                            nombre = len(intersection)
                            print(intersection)
                            print(nombre)
                            return nombre

                for i in range(16):
                    if visible['board'][i] is not None:
                        posPiece = i
                print(posPiece)

                def posliste(pos):
                    # {"row": {1: [1, 2, 3]}, "colons": {1: [4, 8, 12]}, "diagonals": {1: [5, 10, 15]}}
                    allignement = []
                    posdic1 = boardfeature[pos]["row"].values()
                    posdic2 = boardfeature[pos]["colons"].values()
                    if boardfeature[pos]["diagonals"].value() is not None:
                        posdic3 = boardfeature[pos]["diagonals"].value()
                        allignement.append(posdic3)
                    else:
                        posdic3 = []
                        allignement.append(posdic3)
                    allignement.append(posdic1)
                    allignement.append(posdic2)
                    return allignement

                boarddata = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

                if nbrcara(_read(visible['board'])) < 2:
                    list = set(boarddata) - set(posliste(posPiece))
                    move['pos'] = random.choice(list)
                    move['nextPiece'] = randint(0, x - 1)

                else:
                    move['pos'] = randint(posliste(posPiece))
                    move['nextPiece'] = randint(0, x - 1)

        # apply the move to check for quarto
        # applymove will raise if we announce a quarto while there is not
        move['quarto'] = True
        try:
            state.applymove(move)
        except:
            del (move['quarto'])

        # send the move
        return json.dumps(move)


class QuartoPlayer(game.GameClient):
    '''Class representing a client for the Quarto game.'''

    def __init__(self, name, server, verbose=False):
        super().__init__(server, QuartoState, verbose=verbose)
        self.__name = name

    def _handle(self, message):
        pass

    def displayPiece(self, piece):
        if piece is None:
            return " " * 6
        bracket = ('(', ')') if piece['shape'] == "round" else ('[', ']')
        filling = 'E' if piece['filling'] == 'empty' else 'F'
        color = 'L' if piece['color'] == 'light' else 'D'
        format = ' {}{}{}{} ' if piece['height'] == 'low' else '{0}{0}{1}{2}{3}{3}'
        return format.format(bracket[0], filling, color, bracket[1])

    def _nextmove(self, state):
        visible = state._state['visible']
        move = {}

        remainingPieces = visible['remainingPieces']
        piecetoPlay = visible['pieceToPlay']

        # print piece to play and remainingpieces
        print('\npieceToPlay:', self.displayPiece(remainingPieces[int(str(piecetoPlay))]),
              '\n\nremainingPieces:', (", ".join([self.displayPiece(piece) for piece in remainingPieces])), '\n')

        # select the first free position
        if visible['pieceToPlay'] is not None:
            move['pos'] = int(input('Position: '))

        # select the first remaining piece
        move['nextPiece'] = int(input('Next Piece: '))

        # apply the move to check for quarto
        # applymove will raise if we announce a quarto while there is not
        move['quarto'] = True
        try:
            state.applymove(move)

        except:
            del (move['quarto'])

        # send the move
        return json.dumps(move)


if __name__ == '__main__':
    # Create the top-level parser
    parser = argparse.ArgumentParser(description='Quarto game')
    subparsers = parser.add_subparsers(description='server client', help='Quarto game components', dest='component')
    # Create the parser for the 'server' subcommand
    server_parser = subparsers.add_parser('server', help='launch a server')
    server_parser.add_argument('--host', help='hostname (default: localhost)', default='localhost')
    server_parser.add_argument('--port', help='port to listen on (default: 5000)', default=5000)
    server_parser.add_argument('--verbose', action='store_true')
    # Create the parser for the 'client' subcommand
    player_parser = subparsers.add_parser('player', help='launch a client')
    player_parser.add_argument('name', help='name of the player')
    player_parser.add_argument('--host', help='hostname of the server (default: localhost)', default='127.0.0.1')
    player_parser.add_argument('--port', help='port of the server (default: 5000)', default=5000)
    player_parser.add_argument('--verbose', action='store_true')
    # Create the parser for the 'clientAI' subcommand
    AI_parser = subparsers.add_parser('AI', help='launch a client')
    AI_parser.add_argument('name', help='name of the player')
    AI_parser.add_argument('--host', help='hostname of the server (default: localhost)', default='127.0.0.1')
    AI_parser.add_argument('--port', help='port of the server (default: 5000)', default=5000)
    AI_parser.add_argument('--verbose', action='store_true')
    # Parse the arguments of sys.args
    args = parser.parse_args()
    if args.component == 'server':
        QuartoServer(verbose=args.verbose).run()
    elif args.component == 'AI':
        QuartoAI(args.name, (args.host, args.port), verbose=args.verbose)
    else:
        QuartoPlayer(args.name, (args.host, args.port), verbose=args.verbose)
