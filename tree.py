from typing import List, Tuple


class Node:
    def __init__(self, score, total, move, parent: 'Node', *nodes: 'Node'):
        self.parent = parent
        self.children = list(nodes)
        self.score = score
        self.total = total
        self.move: int = move
        self.status = None
        self.winner = False
        self.loser = False

    def add(self, node: 'Node') -> 'Node':
        self.children.append(node)
        node.parent = self
        return self

    def __repr__(self):
        return f'Node(score {self.score} total {self.total} move {self.move}) winner {self.winner} loser {self.loser}'

    def chain(self) -> List[int]:
        result = [self.move]
        if self.parent:
            result += self.parent.chain()
        else:
            return []
        return result
