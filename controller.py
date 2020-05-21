import abc
import board
import tree
from typing import Tuple, List


class Controller(abc.ABC):
    def __init__(self, board: board.Board):
        self.board = board

    @abc.abstractmethod
    def play(self, player: int) -> Tuple[int, int]:
        pass


class HardcodedController(Controller):
    def __init__(self, board: board.Board, moves: List[Tuple[int, int]]):
        super().__init__(board)
        self.moves = moves

    def play(self, player: int) -> Tuple[int, int]:
        return self.moves.pop(0)


class UserController(Controller):
    def __init__(self, board: board.Board):
        super().__init__(board)

    def play(self, player: int) -> Tuple[int, int]:
        row, col = map(lambda t: int(t), input().split(' '))
        return row, col


class ComputerController(Controller):
    def __init__(self, board: board.Board, difficulty=5):
        super().__init__(board)
        self.max_depth = difficulty

    @staticmethod
    def __calc_score(score, total) -> Tuple[float, float]:
        if total == 0:
            return 0, 0
        # sort first by score, then by min of total
        return score / total, -total

    def play(self, player: int) -> Tuple[int, int]:
        root = self._tree(player)
        result = sorted(root.children, key=lambda t: self.__calc_score(t.score, t.total), reverse=True)
        # print(board.remap_char(player), result)

        # todo: fix 5 2 bug
        return result[0].move

    def _tree(self, me: int) -> tree.Node:
        def recurse(player: int, board: board.Board, current_depth: int, node: tree.Node):
            valid = board.valid_moves

            for move in valid:
                new_board = board.copy()
                new_node = tree.Node(0, 0, move, node)
                node.add(new_node)
                status = new_board.play(*move, player)
                new_node.status = status
                if status == board.WIN:
                    if player == me:
                        node.winner = True
                        new_node.winner = True
                        new_node.score = board.WIN
                        new_node.total = 1
                        # print(move, 'wins the game!')
                    else:
                        new_node.score = board.LOSS
                        new_node.total = 1
                        node.loser = True
                        new_node.loser = True
                    continue
                elif status == board.LOSS:
                    raise Exception('board should never return LOSS status')
                if current_depth < self.max_depth:
                    recurse(player * -1, new_board, current_depth + 1, new_node)
                del new_board
            if not (node.winner or node.loser): # if not directly a winner or a loser (child not a winner or loser)
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
                if all_winners:
                    node.winner = True
                if all_losers:
                    node.loser = True
                score, total = 0, 0
                for child in node.children:
                    if child.winner:
                        score += board.WIN
                    elif child.loser:
                        score += board.LOSS
                    total += 1
                node.score = score
                node.total = total
            else:
                if node.winner:
                    node.score = 1
                    node.total = 1
                elif node.loser:
                    node.score = -1
                    node.total = 1
            # print(node)

        tree_node = tree.Node(0, 0, None, None)
        recurse(me, self.board, 1, tree_node)
        return tree_node
