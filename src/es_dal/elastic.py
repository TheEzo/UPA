#!/usr/bin/python3

from elasticsearch import Elasticsearch


class Elastic(Elasticsearch):
    def __init__(self):
        Elasticsearch.__init__(self, [{'host': 'localhost', 'port': 9200}])

