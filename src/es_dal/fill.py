#!/usr/bin/python3

import csv
import logging
import os
import sys
import json

from .elastic import Elastic


logger = logging.getLogger('NoSQL fill')


def fill_data(delete=True):
    data_dir = os.path.join(os.path.dirname(__file__), '../../data')
    es = Elastic()
    for file in os.listdir(data_dir):
        upload_file(file, delete=delete)
        continue

        logging.info('Insert file {0}'.format(file))
        index_name = file.split('.')[0]
        if delete:
            es.indices.delete(index_name, ignore=[400, 404])  # HTTP statuses

        sys.stdout.write(f'Populating index "{index_name}"...')
        with open(os.path.join(data_dir, file),) as f:
            logging.info('load json')
            data = json.load(f)
        for record in data['data']:
            logging.info('Insert record')
            es.index(index_name, record)
        print(f' (done)')

def upload_file(src, delete=True):
    logger.info('Upload file {0} to NoSQL database'.format(src))
    es = Elastic()
    index_name, src_type = os.path.basename(src).rsplit('.', 1)
    src_type = src_type.lower()
    if delete:
        es.indices.delete(index_name, ignore=[400, 404])
    if src_type == 'csv':
        with open(src, newline='') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            columns = []
            data = []
            for row in csv_reader:
                if not columns:
                    columns = row
                    logger.info("CSV file columns: {}".format(columns))
                    continue
                row_data = {}
                for col in columns:
                    row_data[col] = row[columns.index(col)]
                print(row_data)
                es.index(index_name, row_data)
                # print(row)
    elif src_type == 'json':
        with open(src,) as f:
            data = json.load(f)
        sys.stdout.write(f'Populating index "{index_name}"...')
        for record in data['data']:
            logger.info('Insert record')
            es.index(index_name, record)
    else:
        logger.error("Unsupported file type: {0}".format(src_type))

    print(f' (done)')
