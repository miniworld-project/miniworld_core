#!/usr/bin/env bash

(./scripts/install_iproute2.sh)
modprobe ebtables
set -e
pip3 install --upgrade .
mwserver
