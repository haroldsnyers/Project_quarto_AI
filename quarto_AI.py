#!/usr/bin/env python3
# quarto.py
# Server
# Author: Quentin Lurkin
# Version: March 29, 2018

# client AI and player
# Author: Harold Snyers & Alexandre Seynaeve
# version: May 17, 2018

import argparse
import random
import json
import copy

from random import randint
from easyAI import TwoPlayersGame, AI_Player
from easyAI.AI import Negamax, TT, SSS
from easyAI.AI.solving import id_solve
from lib import game


class QuartoState(game.GameState):
    '''Class representing a state for the Quarto game.'''

    def __init__(self, initialstate=None, currentPlayer=None):
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

        if currentPlayer is None:
            currentPlayer = random.randrange(2)

        super().__init__(initialstate, currentPlayer=currentPlayer)

    def applymove(self, move):
        # {pos: 8, quarto: true, nextPiece: 2}
        stateBackup = copy.deepcopy(self._state)
        try:
            state = self._state['visible']
            if state['pieceToPlay'] is not None:
                try:
                    if state['board'][move['pos']] is not None:
                        raise game.InvalidMoveException('The position is not free')
                    state['board'][move['pos']] = state['remainingPieces'][state['pieceToPlay']]
                    del (state['remainingPieces'][state['pieceToPlay']])
                except game.InvalidMoveException as e:
                    raise e
                except:
                    raise game.InvalidMoveException("Your move should contain a \"pos\" key in range(16)")

            if len(state['remainingPieces']) > 0:
                try:
                    state['pieceToPlay'] = move['nextPiece']
                except:
                    raise game.InvalidMoveException("You must specify the next piece to play")
            else:
                state['pieceToPlay'] = None

            if 'quarto' in move:
                state['quartoAnnounced'] = move['quarto']
                winner = self.winner()
                if winner is None or winner == -1:
                    raise game.InvalidMoveException("There is no Quarto !")
            else:
                state['quartoAnnounced'] = False
        except game.InvalidMoveException as e:
            self._state = stateBackup
            raise e

    def _same(self, feature, elems):
        try:
            elems = list(map(lambda piece: piece[feature], elems))
        except:
            return False
        return all(e == elems[0] for e in elems)

    def _quarto(self, elems):
        return self._same('shape', elems) or self._same('color', elems) or self._same('filling', elems) or self._same(
            'height', elems)

    def winner(self):
        state = self._state['visible']
        board = state['board']
        player = self._state['currentPlayer']

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

        print('Board:')
        for row in range(4):
            print('|', end="")
            for col in range(4):
                print(self.displayPiece(state['board'][row * 4 + col]), end="|")
            print()

        print("00 01 02 03", '\n04 05 06 07', '\n08 09 10 11', '\n12 13 14 15\n')

        print('\nRemaining Pieces:')
        print(", ".join([self.displayPiece(piece) for piece in state['remainingPieces']]))

        if state['pieceToPlay'] is not None:
            print('\nPiece to Play:')
            print(self.displayPiece(state['remainingPieces'][state['pieceToPlay']]))

    def nextPlayer(self):
        self._state['currentPlayer'] = (self._state['currentPlayer'] + 1) % 2


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
            self._state.applymove(move)


