from typing import List, Tuple
import numpy as np


class Node:
    def __init__(self, score, total, move: int, state: np.ndarray, player, parent: 'Node', *nodes: 'Node'):
        assert type(move) == int or move is None
        self.parent = parent
        self.children = list(nodes)
        self._children_map = {i.move: i for i in nodes}
        self.score = score
        self.total = total
        self.move: int = move
        self.status = None
        self.winner = False
        self.loser = False
        self.player = player
        self.state = state

    def add(self, node: 'Node') -> 'Node':
        self.children.append(node)
        self._children_map[node.move] = node
        node.parent = self
        return self

    def get_move(self, *moves: int):
        if not moves:
            return self
        return self._children_map[moves[0]].get_move(*moves[1:])

    @property
    def precomputed_valid_moves(self) -> List[int]:
        return list(filter(lambda t: t is not None, map(lambda t: t.move, self.children)))

    def __repr__(self):
        return f'Node(score {self.score} total {self.total} move {self.move}) winner {self.winner} loser {self.loser}'

    def chain(self) -> List[int]:
        result = self._chain()
        result.reverse()
        return result

    def _chain(self) -> List[int]:
        result = [self.move]
        if self.parent:
            result += self.parent._chain()
        else:
            return []
        return result

    def tree(self) -> str:
        return self._tree(0)

    def _tree(self, depth) -> str:
        result = '\t' * depth + f'Node score {self.score} total {self.total} move {self.move} winner {self.winner} loser {self.loser} player {self.player} all {self.chain()}\n'
        for child in self.children:
            result += '\t' * depth + child._tree(depth + 1)
        return result


if __name__ == '__main__':
    n1 = Node(1, 4, 1, None, 1, None)
    n2 = Node(2, 4, 2, None, -1, n1)
    n3 = Node(3, 4, 3, None, 1, n1)
    n4 = Node(4, 4, 4, None, -1, n2)
    n5 = Node(5, 4, 5, None, 1, n4)

    n1.add(n2)
    n1.add(n3)
    n2.add(n4)
    n4.add(n5)

    print(n1.tree())
    print(n1.precomputed_valid_moves)
    print(n2.precomputed_valid_moves)
    print(n4.precomputed_valid_moves)
    print(n5.precomputed_valid_moves)
    print(n1.get_move(2))
