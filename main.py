import controller
import parallel
import board
import game
from mpi4py import MPI

if __name__ == '__main__':
    import sys

    num_of_processes = int(sys.argv[1])
    max_depth = int(sys.argv[2])

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    if rank == 0:
        print('initializing master')
        board = board.Board()
        master = parallel.MasterController(comm, num_of_processes, board)
        game = game.Game(board, controller.UserController(board), master)
        game.run(verbose=True)
    else:
        print(f'initializing slave {rank}')
        ctl = controller.ComputerController(None, max_depth - 1)
        slave = parallel.Slave(comm, ctl)
        slave.run()
