#!/usr/bin/python3

import sys
sys.path.append("..")

import argparse
import datetime
import logging
import os

from business_logic.helpers import delete_all
from sql_dal import sql_helpers
from generate_graphs import generate, generate_township
from business_logic.custom_query_graph import generate_custom_query
from web.views.base import copy_data_file
from es_dal.fill import fill_data

from flask import Flask
from web.views import init_views

import sql_dal.import_data as sqlim
from web.core.session import db_session
import web.core.model as models
from es_dal.elastic import Elastic

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('main')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--web', action='store_true', help='Run Web')
    parser.add_argument('-f', '--fill', action='store_true', help='Fill data into databases')
    parser.add_argument('-m', '--move', action='store_true', help='Imports data from NoSQL to MySQL')
    parser.add_argument('-q', '--queries', action='store_true', help='Answer all queries')
    parser.add_argument('-e', '--erase', action='store_true', help='Deletes both dbs data')

    args = parser.parse_args()

    logger.info("Started: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    work_folder_path = os.path.join(os.path.dirname(__file__), '..', 'work')
    if not os.path.exists(work_folder_path):
        os.mkdir(work_folder_path)
    if args.web:
        app = create_app()
        app.run(host='0.0.0.0', port='80', debug=True)
    elif args.fill:
        files = ['states', 'regions', 'neighbours', 'infected', 'recovered', 'dead']

        es = Elastic()
        es.indices.delete('*')

        for f in files:
            copy_data_file(f)
            path = os.path.join(work_folder_path, f'{f}.csv')
            fill_data(path)
        
        logger.info("Finished fill: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    elif args.move:
        models.Base.metadata.drop_all()
        models.Base.metadata.create_all()

        sql_helpers.import_all()
        
        with db_session() as db:
            db.add(models.DataConsistency(code='valid'))
            db.commit()

        logger.info("Finished move: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    elif args.queries:
        generate()
        generate_township()
        generate_custom_query()

        logger.info("Finished queries: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    elif args.erase:
        delete_all()

        logger.info("Finished erase: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    else:
        app = create_app()
        app.run(host='0.0.0.0', port='80', debug=True)

    logger.info("Finished: {0}".format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))


def create_app():
    # create and configure the app
    app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
    app.config.from_mapping(
        SECRET_KEY='UPA',
        UPLOAD_FOLDER='work/'
    )

    init_views(app)

    return app
   

if __name__ == '__main__':
    models.Base.metadata.create_all()

    with db_session() as db:
        imp_row = db.query(models.DataConsistency).filter(models.DataConsistency.code == 'import').first()
    
    if imp_row is not None:
        delete_all()

    sys.exit(main())
