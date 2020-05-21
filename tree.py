class Node:
    def __init__(self, value, parent: 'Node', *nodes: 'Node'):
        self.parent = parent
        self.nodes = list(nodes)
        self.value = value

    def add(self, node: 'Node') -> 'Node':
        self.nodes.append(node)
        node.parent = self
        return self
