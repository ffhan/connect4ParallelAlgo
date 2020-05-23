import board
import controller


class Game:

    def __init__(self, board: board.Board, player_1: controller.Controller, player_2: controller.Controller):
        self.board = board
        self.move = 0
        self.won = 0
        self.controllers = [player_1, player_2]

    def step(self) -> int:
        '''
        Play a move. Player is automatically chosen based on the game state.
        If either player won, all subsequent statuses will be WON/LOST and game state won't be updated.

        :param row: move row
        :param col: move column
        :return: move status
        '''
        if self.move % 2 == 0:
            ctl = self.controllers[0]
            player = self.board.PLAYER_1
        else:
            ctl = self.controllers[1]
            player = self.board.PLAYER_2
        if self.won:
            self.move += 1
            if player == self.won:
                return self.board.WIN
            return self.board.LOSS

        col = ctl.play(player)

        status = self.board.play(col, player)
        if status == self.board.INVALID_MOVE:
            return status
        if status == self.board.WIN:
            self.won = player
        self.move += 1
        return status

    def run(self, verbose=False):
        while self.won == 0:
            if len(self.board.valid_moves) == 0:
                return
            self.step()
            if verbose:
                print(self.board.table())
        print(f'Player {board.remap_char(self.won)} won!')


def test_1():
    all_moves = [0, 1, 2, 3, 5, 4, 5, 6, 1, 1, 2, 1, 2, 1, 2, 1, 2]
    b = board.Board()
    game = Game(b, controller.HardcodedController(b, all_moves[::2]),
                controller.HardcodedController(b, all_moves[1::2]))
    try:
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.INVALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.INVALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.WIN
        assert game.step() == b.LOSS
        assert game.step() == b.WIN
        assert game.step() == b.LOSS
    except AssertionError as e:
        print(b.table())
        raise e
    print(b.table())
    print(b.valid_moves)


def user_vs_user():
    b = board.Board()
    game = Game(b, controller.UserController(b), controller.UserController(b))
    game.run(verbose=True)


def user_vs_computer():
    b = board.Board()
    game = Game(b, controller.UserController(b), controller.ComputerController(b, difficulty=6))
    game.run(verbose=True)


def computer_vs_computer():
    b = board.Board()
    game = Game(b, controller.ComputerController(b, difficulty=1), controller.ComputerController(b, difficulty=6))
    game.run(verbose=True)


if __name__ == '__main__':
    # test_1()
    # user_vs_user()
    user_vs_computer()
    # computer_vs_computer()