# Main AI
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

        # returns a list of the position on the board which are taken
        def token():
            link = []
            for i in range(16):
                if visible['board'][i] is not None:
                    link.append(i)
            return link

        # returns a list of the free positions on the board
        def nottoken():
            notlink = []
            for i in range(16):
                if visible['board'][i] is None:
                    notlink.append(i)
            return notlink

        # returns a list of the position of the first piece on the board
        def token0():
            list = []
            i = token()[0]
            list.append(i)
            return list

        # returns a list of the position of the second piece on the board
        def token1():
            list = []
            i = token()[1]
            list.append(i)
            return list

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
                move['nextPiece'] = randint(0, 14)

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

                def listpiece(nbr1, nbr2):
                    # returns a list of all the possibilities which satisfy the conditions for the nextpiece to play
                    nextpieces = []
                    i = 0
                    remainingPieces_copy = copy.deepcopy(remainingPieces)
                    remainingPieces_copy.remove(remainingPieces[piecetoplay])
                    for piece in remainingPieces_copy:
                        if nbrcara1(piece, remainingPieces[piecetoplay]) == nbr1:
                            if nbr2+1 >= nbrcara(_read(visible['board']), piece) >= nbr2:
                                nextpieces.append(i)
                        i += 1
                    return nextpieces

                # all the positions possible on the board
                boarddata = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

                # making a choice in function of the number of common characteristics
                if nbrcara(_read(visible['board']), remainingPieces[piecetoplay]) < 2:
                    possibilities = list(filter(lambda x: x not in posliste(posPiece), boarddata))
                    move['pos'] = random.choice(possibilities)
                    # number of common characteristics equals 0
                    if nbrcara(_read(visible['board']), remainingPieces[piecetoplay]) == 0:
                        # will choose a piece which will have 3 common characteristics with the last piece played and
                        # 1 or 2 with the piece which was first played
                        move['nextPiece'] = random.choice(listpiece(3, 1))
                    # number of common characteristics equals 1
                    else:
                        # will choose a piece which will have 2 common characteristics with the last piece played and
                        # 1 or 2 with the piece which was first played
                        move['nextPiece'] = random.choice(listpiece(2, 1))

                else:
                    move['pos'] = random.choice(posliste(posPiece))
                    # number of common characteristics equals 2
                    if nbrcara(_read(visible['board']), remainingPieces[piecetoplay]) == 2:
                        # will choose a piece which will have 1 common characteristics with the last piece played and
                        # 0 or 1 with the piece which was first played or the contrary
                        move['nextPiece'] = random.choice(listpiece(1, 0) or listpiece(0, 1))
                    # number of common characteristics equals 3
                    else:
                        # will choose a piece which will have 2 common characteristics with the last piece played and
                        # 2 or 3 with the piece which was first played
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
                    alignmentbisbis = list(filter(lambda x: x not in token(), alignmentbis))
                    for i in alignmentbisbis:
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
                    return number

                def _read1(board):
                    # same function as _read but here it returns a list of the pieces on the
                    # board without their positions. It returns a list of dictionaries
                    dicoRead = []
                    for i in board:
                        if i is not None:
                            dicoRead.append(i)
                    dicoRead.append(remainingPieces[piecetoplay])
                    return dicoRead

                def master(liste):
                    # returns the characteristics of the piece which will be played by the opponent inf function
                    # of the pieces already on the board
                    roundi = 0
                    squarei = 0
                    darki = 0
                    lighti = 0
                    lowi = 0
                    highi = 0
                    emptyi = 0
                    fulli = 0
                    piecetoplay = {}
                    for piece in liste:
                        for car in piece:
                            if piece[car] == 'round':
                                roundi += 1
                            if piece[car] == 'square':
                                squarei += 1
                            if piece[car] == 'dark':
                                darki += 1
                            if piece[car] == 'light':
                                lighti += 1
                            if piece[car] == 'low':
                                lowi += 1
                            if piece[car] == 'high':
                                highi += 1
                            if piece[car] == 'empty':
                                emptyi += 1
                            if piece[car] == 'full':
                                fulli += 1
                    if roundi < squarei:
                        piecetoplay.update({'shape': 'round'})
                    else:
                        piecetoplay.update({'shape': 'square'})
                    if darki < lighti:
                        piecetoplay.update({'color': 'dark'})
                    else:
                        piecetoplay.update({'color': 'light'})
                    if lowi < highi:
                        piecetoplay.update({'height': 'low'})
                    else:
                        piecetoplay.update({'height': 'high'})
                    if emptyi < fulli:
                        piecetoplay.update({'filling': 'empty'})
                    else:
                        piecetoplay.update({'filling': 'full'})
                    return piecetoplay

                def match(piece2play):
                    # returns the index of the piece in remainingPieces which matches the characteristics of the piece
                    # returned in master
                    remainingPieces_copy = copy.deepcopy(remainingPieces)
                    remainingPieces_copy.remove(remainingPieces[piecetoplay])
                    for i in range(len(remainingPieces_copy)):
                        if remainingPieces_copy[i] == piece2play:
                            return i

                # choices for the position and nextpiece are made here after

                # number of common characteristics between the pieces on the board equals 0
                if count(visible['board'])[0] == 0:
                    # comparison between the common characteristics of each piece on the board and the piecetoplay
                    if count(visible['board'])[1] > count(visible['board'])[2]:
                        possibilities = posliste(token0())[0]   # in alignment with the first piece on the board
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = match(master(_read1(visible['board'])))
                    elif count(visible['board'])[1] == count(visible['board'])[2]:
                        possibilities = posliste(token())[1]    # in alignment with the two pieces on the board
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = match(master(_read1(visible['board'])))
                    else:
                        possibilities = posliste(token1())[0]   # in alignment with the second piece on the board
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = match(master(_read1(visible['board'])))

                # number of common characteristics between the pieces on the board equals 1
                elif count(visible['board'])[0] == 1:
                    # comparison between the common characteristics of each piece on the board and the piecetoplay
                    if count(visible['board'])[1] == 0 and count(visible['board'])[2] >= 1:
                        possibilities = posliste(token1())[0]   # in alignment with the second piece on the board
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = match(master(_read1(visible['board'])))
                    elif count(visible['board'])[1] >= 1 and count(visible['board'])[2] == 0:
                        possibilities = posliste(token0())[0]   # in alignment with the first piece on the board
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = match(master(_read1(visible['board'])))
                    else:
                        if count(visible['board'])[1] > count(visible['board'])[2]:
                            # in alignment with the first piece on the board but not with the second piece on the board
                            possibilities = list(filter(lambda x: x not in posliste(token())[1], posliste(token0())[0]))
                            move['pos'] = random.choice(possibilities)
                            move['nextPiece'] = match(master(_read1(visible['board'])))
                        elif count(visible['board'])[1] == count(visible['board'])[2]:
                            possibilities = posliste(token())[1]    # in alignment with the two pieces on the board
                            move['pos'] = random.choice(possibilities)
                            move['nextPiece'] = match(master(_read1(visible['board'])))
                        else:
                            # in alignment with the second piece on the board but not with the first piece on the board
                            possibilities = list(filter(lambda x: x not in posliste(token())[1], posliste(token1())[0]))
                            move['pos'] = random.choice(possibilities)
                            move['nextPiece'] = match(master(_read1(visible['board'])))

                # number of common characteristics between the pieces on the board equals 2
                elif count(visible['board'])[0] == 2:
                    # comparison between the common characteristics of each piece on the board and the piecetoplay
                    if count(visible['board'])[1] == 0:
                        possibilities = posliste(token1())[0]   # in alignment with the second piece on the board
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = match(master(_read1(visible['board'])))
                    elif count(visible['board'])[2] == 0:
                        possibilities = posliste(token0())[0]   # in alignment with the second piece on the board
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = match(master(_read1(visible['board'])))
                    elif count(visible['board'])[1] == 1 and count(visible['board'])[2] == 1:
                        possibilities = posliste(token())[1]    # in alignment with the two pieces on the board
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = match(master(_read1(visible['board'])))
                    elif count(visible['board'])[1] == 1 and count(visible['board'])[2] > 1:
                        # in alignment with the first piece on the board but not with the second piece on the board
                        possibilities = list(
                            filter(lambda x: x not in posliste(token())[1], posliste(token0())[0]))
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = match(master(_read1(visible['board'])))
                    elif count(visible['board'])[1] > 1 and count(visible['board'])[2] == 1:
                        # in alignment with the second piece on the board but not with the first piece on the board
                        possibilities = list(
                            filter(lambda x: x not in posliste(token())[1], posliste(token1())[0]))
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = match(master(_read1(visible['board'])))
                    # Nbr cara between piece 1 and piecetoplay and between piece 2 and piecetoplay greater than 1
                    else:
                        # not in alignment with any of the pieces on the board
                        possibilities = list(filter(lambda x: x not in posliste(token())[0], boarddata2))
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = match(master(_read1(visible['board'])))

                # number of common characteristics between the pieces on the board equals 3
                elif count(visible['board'])[0] == 3:
                    # takes the sum of the common characteristics of each piece on the board and the piecetoplay and
                    # chooses the moves for each possible outcome for the sum
                    if (count(visible['board'])[1] + count(visible['board'])[2]) == 1:
                        possibilities = posliste(token())[1]    # in alignment with the two pieces on the board
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = match(master(_read1(visible['board'])))
                    elif (count(visible['board'])[1] + count(visible['board'])[2]) == 3:
                        if count(visible['board'])[1] == 2:
                            # in alignment with the second piece on the board but not with the first piece on the board
                            possibilities = list(
                                filter(lambda x: x not in posliste(token())[1], posliste(token1())[0]))
                            move['pos'] = random.choice(possibilities)
                            move['nextPiece'] = match(master(_read1(visible['board'])))
                        else:
                            # in alignment with the first piece on the board but not with the second piece on the board
                            possibilities = list(
                                filter(lambda x: x not in posliste(token())[1], posliste(token0())[0]))
                            move['pos'] = random.choice(possibilities)
                            move['nextPiece'] = match(master(_read1(visible['board'])))
                    # thus the sum equals 5
                    else:
                        # not in alignment with any of the pieces on the board
                        possibilities = list(filter(lambda x: x not in posliste(token())[0], boarddata2))
                        move['pos'] = random.choice(possibilities)
                        move['nextPiece'] = match(master(_read1(visible['board'])))

            # easyAI comes into place from this moment (x=13)
            if 9 < x <= 13:
                QuartoMind.ttentry = lambda self: state     # Send State to the Transposition tables
                quarto_algo_sss = SSS(3)    # Algorithm(depth, scoring=None, win_score=inf)
                quarto_algo_neg = Negamax(8, win_score=90,
                                          tt=TT)   # Algorithm(depth, scoring=None, win_score=inf,tt=None)
                Quarto = QuartoMind([AI_Player(quarto_algo_sss), AI_Player(quarto_algo_neg)], state)
                print(str(Quarto.get_move()))
                move = Quarto.get_move()    # find best move possible

            if 7 < x <= 9:
                QuartoMind.ttentry = lambda self: state     # Send State to the Transposition tables
                quarto_algo_sss = SSS(4)    # Algorithm(depth, scoring=None, win_score=inf)
                quarto_algo_neg = Negamax(7, win_score=90,
                                          tt=TT)   # Algorithm(depth, scoring=None, win_score=inf,tt=None)
                Quarto = QuartoMind([AI_Player(quarto_algo_sss), AI_Player(quarto_algo_neg)], state)
                print(str(Quarto.get_move()))
                move = Quarto.get_move()    # find best move possible

            if 4 < x <= 7:
                QuartoMind.ttentry = lambda self: state     # Send State to the Transposition tables
                quarto_algo_sss = SSS(5)    # Algorithm(depth, scoring=None, win_score=inf)
                quarto_algo_neg = Negamax(8, win_score=90,
                                          tt=TT)   # Algorithm(depth, scoring=None, win_score=inf,tt=None)
                Quarto = QuartoMind([AI_Player(quarto_algo_sss), AI_Player(quarto_algo_neg)], state)
                print(str(Quarto.get_move()))
                move = Quarto.get_move()    # find best move possible

            if x <= 4:
                # solve the game and give the Move to do it, id_solve return:
                #   • Move: Best Move to play for the player.
                #   • Result: Either 1 (certain victory of the first player) or -1 (certain defeat) or 0 (either draw)
                #   • Depth: The minimal number of moves before victory (or defeat)

                Result, Depth, move = id_solve(QuartoMind([], state), ai_depths=range(2, 4), win_score=90)

        # apply the move to check for quarto
        # applymove will raise if we announce a quarto while there is not
        move['quarto'] = True
        try:
            state.applymove(move)
        except:
            del (move['quarto'])

        # send the move
        return json.dumps(move)


