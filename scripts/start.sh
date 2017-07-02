#!/usr/bin/env bash

BRANCH=${BRANCH-$(git symbolic-ref --short HEAD)} docker-compose -f docker-compose-dev.yml up