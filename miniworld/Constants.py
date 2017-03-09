import os
from os.path import join

__author__ = 'Nils Schmidt'

PROJECT_NAME = "MiniWorld"

PATH_CLEANUP_SCRIPT = os.path.relpath("cleanup.sh", os.getcwd())

# temp files ho here
PATH_TMP = "/tmp/%s" % PROJECT_NAME

# logs here
PATH_LOGS = join(PATH_TMP, "logs/")

PATH_MARBURG_OSM_MAP = join('%s' % os.getcwd(), 'osm_marburg.db')

# relative to cwd
PATH_MINIWORLD_DIR = ""
MINIWORLD_CONFIG_NAME = "config.json"

RPC_SERVER_LOCAL_ADDR = 'http://localhost:5001/RPC2'