# AI BOT1 => to play against AI (lvl2)
class QuartoAIBOT1(game.GameClient):
    """Class representing a client for the Quarto game."""

    def __init__(self, name, server, verbose=False):
        super().__init__(server, QuartoState, verbose=verbose)
        self.__name = name

    def _handle(self, message):
        pass

    def _nextmove(self, state):
        # solve the game and give the Move to do it, id_solve return:
        #   • Move: Best Move to play for the player.
        #   • Result: Either 1 (certain victory of the first player) or -1 (certain defeat) or 0 (either draw)
        #   • Depth: The minimal number of moves before victory (or defeat)

        Result, Depth, move = id_solve(QuartoMind([], state), ai_depths=range(2, 4), win_score=90)
        return json.dumps(move)  # send the Move


# AI BOT2 => to play against AI (lvl1)
class QuartoAIBOT2(game.GameClient):
    """Class representing a client for the Quarto game."""

    def __init__(self, name, server, verbose=False):
        super().__init__(server, QuartoState, verbose=verbose)
        self.__name = name

    def _handle(self, message):
        pass

    def _nextmove(self, State):
        QuartoMind.ttentry = lambda self: State     # Send State to the Transposition tables
        quarto_algo_neg = SSS(3)    # Algorithm(depth, scoring=None, win_score=inf)
        quarto_algo_sss = Negamax(6, win_score=90, tt=TT)    # Algorithm(depth, scoring=None, win_score=inf,tt=None)
        Quarto = QuartoMind([AI_Player(quarto_algo_neg), AI_Player(quarto_algo_sss)], State)
        print(str(Quarto.get_move()))
        move = Quarto.get_move()   # find best move possible
        return json.dumps(move)  # send the Move


