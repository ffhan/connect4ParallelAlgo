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

    if rank == 0:
        common.log('initializing master')
        board = board.Board()
        master = parallel.MasterController(comm, num_of_processes, board)
        game = game.Game(board, controller.UserController(board), master)
        game.run(verbose=True)
        comm.bcast(parallel.Message(parallel.DONE_TAG, True), root=0)
    else:
        common.log(f'initializing slave {rank}')
        ctl = controller.ComputerController(None, max_depth - 1)
        slave = parallel.Slave(comm, ctl)
        slave.run()
        common.log(f'slave {rank} exited')
