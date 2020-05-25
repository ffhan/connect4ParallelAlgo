import queue
import threading
from typing import List

import numpy as np

import board
import common
import controller
import measure
import tree

REQUEST_TAG = 50  # tag used for request messages
TASK_TAG = 101  # tag used for task messages
RESULT_TAG = 102  # tag used for result messages
DONE_TAG = 103  # tag used for indicating run end


class Message:
    """
    Message envelope
    """

    def __init__(self, tag, value):
        self.tag = tag
        self.value = value

    def __repr__(self):
        return f'Message(tag: {self.tag}, value: {self.value})'


class Task:
    """
    Task that has to be computed on the worker.
    """

    def __init__(self, worker: int, state: np.ndarray, moves: List[int], player: int):
        self.player = player
        self.moves = moves
        self.worker = worker
        self.state = state

    def __repr__(self) -> str:
        return f'Task(player: {self.player}, moves: {self.moves}, worker:{self.worker})'


class Result:
    """
    Computation result returned from the worker.
    """

    def __init__(self, score: int, total: int, winner: bool, loser: bool, moves: List[int]):
        self.score = score
        self.total = total
        self.winner = winner
        self.loser = loser
        self.moves = moves

    def __repr__(self) -> str:
        return f'Result(score: {self.score}, winner: {self.winner}, loser: {self.loser}, move: {self.moves})'


def do_work(controller: controller.ComputerController, task: Task, max_depth: int) -> Result:
    """
    Does the computation work represented by the Task.

    :param controller: computer controller that will do the computation.
    :param task: task that has to be executed
    :param max_depth: maximum score tree depth to be computed on the worker
    :return: computed result
    """
    # compute for player -(-1)^(precomputed tree depth), compute max depth on the worker
    node = controller.compute(-task.player * (-1) ** controller.precompute_depth, max_depth)
    node.move = task.moves[-1]  # subtree root node move is last task move
    return Result(node.score, node.total, node.winner, node.loser, task.moves)


class MasterController(controller.Controller):
    """
    Controller run on the master node.
    It uses a computer controller to create a pre-computed tree, create tasks, send them to workers,
    collect results and then compute the final score -> turning the pre-computed tree into a score tree.

    It's also possible to run work on the master node, but it's currently disabled because Pythons' GIL
    slows communication with other nodes considerably.
    """

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
        """
        Receive messages and act accordingly to the tag.
        :return:
        """
        totals = [0, 0]
        while True:
            msg: Message = self.comm.recv()  # receive any message tag
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
        """
        Send a task to a worker.

        :param task: task to execute on the worker
        :return:
        """
        self.comm.isend(Message(TASK_TAG, task), dest=task.worker, tag=TASK_TAG)
        common.log(f'sent task to {task.worker}')

    def _return_response(self, result: Result):
        """
        Put Result in response queue.
        :param result: received computation result
        :return:
        """
        self._response_queue.put(result, block=False)

    def _work(self):
        """
        Do the work on the master node.
        Not recommended for usage.
        :return:
        """
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
        """
        Create tasks from the pre-computed tree.

        :param root: root node of the tree
        :param max_depth: maximum pre-compute depth (in case we have a deeper tree)
        :return: list of tasks
        """

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
        """
        Selects an optimal move based on the board state and the current player ID.

        It creates a pre-computed tree on the master, then creates tasks based on that tree.
        Each task is actually a leaf node in the pre-computed tree.
        Afterwards it sends tasks to workers and applies results (scores) to the pre-computed tree created before,
        effectively creating a score tree.
        Finally, it chooses the optimal move for the board state based on the score tree.

        :param player: current player ID
        :return: optimal move
        """
        # create a pre-computed tree of depth 2
        root = self.controller.create_tree(self.board.copy(), player, 2)
        # common.log(f'created root {root.tree()}')
        # create tasks from the pre-computed tree (1 task for 1 leaf node)
        tasks = self._create_tasks(root, max_depth=2)
        num_of_tasks = len(tasks)

        # send out tasks
        for task in tasks:
            worker = self._request_queue.get()
            task.worker = worker
            self._forward_task(task)
            # common.log(f'task put on queue: {task}')

        # update pre-computed tree from results
        for i in range(num_of_tasks):
            result = self._response_queue.get()
            root_node = root.get_move(*result.moves)
            root_node.winner = result.winner
            root_node.loser = result.loser
            root_node.score = result.score
            root_node.total = result.total

        # set controller max depth to be pre-compute depth
        # (because we want to score only the existing nodes, not generate new ones)
        max_depth = self.controller.max_depth
        self.controller.max_depth = self.controller.precompute_depth
        # compute the optimal move based on the pre-computed tree
        result = self.controller.play(player, root)
        # revert controller max depth
        self.controller.max_depth = max_depth
        return result

    def done(self):
        """
        Stop all local threads and workers.
        :return:
        """
        self.stopped = True
        for i in range(0, self.num_of_processes + 1):  # send to every node including ourselves
            self.comm.send(Message(DONE_TAG, True), dest=i, tag=DONE_TAG)


class Worker:
    """
    Worker node object
    """

    def __init__(self, rank: int, comm, ctl: controller.ComputerController):
        self.rank = rank
        self.comm = comm
        self.controller = ctl

    def run(self):
        """
        Run the worker.
        Sends requests for tasks, receives tasks, computes a sub tree for each task and returns the result to the master.
        :return:
        """
        while True:
            request = Message(REQUEST_TAG, self.rank)
            # send a request
            self.comm.isend(request, dest=0, tag=REQUEST_TAG)
            common.log('sent request')

            # receive a task (or DONE event)
            message: Message = self.comm.recv(source=0)

            if message.tag == DONE_TAG:  # exit if DONE event
                common.log('exiting')
                return

            # do the computation
            result, state = self._work(message.value)
            # send the result
            self.comm.isend(Message(RESULT_TAG, result), dest=0, tag=RESULT_TAG)
            common.log('sent result')
            # free up memory
            del state
            del result

    def _work(self, task: Task):
        """
        Does the actual work: updates the controller board from the task state and calls do_work.
        :param task: task to complete
        :return: result and result state
        """
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
    # create a pre-computed tree of depth 3
    root = controller.ComputerController.create_tree(b, 1, 3)
    print(root.tree())
    # create tasks based on the pre-computed tree
    tasks = MasterController._create_tasks(root, max_depth=3)
    for task in tasks:
        print(task)
    print(b.table())
    # get node that represents move state [5,4,4] and print the moves
    print(root.get_move(5, 4, 4).chain())
    # print(controller.ComputerController.create_tree(b, 1, 2).tree())
