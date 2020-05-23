import sys
import controller
import numpy as np
import board
from typing import List
from mpi4py import MPI

TASK_TAG = 101
RESULT_TAG = 102


class Task:
    def __init__(self, worker: int, move: int, player: int):
        self.player = player
        self.move = move
        self.worker = worker

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


class MasterController(controller.Controller):
    def __init__(self, comm, num_of_processes, board):
        super().__init__(board)
        self.comm = comm
        self.num_of_processes = num_of_processes

    def play(self, player: int) -> int:
        tasks = []
        workers = set([i + 1 for i in range(self.num_of_processes - 1)])
        self.comm.Bcast([self.board.state, MPI.INT], root=0)
        print('sent bcast')
        for move in self.board.valid_moves:
            task = Task(workers.pop(), move, player)
            tasks.append(task)
            self.comm.isend(task, dest=task.worker, tag=TASK_TAG)
            print(f'sent task to {task.worker}')
        results: List[Result] = []
        for task in tasks:
            result: Result = self.comm.recv(source=task.worker, tag=RESULT_TAG)
            print(f'received result from {task.worker}')
            results.append(result)
        results = sorted(results, key=lambda t: t.score, reverse=True)
        return results[0].move


class Slave:
    def __init__(self, comm, ctl: controller.ComputerController):
        self.comm = comm
        self.controller = ctl

    @staticmethod
    def _calc_score(score, total) -> float:
        if total == 0:
            return 0
        return score / total

    def run(self):
        while True:
            state = np.empty((board.Board.height, board.Board.width))
            self.comm.Bcast(state, root=0)
            print('received bcast')
            b = board.Board(state)
            self.controller.board = b

            task: Task = self.comm.recv(source=0, tag=TASK_TAG)
            print(f'received task {task}')
            node = self.controller.play_node(task.player, b, task.move, task.player, None)
            if node.status != b.WIN:
                node = self.controller.compute(task.player)
            node.move = task.move
            result = Result(self._calc_score(node.score, node.total), node.winner, node.loser, node.move)
            print(f'calculated result {result}')
            self.comm.isend(result, dest=0, tag=RESULT_TAG)
            print('sent result')
            del state
            del result
