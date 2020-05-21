import board


class Game:

    def __init__(self, board: board.Board):
        self.board = board
        self.move = 0
        self.won = 0

    def play(self, row: int, col: int) -> int:
        '''
        Play a move. Player is automatically chosen based on the game state.
        If either player won, all subsequent statuses will be WON/LOST and game state won't be updated.

        :param row: move row
        :param col: move column
        :return: move status
        '''
        if self.move % 2 == 0:
            player = self.board.PLAYER_1
        else:
            player = self.board.PLAYER_2
        self.move += 1
        if self.won:
            if player == self.won:
                return self.board.WIN
            return self.board.LOSS

        status = self.board.play(row, col, player)
        if status == self.board.INVALID_MOVE:
            return status
        if status == self.board.WIN:
            self.won = player
        return status


if __name__ == '__main__':
    b = board.Board()
    game = Game(b)
    try:
        assert game.play(5, 0) == b.VALID_MOVE
        assert game.play(5, 1) == b.VALID_MOVE
        assert game.play(5, 2) == b.VALID_MOVE
        assert game.play(5, 3) == b.VALID_MOVE
        assert game.play(1, 5) == b.INVALID_MOVE
        assert game.play(5, 4) == b.VALID_MOVE
        assert game.play(5, 5) == b.VALID_MOVE
        assert game.play(5, 6) == b.VALID_MOVE
        assert game.play(1, 1) == b.INVALID_MOVE
        assert game.play(4, 1) == b.VALID_MOVE
        assert game.play(4, 2) == b.VALID_MOVE
        assert game.play(3, 1) == b.VALID_MOVE
        assert game.play(3, 2) == b.VALID_MOVE
        assert game.play(2, 1) == b.WIN
        assert game.play(2, 2) == b.LOSS
        assert game.play(1, 1) == b.WIN
        assert game.play(1, 2) == b.LOSS
    except AssertionError as e:
        print(b)
        raise e
    print(b)