# easyAI
class QuartoMind(TwoPlayersGame):
    def __init__(self, players, State):
        self.State = State
        self.players = players
        self.nplayer = 1

    # structure of the game
    def possible_moves(self):
        liste = []
        visible = self.State._state['visible']

        def nottoken():
            notlink = []
            for i in range(16):
                if visible['board'][i] is None:
                    notlink.append(i)
            return notlink

        boarddata = nottoken()

        # if there is only one free position left on the board, play the last piece
        if visible['board'].count(None) == 1:
            liste.append({'pos': visible['board'].index(None), 'nextPiece': 0})

        else:
            for i in boarddata:
                for n in range(len(visible['remainingPieces']) - 1):
                    move = {}
                    move['pos'] = i
                    move['nextPiece'] = n
                    move['quarto'] = True
                    if visible['board'][i] is None:
                        try:
                            CopyState = copy.deepcopy(self.State)
                            CopyState.applymove(move)
                        except:
                            del (move['quarto'])
                        liste.append(move)
        return liste

    # applying move 
    def make_move(self, move):
        position = move['pos']
        visible = self.State._state['visible']
        if visible['board'][position] is None:
            self.State.applymove(move)

    def win(self):
        return self.State.winner()

    # check if the game is over
    def is_over(self):
        return False if self.win() == -1 else True
    
    # show the state of the board
    def show(self):
        self.State.prettyprint()
    
    # verifies the state of the game and returns its status
    def scoring(self):
        Score = self.win()
        if Score == self.nopponent:
            return 100
        if Score in [-1, 2]:
            return 0
        else:
            return -100


