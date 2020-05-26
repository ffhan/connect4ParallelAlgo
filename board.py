import numpy as np
import common
from typing import List


def _remap_char(value: int) -> str:
    """
    Pretty print character remapping (from player ID to character representing it).

    :param value: player ID
    :return: character remapping
    """
    if value == Board.PLAYER_1:
        return 'o'
    elif value == Board.PLAYER_2:
        return 'x'
    else:
        return ' '


def _official_char(value: int) -> str:
    """
        Spec character remapping (from player ID to character representing it).

        :param value: player ID
        :return: character remapping
        """
    if value == Board.PLAYER_1:
        return 'P'
    elif value == Board.PLAYER_2:
        return 'C'
    return '='


def remap_char(value: int) -> str:
    """
    Remaps characters according to the common.PPRINT config var.

    :param value: player ID
    :return: character remapping
    """
    if common.PPRINT:
        return _remap_char(value)
    else:
        return _official_char(value)


class Board:
    """
    Playing board with fixed width and height.

    It assumes two players, doesn't care who the players are - just defines the rules of the game.
    """
    width = 7
    height = 7

    win_count = 4

    NOT_SET = 0
    PLAYER_1 = 1
    PLAYER_2 = -1

    INVALID_MOVE = 0  # status returned when an invalid move is encountered
    LOSS = -1  # status returned when user loses a game
    WIN = 1  # status returned when user wins a game
    VALID_MOVE = 2  # status returned when user makes a valid move (but doesn't win)

    def __init__(self, state=None):
        """
        Create a board.
        State can be loaded by putting it in state param.
        It has to be a numpy array with shape (Board.height, Board.width).

        :param state: preloaded board state
        """
        if common.PPRINT: # choose which type of table print we're going to be using
            self.table = self._table
        else:
            self.table = self._official_table

        # 0 - unplayed field
        # 1 - player 1
        # -1 - player 2 (opponent)
        self.last_rows = [Board.height - 1 for i in range(Board.width)] # define valid row for every column of the board
        if state is None:
            # if no preloaded state -> initialize an empty board
            self.state = np.zeros((Board.height, Board.width))
        else:
            assert type(state) is np.ndarray and state.shape == (Board.height, Board.width)
            self.state = state
            for col in range(self.width): # compute last_rows based on the loaded state
                self.last_rows[col] = -1
                for row in range(self.height - 1, -1, -1):
                    if self.state[row, col] == self.NOT_SET:
                        self.last_rows[col] = row
                        break

    def play(self, col: int, player: int) -> int:
        """
        Plays a move and updates board state.
        Returns a move status (win/invalid move)

        :param col: move column
        :param player: player index
        :return: move status
        """
        if not (0 <= col < self.width):
            return Board.INVALID_MOVE
        row = self.last_rows[col]
        if player != Board.PLAYER_1 and player != Board.PLAYER_2:
            raise Exception(f'invalid player {player}')
        status = self.think(row, col, player)
        # if invalid, return status and don't update state
        if status == Board.INVALID_MOVE:
            return status
        # otherwise update state and return status
        self.state[row, col] = player
        self.last_rows[col] -= 1
        return status

    def think(self, row: int, col: int, player: int) -> int:
        """
        Checks the outcome of a certain move (defined by row and column) without updating board state.

        :param row: move row
        :param col: move column
        :param player: player making the move
        :return: move outcome
        """
        if not self.check_validity(row, col):
            return Board.INVALID_MOVE
        row_arr = self.state[row] # take a whole row
        col_arr = self.state[:, col].T # take a whole column
        row_count = self._count(row_arr, col, player)
        col_count = self._count(col_arr, row, player)

        if row_count >= Board.win_count or col_count >= Board.win_count:
            return Board.WIN
        return Board.VALID_MOVE

    @property
    def valid_moves(self) -> List[int]:
        """
        Calculate valid moves from the current board state.

        :return: list containing all valid moves
        """
        result = []
        for i, elem in enumerate(self.last_rows):
            if 0 <= elem < Board.height:
                result.append(i)
        return result

    def check_validity(self, row: int, col: int) -> bool:
        """
        Check if a move is valid in the current board state.

        :param row: move row
        :param col: move column
        :return: true if valid, false otherwise
        """
        if not (0 <= row < Board.height):
            return False
        if not (0 <= col < Board.width):
            return False
        # if field is set move is invalid
        if self.state[row, col] != Board.NOT_SET:
            return False
        # if field is not set (guaranteed by the upper if) and
        # row is at the bottom of the board = valid move
        if row == Board.height - 1:
            return True
        # otherwise, row below ours has to be set
        return self.state[row + 1, col] != Board.NOT_SET

    @staticmethod
    def _count(arr: np.ndarray, position: int, player: int) -> int:
        """
        Calculate how many contiguous fields are set for a player in a given array.

        :param arr: input array (could be a row or a column) - always provide it in shape (1, n)
        :param position: start position for checking
        :param player: player we're simulating a move for
        :return: number of contiguous fields set for that player
        """
        # middle-out spread -> count only contiguous player fields
        max_count = 1  # assume we want our current position to be for player
        # go left of position
        for i in range(position - 1, -1, -1):
            if arr[i] != player:
                break
            max_count += 1
        # go right of position
        for i in range(position + 1, len(arr)):
            if arr[i] != player:
                break
            max_count += 1
        return max_count

    def _official_table(self):
        """
        Return a string representation of the board according to the spec.

        :return: string representation of the board
        """
        fmt_string = '{}' * Board.width
        result = ''
        for row in self.state:
            result += fmt_string.format(*list(map(remap_char, row))) + '\n'
        return result[:-1]

    def _table(self):
        """
        Return a pretty print string representation of the board.

        :return: string representation of the board
        """
        horizontal_border = '\u2550'
        vertical_border = '\u2551'
        top_left_border = '\u256C'
        top_right_border = '\u2563'
        bottom_left_border = '\u2569'
        bottom_right_border = '\u255D'

        fmt_string = ('{} ' * Board.width)
        top = ' ' + vertical_border + ' ' + ' '.join([f'{i}' for i in range(self.width)]) + ' ' + vertical_border
        header = horizontal_border + top_left_border + horizontal_border * (Board.width * 2 + 1) + top_right_border
        footer = horizontal_border + bottom_left_border + horizontal_border * (
                Board.width * 2 + 1) + bottom_right_border
        result = ''
        for i, row in enumerate(self.state):
            result += f'{i}' + vertical_border + ' ' + fmt_string.format(
                *list(map(remap_char, row))) + vertical_border + '\n'
        result = top + '\n' + header + '\n' + result + footer + '\n'
        return result

    def copy(self):
        """
        Copies the current board.
        :return: board in the new memory space
        """
        return Board(state=np.copy(self.state))
