import os
import sqlalchemy as db
import json
import os
import numpy as np
from flask import Flask, render_template, request
from flask_cors import CORS

class MySQLDatabaseHandler(object):
    
    def __init__(self,MYSQL_USER,MYSQL_USER_PASSWORD,MYSQL_PORT,MYSQL_DATABASE,MYSQL_HOST = "localhost"):
        self.IS_DOCKER = True if 'DB_NAME' in os.environ else False
        self.MYSQL_HOST = os.environ['DB_NAME'] if self.IS_DOCKER else MYSQL_HOST
        self.MYSQL_USER = "admin" if self.IS_DOCKER else MYSQL_USER
        self.MYSQL_USER_PASSWORD = "admin" if self.IS_DOCKER else MYSQL_USER_PASSWORD
        self.MYSQL_PORT = 3306 if self.IS_DOCKER else MYSQL_PORT
        self.MYSQL_DATABASE = MYSQL_DATABASE
        self.engine = self.validate_connection()

    def validate_connection(self):

        engine = db.create_engine(f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_USER_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}")
        conn = engine.connect()
        conn.execute(f"CREATE DATABASE IF NOT EXISTS {self.MYSQL_DATABASE}")
        conn.execute(f"USE {self.MYSQL_DATABASE}")
        return engine

    def lease_connection(self):
        return self.engine.connect()
    
    def query_executor(self,query):
        conn = self.lease_connection()
        if type(query) == list:
            for i in query:
                conn.execute(i)
        else:
            conn.execute(query)
        

    def query_selector(self,query):
        conn = self.lease_connection()
        data = conn.execute(query)
        return data

    def load_file_into_db(self,file_path  = None):
        if self.IS_DOCKER:
            return
        if file_path is None:
            file_path = os.path.join(os.environ['ROOT_PATH'],'init.sql')
        sql_file = open(file_path,"r")
        sql_file_data = list(filter(lambda x:x != '',sql_file.read().split(";\n")))
        self.query_executor(sql_file_data)
        sql_file.close()

os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

MYSQL_USER = "root"
MYSQL_USER_PASSWORD = ""
MYSQL_PORT = 3306
MYSQL_DATABASE = "productsdb"

mysql_engine = MySQLDatabaseHandler(MYSQL_USER, MYSQL_USER_PASSWORD,
                                      MYSQL_PORT, MYSQL_DATABASE)

mysql_engine.load_file_into_db()
products = list(mysql_engine.query_selector(f"SELECT * FROM productinfo"))
app = Flask(__name__)
CORS(app)

def product_filter(product_type):
    keys = ["id","product_url","product_type","product_price"]

    product_type = f"SELECT * FROM productinfo WHERE LOWER( product_type ) LIKE '%%{product_type.lower()}%%'"
    query1 = mysql_engine.query_selector(product_type)

    return json.dumps([dict(zip(keys,i)) for i in query1])

def price_filter(product_price):
    price = float(product_price)
    keys = ["id","product_url","product_type","product_price"]

    product_price = f"SELECT * FROM productinfo WHERE CAST(product_price as decimal(5,2)) BETWEEN '%%{price*0.5}%%' AND '%%{price*1.5}%%'"
    query2 = mysql_engine.query_selector(product_price)

    return json.dumps([dict(zip(keys,i)) for i in query2])

product = products[2]
# print(product)
# print(product_filter(product[2]))
print(product[1])
# print(price_filter(product[4]))

@app.route("/")
def home():
    return render_template('base.html', title="sample html")


@app.route("/products")
def products_search():
    # product_name = request.args.get("product_name")
    # product_url = request.args.get("product_url")
    product_type = request.args.get("product_type")
    product_price = request.args.get("product_price")
    # clean_ingreds = request.args.get("clean_ingreds")
    # price = request.args.get("price")
    return boolean_search1(product_type, product_price)

app.run(debug=True)
