#!/usr/bin/env bash

modprobe ebtables
set -e
pip3 install --upgrade .
mwserver
