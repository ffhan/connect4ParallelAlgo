#!/bin/bash

workers=$1
total_proc=$(($workers + 1))
mpiexec --hostfile hostfile -n $total_proc python main.py $total_proc $2