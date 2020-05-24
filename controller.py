import abc
from typing import Tuple, List

import common
import board
import tree
import numpy as np


class Controller(abc.ABC):
    def __init__(self, board: board.Board):
        self.board = board

    @abc.abstractmethod
    def play(self, player: int) -> int:
        pass


class HardcodedController(Controller):
    def __init__(self, board: board.Board, moves: List[int]):
        super().__init__(board)
        self.moves = moves

    def play(self, player: int) -> int:
        return self.moves.pop(0)


class UserController(Controller):
    def __init__(self, board: board.Board):
        super().__init__(board)

    def play(self, player: int) -> int:
        return int(input())


class ComputerController(Controller):
    def __init__(self, board: board.Board, difficulty=7):
        super().__init__(board)
        self.max_depth = difficulty

    @staticmethod
    def __calc_score(score, total) -> Tuple[float, float]:
        if total == 0:
            return 0
        # sort first by score, then by min of total
        return score / total

    def compute(self, player: int, max_depth: int, precomputed_tree: tree.Node = None) -> tree.Node:
        return self._tree(player, max_depth, root=precomputed_tree)

    def play(self, player: int) -> int:
        root = self.compute(player, self.max_depth)
        print(*map(lambda t: '{:.3f}'.format(self.__calc_score(t.score, t.total)), root.children))
        result = sorted(root.children, key=lambda t: self.__calc_score(t.score, t.total), reverse=True)
        # print(board.remap_char(player), result)
        # with open('root.txt', 'w') as file:
        #     file.write(root.tree())
        return result[0].move

    @staticmethod
    def create_tree(b: board.Board, player: int, max_depth) -> tree.Node:
        def recurse(move: int, board: board.Board, depth: int, current_player: int, node: tree.Node):
            if move is not None:
                node = ComputerController.play_node(player, board, move, current_player, node)
                if abs(node.status) == board.WIN:
                    return
            for m in board.valid_moves:
                if depth < max_depth:
                    recurse(m, board.copy(), depth + 1, current_player * -1, node)

        node = tree.Node(0, 0, None, b.state, player * -1, None)
        recurse(None, b, 0, player * -1, node)
        return node

    @staticmethod
    def play_node(me: int, board: board.Board, move: int, player: int, node: tree.Node) -> tree.Node:
        new_node = tree.Node(0, 1, move, board.state, player, node)
        if node:
            node.add(new_node)
        status = board.play(move, player)
        new_node.status = status
        if status == board.WIN:
            if player == me:
                if node:
                    node.winner = True
                new_node.winner = True
                new_node.score = board.WIN
                new_node.total = 1
                # print(move, 'wins the game!')
            else:
                if node:
                    node.loser = True
                new_node.score = board.LOSS
                new_node.total = 1
                new_node.loser = True
        return new_node

    def _tree(self, me: int, max_depth: int, root: tree.Node = None) -> tree.Node:
        def recurse(player: int, r_board: board.Board, current_depth: int, node: tree.Node):
            if node.children:
                for child in node.children:
                    new_board = board.Board(np.copy(child.state))
                    if abs(child.status) == r_board.WIN:
                        continue
                    if current_depth < max_depth:
                        recurse(player * -1, new_board, current_depth + 1, child)
                    del new_board
            else:
                for move in r_board.valid_moves:
                    new_board = r_board.copy()
                    new_node = self.play_node(me, new_board, move, player, node)
                    if abs(new_node.status) == r_board.WIN:
                        continue
                    if current_depth < max_depth:
                        recurse(player * -1, new_board, current_depth + 1, new_node)
                    del new_board
            if not (node.winner or node.loser):  # if not directly a winner or a loser (child not a winner or loser)
                all_winners = True
                all_losers = True
                for child in node.children:
                    if child.winner:
                        all_losers = False
                    elif child.loser:
                        all_winners = False
                    else:
                        all_winners = False
                        all_losers = False
                node.winner = all_winners
                node.loser = all_losers

            if node.children:
                score, total = 0, 0
                for child in node.children:
                    score += child.score
                    total += child.total
                    # if child.loser:
                    #     score += board.LOSS
                    # elif child.winner:
                    #     score += board.WIN
                    # total += 1
                node.score = score
                node.total = total
            # print(node)

        if root is None:
            root = self.create_tree(self.board.copy(), me, max_depth)
        recurse(me, self.board, 1, root)
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
    test_root = test_controller.create_tree(test_board.copy(), -1, 3)
    print(test_root.tree())
    result_node = test_controller.compute(-1, 5, test_root)
    print(result_node.tree())
