#!/usr/bin/env bash

set -e

kernel_version=$(cut -d- -f1 <<< `uname -r`)
echo "found kernel version: '$kernel_version'"
tag="v4.11.0"

if [ ! -d /tmp/iproute2 ]; then
    pushd /tmp
    git clone https://kernel.googlesource.com/pub/scm/linux/kernel/git/shemminger/iproute2
fi
pushd /tmp/iproute2

git checkout $tag
echo "installing iproute2 tag: $tag"
make
make install
