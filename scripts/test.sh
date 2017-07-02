#!/usr/bin/env bash
time BRANCH=${BRANCH-$(git symbolic-ref --short HEAD)} docker-compose -f docker-compose-dev.yml exec core pytest -x -vvvvv -m "not examples" tests/ $@
