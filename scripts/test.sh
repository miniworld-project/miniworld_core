#!/usr/bin/env bash
time docker-compose -f docker-compose-dev.yml exec core pytest -x -vvvvv -m "not examples" tests/ $@