# player => human player can play against AI
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
    # Create the parser for the 'clientAIBOT' subcommand
    AI_parser = subparsers.add_parser('BOT1', help='launch a client')
    AI_parser.add_argument('name', help='name of the player')
    AI_parser.add_argument('--host', help='hostname of the server (default: localhost)', default='127.0.0.1')
    AI_parser.add_argument('--port', help='port of the server (default: 5000)', default=5000)
    AI_parser.add_argument('--verbose', action='store_true')
    # Create the parser for the 'clientAIBOT' subcommand
    AI_parser = subparsers.add_parser('BOT2', help='launch a client')
    AI_parser.add_argument('name', help='name of the player')
    AI_parser.add_argument('--host', help='hostname of the server (default: localhost)', default='127.0.0.1')
    AI_parser.add_argument('--port', help='port of the server (default: 5000)', default=5000)
    AI_parser.add_argument('--verbose', action='store_true')
    # Create the parser for the 'clientAIBOT' subcommand
    AI_parser = subparsers.add_parser('BOT3', help='launch a client')
    AI_parser.add_argument('name', help='name of the player')
    AI_parser.add_argument('--host', help='hostname of the server (default: localhost)', default='127.0.0.1')
    AI_parser.add_argument('--port', help='port of the server (default: 5000)', default=5000)
    AI_parser.add_argument('--verbose', action='store_true')
    # Create the parser for the 'clientAIBOT' subcommand
    AI_parser = subparsers.add_parser('BOT4', help='launch a client')
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
    elif args.component == 'player':
        QuartoPlayer(args.name, (args.host, args.port), verbose=args.verbose)
    elif args.component == 'BOT1':
        QuartoAIBOT1(args.name, (args.host, args.port), verbose=args.verbose)
    elif args.component == 'BOT2':
        QuartoAIBOT2(args.name, (args.host, args.port), verbose=args.verbose)
