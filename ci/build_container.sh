#!/bin/bash

echo $BRANCH
docker build --pull -t miniworldproject/miniworld_core:${BRANCH-master} -f ci/Dockerfile $@ --build-arg BRANCH=${BRANCH-master} .