from typing import List, Tuple


class Node:
    def __init__(self, score, total, move, player, parent: 'Node', *nodes: 'Node'):
        self.parent = parent
        self.children = list(nodes)
        self.score = score
        self.total = total
        self.move: int = move
        self.status = None
        self.winner = False
        self.loser = False
        self.player = player

    def add(self, node: 'Node') -> 'Node':
        self.children.append(node)
        node.parent = self
        return self

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
    n1 = Node(1, 4, 0, None)
    n2 = Node(2, 4, 0, n1)
    n3 = Node(3, 4, 0, n1)
    n4 = Node(4, 4, 0, n2)
    n5 = Node(5, 4, 0, n4)

    n1.add(n2)
    n1.add(n3)
    n2.add(n4)
    n4.add(n5)

    print(n1.tree())
