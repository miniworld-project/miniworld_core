#!/bin/bash

docker build --pull -t miniworldproject/miniworld_core:${BRANCH-nightly} -f ci/Dockerfile $@ .