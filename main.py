from mpi4py import MPI

import board
import common
import controller
import game
import parallel

if __name__ == '__main__':
    import sys

    total_processes = int(sys.argv[1])
    num_of_workers = total_processes - 1  # minus the master

    max_depth = int(sys.argv[2])

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    common.VERBOSE = False
    common.PPRINT = False

    ctl = controller.ComputerController(None, max_depth,
                                        precompute_depth=2)  # pre-compute depth for controller is 2 (max 49 tasks)
    if rank == 0:  # code for master
        common.log('initializing master')
        board = board.Board()
        master = parallel.MasterController(comm, num_of_workers, board, ctl)  # initialize master
        game = game.Game(board, controller.UserController(board), master)
        game.run(verbose=True)  # run game loop
        master.done()  # indicate MPI ending
    else:  # code for worker
        common.log(f'initializing worker {rank}')
        worker = parallel.Worker(rank, comm, ctl)  # initialize worker
        worker.run()
        common.log(f'worker {rank} exited')
