#!/usr/bin/python3

import csv
import datetime
import json
import logging
import os
import sys
import urllib.request

from .elastic import Elastic


logger = logging.getLogger('nosql_fill')


def is_url(url):
    try:
        status_code = urllib.request.urlopen(url).getcode()
        if status_code == 200:
            return True
    except:
        pass
    logger.warning('Url is not valid: {0}'.format(url))
    return False


def fill_data(data=None, work_dir=os.path.join(os.path.dirname(__file__), '..', '..', 'work'), delete=True):
    # data to list
    data = [] if data is None else data  # non-mutable data argument
    data = data if type(data) is list else [data]  # data as a list

    if not os.path.exists(work_dir):  # assure work directory exists
        os.makedirs(work_dir)

    for data_src in data:  # upload data to database
        if os.path.isdir(data_src):  # directory
            # TODO: do we want this to be recursive?
            for data_file in os.listdir(data_src):
                if os.path.isfile(data_src):
                    upload_file(data_file, delete=delete)
        elif os.path.isfile(data_src):  # file
            upload_file(data_src, delete=delete)
        elif '/' in data_src and is_url(data_src):  # url
            tmp_file_name = os.path.join(work_dir, data_src.rsplit('/', 1)[1])  # workdir + filename
            with urllib.request.urlopen(data_src) as response, open(tmp_file_name, 'wb') as tmp_file:
                data = response.read()  # a `bytes` object, therefore "wb" mode
                tmp_file.write(data)
            upload_file(tmp_file_name, delete=delete)


def upload_file(src, delete=True):
    logger.info('Upload file to NoSQL database\n\t{0}\n\t{1}'.format(src, datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    es = Elastic()
    index_name, src_type = os.path.basename(src).rsplit('.', 1)
    src_type = src_type.lower()
    logger.info("Database index: {0}, file type: {1}".format(index_name, src_type))
    if delete:
        es.indices.delete(index_name, ignore=[400, 404])
    if src_type == 'csv':
        # First three characters of a file can be 'Byte order mark', use encoding to skip them
        # Otherwise it will corrupt the first column name like ['ï»¿MINUTE', 'HOUR', ...]
        with open(src, encoding="utf-8-sig", newline='') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            columns = []
            for row in csv_reader:
                if not columns:  # first line defines column names
                    columns = row
                    logger.info("CSV columns: {}".format(columns))
                    continue
                row_data = {}  # add keys to values (list to dict conversion)
                for col in columns:
                    row_data[col] = row[columns.index(col)]
                es.index(index_name, row_data)  # insert data to DB
    elif src_type == 'json':
        with open(src,) as f:
            data = json.load(f)
        for record in data['data']:
            es.index(index_name, record)  # insert data to DB
    else:
        logger.error("Unsupported file type: {0}".format(src_type))
    logger.info('File uploaded to NoSQL database:\n\t{0}\n\t{1}'.format(src, datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
