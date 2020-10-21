#!/usr/bin/python3

import datetime
import logging
import os
import mysql.connector
import sys

from es_dal.fill import fill_data

# lower level to see logs even from other modules (elasticsearch, mysql.connector etc.)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('main')


def main():
    logger.info("Started: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))

    # fill specific sources
    fill_data(data=['https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/nakaza.json',
                    os.path.join(os.path.dirname(__file__), '..', 'data', 'nakaza.csv')])
    
    # fill data from data folder
    # fill_data(data=[os.path.join(os.path.dirname(__file__), '..', 'data')]):

    db = mysql.connector.connect(
        host="localhost",
        port=3306,
        user='root'
    )
    logger.info(db)

    logger.info("Finished: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))


if __name__ == '__main__':
    sys.exit(main())
