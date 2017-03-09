#!/bin/bash

./cleanup.sh
export PYTHONPATH=$PWD:$PYTHONPATH
./miniworld/rpc/RPCServer.py server
