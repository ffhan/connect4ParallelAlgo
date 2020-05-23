import abc
import board
from board import remap_char
import tree
from typing import Tuple, List


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
            return 0, 0
        # sort first by score, then by min of total
        return score / total, -total

    def compute(self, player: int) -> tree.Node:
        return self._tree(player)

    def play(self, player: int) -> int:
        root = self.compute(player)
        result = sorted(root.children, key=lambda t: self.__calc_score(t.score, t.total), reverse=True)
        # print(board.remap_char(player), result)
        # with open('root.txt', 'w') as file:
        #     file.write(root.tree())
        return result[0].move

    @staticmethod
    def play_node(me: int, board: board.Board, move: int, player: int, node: tree.Node):
        new_node = tree.Node(0, 0, move, remap_char(player), node)
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

    def _tree(self, me: int) -> tree.Node:
        def recurse(player: int, board: board.Board, current_depth: int, node: tree.Node):
            valid = board.valid_moves

            for move in valid:
                new_board = board.copy()
                new_node = self.play_node(me, new_board, move, player, node)
                if new_node.status == board.WIN:
                    continue
                if current_depth < self.max_depth:
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

        tree_node = tree.Node(0, 0, None, None, None)
        recurse(me, self.board, 1, tree_node)
        return tree_node
