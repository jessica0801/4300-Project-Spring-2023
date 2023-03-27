import json
import os
import numpy as np
import ast
from flask import Flask, render_template, request
from flask_cors import CORS
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler

# ROOT_PATH for linking with all your files.
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

# These are the DB credentials for your OWN MySQL
# Don't worry about the deployment credentials, those are fixed
# You can use a different DB name if you want to
MYSQL_USER = "root"
MYSQL_USER_PASSWORD = ""
MYSQL_PORT = 3306
MYSQL_DATABASE = "productsdb"

mysql_engine = MySQLDatabaseHandler(MYSQL_USER, MYSQL_USER_PASSWORD,
                                    MYSQL_PORT, MYSQL_DATABASE)

# Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
mysql_engine.load_file_into_db()

app = Flask(__name__)
CORS(app)


# Sample search, the LIKE operator in this case is hard-coded,
# but if you decide to use SQLAlchemy ORM framework,
# there's a much better and cleaner way to do this
def sql_search(product):
    query_sql = f"""SELECT * FROM products WHERE LOWER( product_name ) LIKE '%%{product.lower()}%%' limit 10"""
    keys = [
        "product_name", "product_url", "product_type", "clean_ingreds", "price"
    ]
    data = mysql_engine.query_selector(query_sql)
    return json.dumps([dict(zip(keys, i)) for i in data])


def getSkinType(skin_type):
    # 14 product types: moisturizer, serum, oil, mist, balm, mask, peel, eye care,
    # cleanser, toner, exfoliater, bath salts, body wash, bath oil
    product_types = []

    if skin_type == 'normal' or skin_type == 'combination':
        product_types = [
            'moisturizer', 'serum', 'oil', 'mist', 'balm', 'mask', 'peel',
            'cleanser', 'toner', 'exfoliater'
        ]
    elif skin_type == 'dry':
        product_types = ['moisturizer', 'serum', 'oil', 'mist', 'balm', 'mask']
    elif skin_type == 'oily':
        product_types = ['mist', 'peel', 'cleanser', 'toner', 'exfoliater']
    elif skin_type == 'sensitive':
        product_types = [
            'moisturizer', 'serum', 'mist', 'cleanser', 'toner', 'mask'
        ]
    else:
        product_types = ['eye care', 'bath salts', 'body wash', 'bath oil']

    return product_types


def boolean_search2(survey, product):
    # draft for p4
    skin, allergens = survey
    product_types = getSkinType(skin)
    # clean_ingreds = ast.literal_eval(product.clean_ingreds)
    price = float(product.price[1:])

    product_type = f"""SELECT * FROM products WHERE LOWER( product_type ) IN '%%{skin_types}%%'"""
    # allergies = f"""SELECT * FROM products WHERE LOWER( clean_ingreds ) IN '%%{allergens}%%'"""
    price = f"""SELECT * FROM products WHERE price BETWEEN '%%{price*0.9}%%' AND '%%{price*1.1}%%'"""

    keys = [
        "product_name", "product_url", "product_type", "clean_ingreds", "price"
    ]
    query_sql = np.intersect1d(product_type, price)
    # query_sql2 = np.setdiff1d(query_sql1, allergies)
    data = mysql_engine.query_selector(query_sql)

    return json.dumps([dict(zip(keys, i)) for i in data])


def boolean_search1(product):
    # draft for p3
    # product includes product_name,product_url,product_type,clean_ingreds,price
    product_name = product.product_name
    price = float(product.price[1:])

    product_type = f"""SELECT * FROM products WHERE LOWER( product_type ) LIKE '%%{product_name.lower()}%%'"""
    price = f"""SELECT * FROM products WHERE price BETWEEN '%%{price*0.9}%%' AND '%%{price*1.1}%%'"""
    keys = [
        "product_name", "product_url", "product_type", "clean_ingreds", "price"
    ]

    query_sql = np.intersect1d(product_type, price)
    data = mysql_engine.query_selector(query_sql)

    return json.dumps([dict(zip(keys, i)) for i in data])


@app.route("/")
def home():
    return render_template('base.html', title="sample html")


@app.route("/products")
def products_search():
    text = request.args.get("product_name")
    return boolean_search1(text)


# app.run(debug=True)
