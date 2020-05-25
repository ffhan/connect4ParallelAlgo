import board
import controller


class Game:
    """
    Game is a wrapper around the Board that contains the current game state.
    It also controls the main game loop and exit conditions.
    """

    def __init__(self, board: board.Board, player_1: controller.Controller, player_2: controller.Controller):
        """
        Create a Game object from the current board and 2 players represented by controllers.

        :param board: board
        :param player_1: player 1 controller
        :param player_2: player 2 controller
        """
        self.board = board
        self.move = 0
        self.won = 0
        self.controllers = [player_1, player_2]

    def step(self) -> int:
        """
        Play a move. Player is automatically chosen based on the game state.
        If either player won, all subsequent statuses will be WON/LOST and game state won't be updated.

        :return: move status (WIN/LOSS/VALID_MOVE/INVALID_MOVE)
        """
        # select the appropriate controller and player ID from the game state
        if self.move % 2 == 0:
            ctl = self.controllers[0]
            player = self.board.PLAYER_1
        else:
            ctl = self.controllers[1]
            player = self.board.PLAYER_2
        if self.won:  # if the game was already completed return the appropriate status for the current player (WIN/LOSS)
            self.move += 1
            if player == self.won:
                return self.board.WIN
            return self.board.LOSS

        selected_move = ctl.play(player)  # player selects the move

        status = self.board.play(selected_move, player)  # play the selected move
        if status == self.board.INVALID_MOVE:
            return status
        if status == self.board.WIN:
            self.won = player
        self.move += 1
        return status

    def run(self, verbose=False):
        """
        Runs the main game loop.

        :param verbose: prints the board after every move
        :return:
        """
        step_num = 0
        while self.won == 0:
            if len(self.board.valid_moves) == 0:
                return
            status = self.step()
            if verbose and step_num % 2 == 1:
                print(self.board.table())
            if status != board.Board.INVALID_MOVE:
                step_num += 1
        print(f'Player {board.remap_char(self.won)} won!')


def test_1():
    all_moves = [3, 3, 3, 3, 3, 3, 3, 0, 1, 0, 1, 0, 1, 0, 1]
    b = board.Board()
    game = Game(b, controller.HardcodedController(b, all_moves[::2]),
                controller.HardcodedController(b, all_moves[1::2]))
    try:
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.INVALID_MOVE
        assert game.step() == b.VALID_MOVE
        assert game.step() == b.VALID_MOVE
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
    game = Game(b, controller.ComputerController(b, difficulty=6), controller.ComputerController(b, difficulty=6))
    game.run(verbose=True)


if __name__ == '__main__':
    import common

    # test for board states
    # test_1()
    # user vs user game
    # user_vs_user()
    # user vs computer game
    # user_vs_computer()
    # computer vs computer game
    computer_vs_computer()
