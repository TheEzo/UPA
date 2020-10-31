#!/usr/bin/python3

import argparse
import datetime
import logging
import os
import sys

import mysql.connector
import mysql.connector
from flask import Flask

from src.es_dal.fill import fill_data
from src.web.views import init_views

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('main')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--web', action='store_true', help='Run Web')
    parser.add_argument('-f', '--fill', action='store_true', help='Fill data into databases')

    args = parser.parse_args()

    if args.web:
        app = create_app()
        app.run(host='0.0.0.0', port='80', debug=True)
    elif args.fill:
        logger.info("Started: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))

        # fill specific sources
        fill_data(data=['https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/nakaza.json',
                        os.path.join(os.path.dirname(__file__), '..', 'data', 'nakaza.csv')])

        db = mysql.connector.connect(
            host="localhost",
            port=3306,
            user='root'
        )
        logger.info(db)

        logger.info("Finished: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))


def create_app():
    # create and configure the app
    app = Flask(__name__, template_folder='web/templates')
    app.config.from_mapping(
        SECRET_KEY='UPA',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'root'
    app.config['MYSQL_DB'] = 'upa'

    init_views(app)

    return app


if __name__ == '__main__':
    sys.exit(main())
