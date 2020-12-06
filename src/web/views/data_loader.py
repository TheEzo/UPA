import shapefile
import math
import copy
import random
import sys
import os

from flask import render_template
# from flask import current_app as app
from flask.views import MethodView
from flask import Flask, make_response
import numpy as np

from os import listdir
from os.path import isfile, join
from os import walk
import os.path

import pathlib

def get_files_list():
    files_path = os.path.join(os.path.dirname(__file__), '..', 'data')
    extensions = {'.csv', '.json'}

    (_, _, filenames) = next(os.walk(files_path))

    filenames = [f for f in filenames if os.path.splitext(f)[1] in extensions]
    
    return filenames