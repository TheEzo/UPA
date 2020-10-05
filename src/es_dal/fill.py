#!/usr/bin/python3

import os
import sys
from json import loads

from .elastic import Elastic


def fill_data(delete=True):
    data_dir = os.path.join(os.path.dirname(__file__), '../../data')
    es = Elastic()
    for file in os.listdir(data_dir):
        index_name = file.split('.')[0]
        if delete:
            es.indices.delete(index_name, ignore=[400, 404])

        sys.stdout.write(f'Populating index "{index_name}"...')
        with open(os.path.join(data_dir, file), 'r') as f:
            data = loads(f.read())
        for record in data['data']:
            es.index(index_name, record)
        print(f' (done)')
