from mpi4py import MPI

import board
import common
import controller
import game
import parallel

if __name__ == '__main__':
    import sys

    num_of_processes = int(sys.argv[1])
    max_depth = int(sys.argv[2])

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    common.VERBOSE = True

    ctl = controller.ComputerController(None, max_depth, precompute_depth=2)
    if rank == 0:
        common.log('initializing master')
        board = board.Board()
        master = parallel.MasterController(comm, num_of_processes, board, ctl)
        game = game.Game(board, controller.UserController(board), master)
        game.run(verbose=True)
        master.done()
    else:
        common.log(f'initializing slave {rank}')
        slave = parallel.Worker(rank, comm, ctl)
        slave.run()
        common.log(f'slave {rank} exited')
