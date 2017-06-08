#!/usr/bin/env bash

set -e

kernel_version=$(cut -d- -f1 <<< `uname -r`)
echo "found kernel version: '$kernel_version'"
# quickfix
if [ kernel_version == "4.4.0" ]
    fallback_kernel="4.2.0"
    echo "using kernel version $fallback_kernel"
    then kernel_version=$fallback_kernel
fi
tag="v$kernel_version"

if [ ! -d iproute2 ]; then
    git clone https://kernel.googlesource.com/pub/scm/linux/kernel/git/shemminger/iproute2
    pushd iproute2
else
    pushd iproute2
fi

git checkout $tag
#git pull origin master
echo "installing iproute2 tag: $tag"
# make clean
make
make install


