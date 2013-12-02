# -*- coding: utf-8 -*-

from os import listdir
from os.path import join as path_join
from os.path import isfile as path_isfile

def os_listdir(path):
    return listdir(path)

def os_path_join(a, *b):
    return path_join(a, *b)

def os_path_isfile(path):
    return path_isfile(path)