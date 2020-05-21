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

    def __calc_score(self, score, total):
        if total == 0:
            return 0
        return score / total

    def play(self, player: int) -> Tuple[int, int]:
        root = self._tree(player)
        result = sorted(root.nodes, key=lambda t: self.__calc_score(*t.value[1]), reverse=True)
        return result[0].value[0]

    def _tree(self, me: int) -> tree.Node:
        def recurse(player: int, board: board.Board, current_depth: int, node: tree.Node) -> Tuple[int, int]:
            valid = board.valid_moves

            score = 0
            total = 0
            for move in valid:
                new_board = board.copy()
                new_node = tree.Node([move], node)
                node.add(new_node)
                status = new_board.play(*move, player)
                if status == board.WIN:
                    if player == me:
                        score += board.WIN
                    else:
                        score += board.LOSS
                    total += 1
                    continue
                elif status == board.LOSS:
                    raise Exception('board should never return LOSS status')
                if current_depth < self.max_depth:
                    sub_score, sub_total = recurse(player * -1, new_board, current_depth + 1, new_node)
                    score += sub_score
                    total += sub_total
                del new_board
            node.value.append((score, total))
            # print(f'score {score} total {total} depth {current_depth}')
            return score, total

        tree_node = tree.Node([None], None)
        recurse(me, self.board, 1, tree_node)
        return tree_node
