import queue
import threading
from typing import List

import numpy as np

import board
import common
import controller
import measure
import tree

REQUEST_TAG = 50
TASK_TAG = 101
RESULT_TAG = 102
DONE_TAG = 103


class Message:
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value

    def __repr__(self):
        return f'Message(tag: {self.tag}, value: {self.value})'


class Task:
    def __init__(self, worker: int, state: np.ndarray, moves: List[int], player: int):
        self.player = player
        self.moves = moves
        self.worker = worker
        self.state = state

    def __repr__(self) -> str:
        return f'Task(player: {self.player}, moves: {self.moves}, worker:{self.worker})'


class Result:
    def __init__(self, score: int, total: int, winner: bool, loser: bool, moves: List[int]):
        self.score = score
        self.total = total
        self.winner = winner
        self.loser = loser
        self.moves = moves

    def __repr__(self) -> str:
        return f'Result(score: {self.score}, winner: {self.winner}, loser: {self.loser}, move: {self.moves})'


def do_work(controller: controller.ComputerController, task: Task, max_depth: int) -> Result:
    node = controller.compute(-task.player * (-1) ** controller.precompute_depth, max_depth)
    node.move = task.moves[-1]
    return Result(node.score, node.total, node.winner, node.loser, task.moves)


class MasterController(controller.Controller):
    def __init__(self, comm, num_of_processes, b: board.Board, ctl: controller.ComputerController):
        super().__init__(b)
        self.comm = comm
        self.num_of_processes = num_of_processes
        self.controller = ctl
        self.controller.board = self.board

        self._recv_thread = threading.Thread(target=self._recv_msg)

        self._task_queue = queue.Queue()
        self._request_queue = queue.Queue()
        self._response_queue = queue.Queue()

        self.stopped = False

        self._recv_thread.start()

    def _recv_msg(self):
        totals = [0, 0]
        while True:
            msg: Message = self.comm.recv()
            common.log(f'got message {msg}')
            if msg.tag == DONE_TAG:
                common.log('detected done - exiting')
                return
            elif msg.tag == REQUEST_TAG:
                totals[0] += 1
                common.log(f'got request from {msg.value} {totals[0]}')
                self._request_queue.put(msg.value)
            elif msg.tag == RESULT_TAG:
                totals[1] += 1
                common.log(f'received result ({totals[1]})')
                self._return_response(msg.value)
            else:
                raise Exception(msg)

    def _forward_task(self, task: Task):
        self.comm.isend(Message(TASK_TAG, task), dest=task.worker, tag=TASK_TAG)
        common.log(f'sent task to {task.worker}')

    def _return_response(self, result: Result):
        self._response_queue.put(result, block=False)

    def _work(self):
        while True:
            task: Task = self._task_queue.get()
            # common.log(f'got task {task}')
            b = board.Board(task.state)
            self.controller.board = b
            response = do_work(self.controller, task, self.controller.max_depth - self.controller.precompute_depth)
            # common.log(f'putting response {response} to queue')
            self._response_queue.put(response)

    @staticmethod
    def _create_tasks(root: tree.Node, max_depth=2) -> List[Task]:
        def recurse(existing_moves: List[int], move: int, depth: int, node: tree.Node) -> List[Task]:
            result = []
            if node.winner or node.loser:
                return result
            if move is not None:
                existing_moves.append(move)
            for child in node.children:
                m = child.move
                if depth < max_depth:
                    result += recurse(existing_moves.copy(), m, depth + 1, child)
                else:
                    result.append(Task(None, child.state, existing_moves.copy() + [m], child.player))
            if not node.children:
                return [Task(None, node.state, existing_moves.copy(), node.player)]
            return result

        return recurse([], None, 1, root)

    @measure.log
    def play(self, player: int) -> int:
        root = self.controller.create_tree(self.board.copy(), player, 2)
        # common.log(f'created root {root.tree()}')
        tasks = self._create_tasks(root, max_depth=2)
        num_of_tasks = len(tasks)

        for task in tasks:
            worker = self._request_queue.get()
            task.worker = worker
            self._forward_task(task)
            # common.log(f'task put on queue: {task}')

        for i in range(num_of_tasks):
            result = self._response_queue.get()
            root_node = root.get_move(*result.moves)
            root_node.winner = result.winner
            root_node.loser = result.loser
            root_node.score = result.score
            root_node.total = result.total
        max_depth = self.controller.max_depth
        self.controller.max_depth = self.controller.precompute_depth
        result = self.controller.play(player, root)
        self.controller.max_depth = max_depth
        return result

    def done(self):
        self.stopped = True
        for i in range(0, self.num_of_processes + 1):
            self.comm.send(Message(DONE_TAG, True), dest=i, tag=DONE_TAG)


class Worker:
    def __init__(self, rank: int, comm, ctl: controller.ComputerController):
        self.rank = rank
        self.comm = comm
        self.controller = ctl

    def run(self):
        while True:
            request = Message(REQUEST_TAG, self.rank)
            self.comm.isend(request, dest=0, tag=REQUEST_TAG)
            common.log('sent request')

            message: Message = self.comm.recv(source=0)

            if message.tag == DONE_TAG:
                common.log('exiting')
                return

            result, state = self._work(message.value)
            self.comm.isend(Message(RESULT_TAG, result), dest=0, tag=RESULT_TAG)
            common.log('sent result')
            del state
            del result

    def _work(self, task: Task):
        state = task.state
        b = board.Board(state)
        self.controller.board = b
        common.log(f'received task {task}')

        result = do_work(self.controller, task, self.controller.max_depth - self.controller.precompute_depth)
        common.log(f'calculated result {result}')
        return result, state


if __name__ == '__main__':
    b = board.Board(state=np.array(
        [
            [1, 1, 0, 0, 0, 0, 1],
            [1, 1, 0, 1, 0, -1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
         ]
    ))
    root = controller.ComputerController.create_tree(b, 1, 3)
    print(root.tree())
    tasks = MasterController._create_tasks(root, max_depth=3)
    for task in tasks:
        print(task)
    print(b.table())
    print(root.get_move(5, 4, 4).chain())
    # print(controller.ComputerController.create_tree(b, 1, 2).tree())
