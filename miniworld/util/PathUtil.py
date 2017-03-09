from miniworld.Constants import PATH_TMP, PATH_LOGS
import os

__author__ = 'Nils Schmidt'

'''
Utility for path constructions.
'''

def get_temp_file_path(file_name):
    ''' Get the path to a temporary file named `file_name` '''
    return os.path.join(PATH_TMP, file_name)

def get_log_file_path(log_file_name):
    ''' Get the path to the `log_file_name` '''
    return os.path.join(PATH_LOGS, log_file_name)
