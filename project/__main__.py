from elasticsearch import Elasticsearch
import mysql.connector

if __name__ == '__main__':
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
    
    db = mysql.connector.connect(
        host="localhost",
        port=3306,
        user='root'
    )

    
