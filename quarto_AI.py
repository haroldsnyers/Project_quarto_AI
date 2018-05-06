#!/usr/bin/env python3
# quarto.py
# Server
# Author: Quentin Lurkin
# Version: March 29, 2018
# client AI and player
# Author: Harold Snyers & Alexandre Seynaeve
# version:

import argparse
import socket
import sys
import random
from random import randint
import json
import copy

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
        # gives a dictionary containing all the position on the board with their state, state stands here for if the
        # position is free. If it's free, then the state = None otherwise we have the characteristics of the piece
        def _read(board):
            dicoRead = {}
            for i in range(len(board)):
                dicoRead[i] = board[i]
            return dicoRead

        # determines on which position the piece is on the board
        def token():
            link = []
            for i in range(16):
                if visible['board'][i] is not None:
                    link.append(i)
            return link

        # determines on which position the piece are not on the board
        def nottoken():
            notlink = []
            for i in range(16):
                if visible['board'][i] is None:
                    notlink.append(i)
            return notlink

        visible = state._state['visible']
        move = {}
        piecetoplay = visible['pieceToPlay']
        remainingPieces = visible['remainingPieces']
        x = len(remainingPieces)

        # structure for each position on the board
        boardfeature = {0: {"row": [1, 2, 3], "colons": [4, 8, 12], "diagonals": [5, 10, 15]},
                        1: {"row": [0, 2, 3], "colons": [5, 9, 13], "diagonals": []},
                        2: {"row": [0, 1, 3], "colons": [6, 10, 14], "diagonals": []},
                        3: {"row": [0, 1, 2], "colons": [7, 11, 15], "diagonals": [6, 9, 12]},
                        4: {"row": [5, 6, 7], "colons": [0, 8, 12], "diagonals": []},
                        5: {"row": [4, 6, 7], "colons": [1, 9, 13], "diagonals": [0, 10, 15]},
                        6: {"row": [4, 5, 7], "colons": [2, 10, 14], "diagonals": [3, 9, 12]},
                        7: {"row": [4, 5, 6], "colons": [3, 11, 15], "diagonals": []},
                        8: {"row": [9, 10, 11], "colons": [0, 4, 12], "diagonals": []},
                        9: {"row": [8, 10, 11], "colons": [1, 5, 13], "diagonals": [3, 6, 12]},
                        10: {"row": [8, 9, 11], "colons": [2, 6, 14], "diagonals": [0, 5, 15]},
                        11: {"row": [8, 9, 10], "colons": [3, 7, 15], "diagonals": []},
                        12: {"row": [13, 14, 15], "colons": [0, 4, 8], "diagonals": [3, 6, 9]},
                        13: {"row": [12, 14, 15], "colons": [1, 5, 9], "diagonals": []},
                        14: {"row": [12, 13, 15], "colons": [2, 6, 10], "diagonals": []},
                        15: {"row": [12, 13, 14], "colons": [3, 7, 11], "diagonals": [0, 5, 10]}
                        }

        # select next piece to play if you are first to play
        # first to play means, choose the first piece which will be played and that he is player 1
        if visible['pieceToPlay'] is None:
            move['nextPiece'] = randint(0, x - 1)

        if visible['pieceToPlay'] is not None:
            # There are no pieces on the board
            # AI is playing second, he is the first one to place a piece on the board and he is player 2
            if x == 16:
                move['pos'] = randint(0, 15)
                move['nextPiece'] = randint(0, x - 1)

            # 1 piece is already on board.
            # move for player 1
            if x == 15:
                posPiece = 0

                def posliste(pos):
                    # makes a list of all the positions related to the position of piece already laying on the board
                    alignment = []
                    posdic1 = boardfeature[pos]["row"]
                    posdic2 = boardfeature[pos]["colons"]
                    posdic3 = boardfeature[pos]["diagonals"]
                    for elem in posdic1:
                        alignment.append(elem)
                    for elem in posdic2:
                        alignment.append(elem)
                    for elem in posdic3:
                        alignment.append(elem)
                    return alignment

                def nbrcara(para, piece):
                    # returns the number of common characteristics between 2 pieces
                    # This function is when para is a dictionary of dictionaries
                    for data in para.values():
                        if data is not None:
                            keys_a = set(data.values())
                            keys_b = set(piece.values())
                            intersection = keys_a & keys_b
                            nombre = len(intersection)
                            return nombre

                def nbrcara1(piece, data):
                    # Returns the number of common characteristics between 2 pieces
                    # This function is when piece is just a dictionary
                    keys_a = set(piece.values())
                    keys_b = set(data.values())
                    intersection = keys_a & keys_b
                    nombre = len(intersection)
                    return nombre

                # determines on which position the piece is on the board
                for i in range(16):
                    if visible['board'][i] is not None:
                        posPiece = i
                    print("this is pospiece" +str(posPiece))

                def listpiece(nbr1, nbr2):
                    # returns a list of all the possibilities which satisfy the conditions for the nextpiece to play
                    nextpieces =[]
                    i = 0
                    remainingPieces_copy = copy.deepcopy(remainingPieces)
                    remainingPieces_copy.remove(remainingPieces[piecetoplay])
                    for piece in remainingPieces_copy:
                        if nbrcara1(piece, remainingPieces[int(str(piecetoplay))]) == nbr1:
                            if nbr2+1 >= nbrcara(_read(visible['board']), piece) >= nbr2:
                                nextpieces.append(i)
                        i += 1
                    return nextpieces

                # all the positions possible on the board
                boarddata = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

                # making a choice in function of the number of common characteristics
                if nbrcara(_read(visible['board']), remainingPieces[int(str(piecetoplay))]) < 2:
                    possibilities = list(filter(lambda x: x not in posliste(posPiece), boarddata))
                    print("pos is" + str(possibilities))
                    move['pos'] = random.choice(possibilities)
                    # number of common characteristics equals 0
                    if nbrcara(_read(visible['board']), remainingPieces[int(str(piecetoplay))]) == 0:
                        # will choose a piece which will have 3 common characteristics with the last piece played and
                        # 1 or 2 with the piece which was first played
                        print("this is listpiece(3, 1)" + str(listpiece(3, 1)))
                        move['nextPiece'] = random.choice(listpiece(3, 1))
                    # number of common characteristics equals 1
                    else:
                        # will choose a piece which will have 2 common characteristics with the last piece played and
                        # 1 or 2 with the piece which was first played
                        print("this is listpiece(2, 1)" + str(listpiece(2, 1)))
                        move['nextPiece'] = random.choice(listpiece(2, 1))

                else:

                    print("posliste" + str(posliste(posPiece)))
                    move['pos'] = random.choice(posliste(posPiece))
                    # number of common characteristics equals 2
                    if nbrcara(_read(visible['board']), remainingPieces[int(str(piecetoplay))]) == 2:
                        # will choose a piece which will have 1 common characteristics with the last piece played and
                        # 0 or 1 with the piece which was first played or the contrary
                        print("this is listpiece(1, 0)" +str(listpiece(1, 0)))
                        move['nextPiece'] = random.choice(listpiece(1, 0) or listpiece(0, 1))
                    # number of common characteristics equals 3
                    else:
                        # will choose a piece which will have 2 common characteristics with the last piece played and
                        # 2 or 3 with the piece which was first played
                        print("this is listpiece(2, 2)" + str(listpiece(2, 2)))
                        move['nextPiece'] = random.choice(listpiece(2, 2))

            # 2 pieces already on the board
            # move for player 2
            if x == 14:

                boarddata2 = nottoken()  # boarddata changes in the current of the game

                def posliste(pos):
                    # returns a list of lists
                    # (result = [all the positions in alignment to at least one of the positions of the pieces on the
                    # board, , all the positions in alignment with the 2 pieces on the board, all the positions in
                    # alignment with just 1 piece on the board)
                    alignment = []
                    alignmentbis = []
                    arrangement = []
                    for data in pos:
                        posdic1 = boardfeature[data]["row"]
                        posdic2 = boardfeature[data]["colons"]
                        posdic3 = boardfeature[data]["diagonals"]
                        for elem in posdic1:
                            alignmentbis.append(elem)
                        for elem in posdic2:
                            alignmentbis.append(elem)
                        for elem in posdic3:
                            alignmentbis.append(elem)
                    for i in alignmentbis:
                        if i not in alignment:
                            alignment.append(i)
                        else:
                            arrangement.append(i)
                    arrangement2 = list(filter(lambda x: x not in arrangement, alignment))
                    result = [alignment, arrangement, arrangement2]
                    return result

                def count(cara):
                    # returns a list of lists
                    # (number = (Common Cara of the 2 piece on the board, Common Cara of one of the pieces on the board
                    # and the piece to play, Common Cara of the other piece on the board an the piece to play).
                    keys_a = []
                    for data in cara:
                        if data is not None:
                            keys_a.append(data)
                    piece1 = keys_a[0]
                    piece2 = keys_a[1]
                    lista1 = set(piece1.values())
                    listb1 = set(piece2.values())
                    listc1 = set(remainingPieces[piecetoplay].values())
                    intersection0 = lista1 & listb1
                    intersection1 = listc1 & lista1
                    intersection2 = listc1 & listb1
                    nombre0 = len(intersection0)
                    nombre1 = len(intersection1)
                    nombre2 = len(intersection2)
                    number = [nombre0, nombre1, nombre2]
                    print("number" + str(number))
                    return number

                if count(visible['board'])[0] == 0:
                    # number of common characteristics between the 2 pieces on the board equals 0
                    possibilities = list(filter(lambda x: x not in boarddata2, posliste(token())[0]))
                    print("pos is" + str(possibilities))
                    move['pos'] = random.choice(possibilities)
                    move['nextPiece'] = randint(0, x - 1)

                if count(visible['board'])[0] == 1:
                    # number of common characteristics between the 2 pieces on the board equals 0
                    if count(visible['board'])[1] >= 1 and count(visible['board'])[2] >= 1:
                        # attack mode
                        # conditions must be improved because it doesn't what we really want
                        # the if just below does the same thing except it's only for 1 common cara ...
                        possibilities = posliste(token())[1]
                        print("pos is" + str(possibilities))
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = randint(0, x - 1)
                    if count(visible['board'])[1] == 1 or count(visible['board'])[2] == 1:
                        possibilities = posliste(token())[2]
                        print("pos is" + str(possibilities))
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = randint(0, x - 1)

                if count(visible['board'])[0] >= 2:
                    if count(visible['board'])[1] >= 1 and count(visible['board'])[2] >= 1:  #
                        possibilities = posliste(token())[1]  # a revoir
                        print("pos is" + str(possibilities))
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = randint(0, x - 1)
                    if (count(visible['board'])[1] == 1 and not count(visible['board'])[2] == 1) \
                            or (count(visible['board'])[2] == 1 and not count(visible['board'])[1] == 1):
                        # (a and not b) or (not a and b)
                        possibilities = posliste(token())[1]  # a revoir
                        print("pos is" + str(possibilities))
                        move['pos'] = random.choice(possibilities)
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
        def _read(board):
            dicoReadbis = []
            for i in range(len(board)):
                dicoRead = {}
                dicoRead[i] = board[i]
                dicoReadbis.append(dicoRead)
            return dicoReadbis

        visible = state._state['visible']
        move = {}

        remainingPieces = visible['remainingPieces']
        piecetoPlay = visible['pieceToPlay']
        remainingPieces_copy = copy.deepcopy(remainingPieces)

        # select the first free position
        if visible['pieceToPlay'] is not None:
            remainingPieces_copy.remove(remainingPieces[piecetoPlay])
            print('\npieceToPlay:', self.displayPiece(remainingPieces[piecetoPlay]),
                  '\n\nremainingPieces:',
                  (", ".join([self.displayPiece(piece) for piece in remainingPieces_copy])),
                  '\n')
            move['pos'] = int(input('Position: '))
            move['nextPiece'] = int(input('Next Piece: '))

        if visible['pieceToPlay'] is None:
            print('\nremainingPieces:', (", ".join([self.displayPiece(piece) for piece in remainingPieces])),
                  '\n')
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
