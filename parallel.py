import threading
import queue

from typing import List

import measure
import numpy as np

import board
import common
import controller

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
    def __init__(self, worker: int, state: np.ndarray, move: int, player: int):
        self.player = player
        self.move = move
        self.worker = worker
        self.state = state

    def __repr__(self) -> str:
        return f'Task(player: {self.player}, move: {self.move}, worker:{self.worker})'


class Result:
    def __init__(self, score: float, winner: bool, loser: bool, move: int):
        self.score = score
        self.winner = winner
        self.loser = loser
        self.move = move

    def __repr__(self) -> str:
        return f'Result(score: {self.score}, winner: {self.winner}, loser: {self.loser}, move: {self.move})'


def do_work(controller: controller.ComputerController, task: Task, board: board.Board) -> Result:
    node = controller.play_node(task.player, board, task.move, task.player, None)
    if node.status != board.WIN:
        node = controller.compute(task.player * -1)
    node.move = task.move
    return Result(common.calculate_score(-node.score, node.total), node.winner, node.loser, node.move)


class MasterController(controller.Controller):
    def __init__(self, comm, num_of_processes, board, controller):
        super().__init__(board)
        self.comm = comm
        self.num_of_processes = num_of_processes
        self.controller = controller

        self._forward_thread = threading.Thread(target=self._forward_tasks, daemon=True)
        self._recv_thread = threading.Thread(target=self._return_response, daemon=True)
        self._work_thread = threading.Thread(target=self._work, daemon=True)

        self._task_queue = queue.Queue()
        self._response_queue = queue.Queue()

        self._forward_thread.start()
        self._recv_thread.start()
        self._work_thread.start()

    def _forward_tasks(self):
        while True:
            request: Message = self.comm.recv(tag=REQUEST_TAG)
            common.log(f'got request from {request.value}')
            worker = request.value
            task = self._task_queue.get()
            task.worker = worker
            self.comm.isend(Message(TASK_TAG, task), dest=task.worker, tag=TASK_TAG)
            common.log(f'sent task to {task.worker}')

    def _return_response(self):
        while True:
            result: Message = self.comm.recv(tag=RESULT_TAG)
            common.log(f'received result')
            self._response_queue.put(result.value)

    def _work(self):
        while True:
            task: Task = self._task_queue.get()
            common.log(f'got task {task}')
            b = board.Board(task.state)
            self.controller.board = b
            response = do_work(self.controller, task, b)
            common.log(f'putting response {response} to queue')
            self._response_queue.put(response)

    @measure.log
    def play(self, player: int) -> int:
        num_of_tasks = len(self.board.valid_moves)
        common.log('sent bcast')
        for move in self.board.valid_moves:
            task = Task(-1, np.copy(self.board.state), move, player)
            self._task_queue.put(task)

        results: List[Result] = []
        for i in range(num_of_tasks):
            results.append(self._response_queue.get())
        results = sorted(results, key=lambda t: t.score, reverse=True)
        return results[0].move

    def done(self):
        self.comm.bcast(Message(DONE_TAG, True), root=0)


class Slave:
    def __init__(self, rank: int, comm, ctl: controller.ComputerController):
        self.rank = rank
        self.comm = comm
        self.controller = ctl

    def run(self):
        while True:
            request = Message(REQUEST_TAG, self.rank)
            self.comm.isend(request, dest=0, tag=REQUEST_TAG)

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
        common.log('received bcast')
        b = board.Board(state)
        self.controller.board = b
        common.log(f'received task {task}')

        result = do_work(self.controller, task, b)
        common.log(f'calculated result {result}')
        return result, state
