#!/bin/bash

cd "$(dirname "$0")"

source venv/bin/activate

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)/venv/lib/python3.13/site-packages/nvidia/cudnn/lib
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)/venv/lib/python3.13/site-packages/nvidia/cublas/lib

python main.py