#!/usr/bin/python3

import sys

from src.es_dal.fill import fill_data
import mysql.connector


def main():
    fill_data()
    # db = mysql.connector.connect(
    #     host="localhost",
    #     port=3306,
    #     user='root'
    # )


if __name__ == '__main__':
    sys.exit(main())
