import abc
from typing import Tuple, List

import common
import board
import tree
import numpy as np


class Controller(abc.ABC):
    """
    Controller is a component used by a Game object to determine the next move.
    It doesn't depend on the player ID, meaning any controller can be used as any player.
    """

    def __init__(self, board: board.Board):
        self.board = board

    @abc.abstractmethod
    def play(self, player: int) -> int:
        """
        Returns a move the controller wants to make.

        :param player: current player ID
        :return: chosen move
        """
        pass


class HardcodedController(Controller):
    """
    Controller that executes pre-recorded moves (used primarily in testing)
    """

    def __init__(self, board: board.Board, moves: List[int]):
        super().__init__(board)
        self.moves = moves

    def play(self, player: int) -> int:
        return self.moves.pop(0)


class UserController(Controller):
    """
    Controller that allows user input to interact with the game.

    It can build score trees from scratch (purely from the board state and current player ID) or from a pre-computed score tree.
    It can also use a pre-comouted score tree as a basis and build from there.
    """

    def __init__(self, board: board.Board):
        super().__init__(board)

    def play(self, player: int) -> int:
        return int(input())


class ComputerController(Controller):
    """
    Controller that allows computer to interact with the game.
    """

    def __init__(self, board: board.Board, difficulty=7, precompute_depth=0):
        super().__init__(board)
        self.max_depth = difficulty
        self.precompute_depth = precompute_depth

    def compute(self, player: int, max_depth: int, precomputed_tree: tree.Node = None) -> tree.Node:
        """
        Computes the score tree from the current board state for a selected player.

        :param player: player making the move
        :param max_depth: maximum score tree depth
        :param precomputed_tree: optional pre-computed tree that can be used as a basis for tree-building and computing scores
        :return: completely built & scored tree to the max_depth depth
        """
        return self._tree(player, max_depth, root=precomputed_tree)

    def play(self, player: int, precomputed_tree: tree.Node = None) -> int:
        """
        Computes the score tree and returns the optimal move for that tree.

        :param player: player making the move
        :param precomputed_tree: optional pre-computed tree (see controller.ComputerController#compute}
        :return:
        """
        root = self.compute(player, self.max_depth, precomputed_tree)  # compute the score tree
        print(*map(lambda t: '{:.3f}'.format(common.calculate_score(t.score, t.total)),
                   root.children))  # print scores for each valid move
        result = sorted(root.children, key=lambda t: common.calculate_score(t.score, t.total),
                        reverse=True)  # sort children nodes by score
        return result[0].move  # select the optimal child node and select it's move

    @staticmethod
    def create_tree(b: board.Board, player: int, max_depth) -> tree.Node:
        """
        Creates a pre-computed tree. It does NOT store scores for all nodes, just the leaf nodes and their direct parents.

        :param b: board
        :param player: current player
        :param max_depth: maximum tree depth to create
        :return: pre-computed tree
        """

        def recurse(move: int, board: board.Board, depth: int, current_player: int, node: tree.Node):
            """
            Recursively create a tree

            :param move: current move
            :param board: current board state
            :param depth: current depth
            :param current_player: current player
            :param node: parent node for this move
            :return:
            """
            if move is not None:
                node = ComputerController.play_node(player, board, move, current_player, node)
                if abs(node.status) == board.WIN:  # if win occurs this new node is a leaf in the tree
                    return  # we never encounter board.LOSS as a state because it's impossible to lose when it's your move
            for m in board.valid_moves:
                if depth < max_depth:
                    recurse(m, board.copy(), depth + 1, current_player * -1,
                            node)  # create a subtree for each valid move of the current board state

        node = tree.Node(0, 0, None, b.state, player * -1, None)  # create a root node
        recurse(None, b, 0, player * -1, node)  # compute from the current root node
        return node

    @staticmethod
    def play_node(me: int, board: board.Board, move: int, player: int, node: tree.Node) -> tree.Node:
        """
        Play a move in the current board and for the parent node.

        :param me: player we're building the tree for
        :param board: current board
        :param move: move to make
        :param player: current player
        :param node: parent node
        :return: new node for the current move
        """
        status = board.play(move, player)
        total_valid_moves_after_play = len(board.valid_moves)
        new_node = tree.Node(0, 1, move, board.state, player, node)  # create a new node
        if node:
            node.add(new_node)  # if parent node is supplied -> add new node as a child
        new_node.status = status
        if status == board.WIN:
            if player == me:
                if node:
                    node.winner = True  # mark parent as a winner
                new_node.winner = True
                # score is equal to the number of valid moves that would be possible if a win didn't occur
                new_node.score = board.WIN * total_valid_moves_after_play
                new_node.total = total_valid_moves_after_play
                # print(move, 'wins the game!')
            else:
                if node:
                    node.loser = True  # mark parent as a loser
                new_node.score = board.LOSS * total_valid_moves_after_play
                new_node.total = total_valid_moves_after_play
                new_node.loser = True
        return new_node

    def _tree(self, me: int, max_depth: int, root: tree.Node = None) -> tree.Node:
        """
        Creates a score tree of max depth with an optional pre-computed tree.

        :param me: player that the score tree is being computed for
        :param max_depth: maximum tree depth
        :param root: pre-computed tree
        :return: score tree of max depth max_depth
        """

        def recurse(player: int, r_board: board.Board, current_depth: int, node: tree.Node):
            """
            Goes through all pre-computed tree nodes, generates new ones if necessary
            and recursively scores the nodes from the bottom-up.

            :param player: current player
            :param r_board: current board state
            :param current_depth: current tree depth
            :param node: current tree node
            :return:
            """
            if node.children:  # if pre-computed tree was supplied
                for child in node.children:
                    new_board = board.Board(np.copy(child.state))
                    try:
                        if abs(child.status) == r_board.WIN:
                            continue
                    except AttributeError as er:
                        print(r_board)
                        raise er
                    if current_depth < max_depth:
                        # just go through the whole pre-computed tree
                        recurse(player * -1, new_board, current_depth + 1, child)
                    del new_board
            else:  # if no pre-computed tree was supplied -> generate your own
                for move in r_board.valid_moves:
                    new_board = r_board.copy()  # copy the board state (so that it doesn't affect other nodes)
                    new_node = self.play_node(me, new_board, move, player, node)  # play the move
                    if abs(new_node.status) == r_board.WIN:
                        continue  # if we won -> leaf node -> don't recurse any further
                    if current_depth < max_depth:
                        # create a sub-tree for the current state after our played move
                        recurse(player * -1, new_board, current_depth + 1, new_node)
                    del new_board
            if not (node.winner or node.loser):  # if not directly a winner or a loser (child not a winner or loser)
                all_winners = True
                all_losers = True
                for child in node.children:  # if all children are winners the current node is a winner, analogous for losers
                    if child.winner:
                        all_losers = False
                    elif child.loser:
                        all_winners = False
                    else:
                        all_winners = False
                        all_losers = False
                node.winner = all_winners
                node.loser = all_losers

            if node.children:  # if node has children (is not a leaf node) -> score it by using children scores
                score, total = 0, 0
                for child in node.children:
                    score += child.score  # this differs from spec but creates much better computer moves
                    total += child.total
                node.score = score
                node.total = total
            # print(node)

        common.log(f'tree with root {root}')
        if root is None:
            root = self.create_tree(self.board.copy(), me,
                                    max_depth)  # if no pre-computed tree was supplied -> create just the root node
        recurse(me, self.board, 1, root)  # create the tree recursively
        return root


if __name__ == '__main__':
    import numpy as np

    test_board = board.Board(np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    ))
    test_controller = ComputerController(test_board, difficulty=3)
    # create a pre-computed tree of depth 2
    test_root = test_controller.create_tree(test_board.copy(), -1, 2)
    print(test_root.tree())
    # use the pre-computed tree to compute the score tree of depth 3
    result_node = test_controller.compute(-1, 3, test_root)
    print(result_node.tree())
