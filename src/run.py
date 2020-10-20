#!/usr/bin/python3

import datetime
import logging
import os
import mysql.connector
import sys

from es_dal.fill import fill_data, upload_file


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('main')


def main():
    logger.info("Started: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    upload_file(os.path.join(os.path.dirname(__file__), '../data/nakaza.csv'))
    logger.info("First file uploaded: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    return 0
    # fill_data()
    db = mysql.connector.connect(
        host="localhost",
        port=3306,
        user='root'
    )
    logger.info("Finished: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))


if __name__ == '__main__':
    sys.exit(main())
