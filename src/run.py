#!/usr/bin/python3

import argparse
import datetime
import logging
import os
import sys

import mysql.connector
from flask import Flask

from es_dal.fill import fill_data
from web.views import init_views

import sql_dal.import_data as sqlim
from web.core.model import Base

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('main')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--web', action='store_true', help='Run Web')
    parser.add_argument('-f', '--fill', action='store_true', help='Fill data into databases')
    parser.add_argument('-m', '--move', action='store_true', help='Imports data from NoSQL to MySQL')

    args = parser.parse_args()

    logger.info("Started: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    if args.web:
        app = create_app()
        app.run(host='0.0.0.0', port='80', debug=True)
    elif args.fill:

        # fill specific sources

        get_data_path = lambda file_name : os.path.join(os.path.dirname(__file__), '..', 'data', file_name)

        #fill_data('https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/nakaza.json') #nakaza.csv
        #fill_data('http://apl.czso.cz/iSMS/cisexp.jsp?kodcis=1186&typdat=0&cisvaz=86_275&datpohl=25.11.2020&cisjaz=203&format=2&separator=,') #staty.csv; windows-1250
        #fill_data('http://apl.czso.cz/iSMS/cisexp.jsp?kodcis=108&typdat=1&cisvaz=109_210&datpohl=20.10.2020&cisjaz=203&format=2&separator=,') #kraje_a_okresy.csv; windows-1250

        fill_data(get_data_path('staty.csv'))
        fill_data(get_data_path('kraje_a_okresy.csv'))
        fill_data(get_data_path('sousedni_okresy.csv'))

        fill_data(r'https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/osoby.csv') #osoby (nakazeni)
        fill_data(r'https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/vyleceni.csv') #vyleceni
        fill_data(r'https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/umrti.csv') #umrti

        db = mysql.connector.connect(
            host="localhost",
            port=3306,
            user='root',
            password='root'
        )

        logger.info(db)
        logger.info("Finished fill: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    elif args.move:
        sqlim.import_countries()
        sqlim.import_townships_and_regions()
        sqlim.import_township_neighbours()
        sqlim.import_covid_cases()
        logger.info("Finished move: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    
    logger.info("Finished: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))

def create_app():
    # create and configure the app
    app = Flask(__name__, template_folder='web/templates')
    app.config.from_mapping(
        SECRET_KEY='UPA',
    )

    init_views(app)

    return app


if __name__ == '__main__':
    Base.metadata.create_all()
    sys.exit(main())
