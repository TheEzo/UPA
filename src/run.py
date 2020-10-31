#!/usr/bin/python3

import sys

from src.web.views import init_views

import os
from src.es_dal.fill import fill_data
import mysql.connector
import argparse
from flask import Flask, render_template, redirect, url_for


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--web', action='store_true', help='Run Web')
    parser.add_argument('-f', '--fill', action='store_true', help='Fill data into databases')

    args = parser.parse_args()

    if args.web:
        app = create_app()
        app.run(host='0.0.0.0', port='80', debug=True)
    elif args.fill:
        fill_data()


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
