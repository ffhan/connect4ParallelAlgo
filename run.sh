#!/bin/bash

mpiexec --hostfile hostfile -n $1 python main.py $1 $2