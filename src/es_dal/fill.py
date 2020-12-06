#!/usr/bin/python3

import sys
sys.path.append("..")

import csv
import datetime
import json
import logging
import os
import urllib.error
import urllib.request
import ssl
import pandas as pd
from .elastic import Elastic
from elasticsearch import helpers
from business_logic.helpers import get_filename_without_extension
from elasticsearch.client import IndicesClient

logger = logging.getLogger('nosql_fill')
context = ssl._create_unverified_context()

def is_url(url):
    """
    Check if given string is an url
    :param url: string that to be checked
    :type url: str
    :return: True if string is an URl that can be accessed, False otherwise
    :rtype: bool
    """
    try:
        status_code = urllib.request.urlopen(url, context=context).getcode()
        if status_code == 200:
            return True
    except urllib.error.URLError as e:  # URLError is a base class for urllib exceptions
        logger.warning(str(e.reason))
        logger.warning('Url is not valid: {0}'.format(url))
    return False


def fill_data(data=None, work_dir=os.path.join(os.path.dirname(__file__), '..', '..', 'work'), delete=True):
    """
    Get data from given sources and pass them to NoSQL database.

    :param data: files, directories and urls to get data from and upload to database
    :param work_dir: directory where to create temporary files
    :param delete: delete existing indexes in database if already exists
    :type data: list or str
    :type work_dir: str
    :type delete: bool
    """
    data = [] if data is None else data  # non-mutable data argument
    data = data if type(data) is list else [data]  # data is a list

    if not os.path.exists(work_dir):  # assure work directory exists
        os.makedirs(work_dir)

    for data_src in data:  # upload data to database
        if os.path.isdir(data_src):  # directory
            for base_dir, _, files in os.walk(data_src):
                for data_file in files:
                    upload_file(os.path.join(base_dir, data_file), delete=delete)
        elif os.path.isfile(data_src):  # file
            upload_file(data_src, delete=delete)
        elif '/' in data_src and is_url(data_src):  # url
            tmp_file_name = os.path.join(work_dir, data_src.rsplit('/', 1)[1])  # workdir + filename
            with urllib.request.urlopen(data_src, context=context) as response, open(tmp_file_name, 'wb') as tmp_file:
                data = response.read()  # a `bytes` object, therefore "wb" mode
                tmp_file.write(data)
            upload_file(tmp_file_name, delete=delete)
        else:
            logger.error("Unrecognized data type (not a file/directory/url): {0}".format(data_src))


def upload_file(src, delete=True):
    """
    Get data from given sources and pass them to NoSQL database.

    :param src: path of file to be read, parsed and uploaded to database. can be CSV of JSON
    :param delete: delete existing indexes in database if already exists
    :type src: str
    :type delete: bool
    """
    logger.info('Upload file to NoSQL database\n\t{0}\n\t{1}'
                ''.format(src, datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    es = Elastic()
    index_name, src_type = os.path.basename(src).rsplit('.', 1)

    index_name = get_filename_without_extension(index_name)

    src_type = src_type.lower()
    logger.info("Database index: {0}, file type: {1}".format(index_name, src_type))
    if delete:
        es.indices.delete(index_name, ignore=[400, 404])
    if src_type == 'csv':
        # First three characters of a file can be 'Byte order mark', use encoding to skip them
        # Otherwise it will corrupt the first column name like ['ï»¿MINUTE', 'HOUR', ...]
        
        es.indices.create(index_name)
        csvfile=pd.read_csv(src, iterator=True, chunksize=5000) 
        
        for i,df in enumerate(csvfile): 
            records=df.where(pd.notnull(df), None).T.to_dict()
            list_records=[records[it] for it in records]
            helpers.bulk(es, list_records, index=index_name)

        es.indices.refresh(index=index_name)
    elif src_type == 'json':
        es.indices.create(index_name)
        chunksize = 5000

        with open(src,) as f:
            data = (json.load(f))['data']

        for i in range(0, len(data), chunksize):
            helpers.bulk(es, data[i:i + chunksize], index=index_name)

        es.indices.refresh(index=index_name)
    else:
        logger.error("Unsupported file type: {0}".format(src_type))
    logger.info('File uploaded to NoSQL database:\n\t{0}\n\t{1}'
                ''.format(src, datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
