import json
import os
import numpy as np
import ast
from flask import Flask, render_template, request
from flask_cors import CORS
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler
import math
import re
import string

# ROOT_PATH for linking with all your files.
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

# These are the DB credentials for your OWN MySQL
# Don't worry about the deployment credentials, those are fixed
# You can use a different DB name if you want to
MYSQL_USER = "root"
MYSQL_USER_PASSWORD = ""
MYSQL_PORT = 3306
MYSQL_DATABASE = "cosmetics_db"

mysql_engine = MySQLDatabaseHandler(MYSQL_USER, MYSQL_USER_PASSWORD,
                                    MYSQL_PORT, MYSQL_DATABASE)

# Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
mysql_engine.load_file_into_db()
products = list(mysql_engine.query_selector(f"SELECT * FROM korean_skincare"))
# print(products)
app = Flask(__name__)
CORS(app)


# Sample search, the LIKE operator in this case is hard-coded,
# but if you decide to use SQLAlchemy ORM framework,
# there's a much better and cleaner way to do this
def sql_search(product):
    query_sql = f"""SELECT * FROM products WHERE LOWER( product_name ) LIKE '%%{product.lower()}%%' limit 10"""
    keys = [
        "product_name", "product_brand", "price", "product_description",
        "product_type"
    ]
    data = mysql_engine.query_selector(query_sql)
    return json.dumps([dict(zip(keys, i)) for i in data])


# def product_filter(product_type):
#     keys = ["product_name","product_brand","price","product_description","product_type"]

#     product_type = f"SELECT * FROM korean_skincare WHERE LOWER( product_type ) LIKE '%%{product_type.lower()}%%'"
#     query1 = mysql_engine.query_selector(product_type)

#     return json.dumps([dict(zip(keys, i)) for i in query1])

# def price_filter(min_price, max_price):
#     keys = ["product_name","product_brand","price","product_description","product_type"]

#     product_price = f"SELECT * FROM korean_skincare WHERE price BETWEEN '%%{min_price}%%' AND '%%{max_price}%%'"
#     query2 = mysql_engine.query_selector(product_price)

#     return json.dumps([dict(zip(keys, i)) for i in query2])


def boolean_search(product_types, min_price, max_price):
    keys = [
        "product_name", "product_brand", "price", "product_review",
        "product_type"
    ]

    survey = f"SELECT * FROM korean_skincare WHERE LOWER( product_type ) IN ({str(product_types)}) AND price BETWEEN {min_price} AND {max_price}"
    # print(survey)
    query = mysql_engine.query_selector(survey)

    return [dict(zip(keys, i)) for i in query]


def tokenize(text):
    """text is a string. tokenize(text) cleans the text and removes stopwords 
    and punctuations.
    returns: list of words"""
    text = ''.join([word for word in text if word not in string.punctuation])
    text = text.lower()
    stopwords = [
        "ourselves", "hers", "between", "yourself", "but", "again", "there",
        "about", "once", "during", "out", "very", "having", "with", "they",
        "own", "an", "be", "some", "for", "do", "its", "yours", "such", "into",
        "of", "most", "itself", "other", "off", "is", "s", "am", "or", "who",
        "as", "from", "him", "each", "the", "themselves", "until", "below",
        "are", "we", "these", "your", "his", "through", "don", "nor", "me",
        "were", "her", "more", "himself", "this", "down", "should", "our",
        "their", "while", "above", "both", "up", "to", "ours", "had", "she",
        "all", "no", "when", "at", "any", "before", "them", "same", "and",
        "been", "have", "in", "will", "on", "does", "yourselves", "then",
        "that", "because", "what", "over", "why", "so", "can", "did", "not",
        "now", "under", "he", "you", "herself", "has", "just", "where", "too",
        "only", "myself", "which", "those", "i", "after", "few", "whom", "t",
        "being", "if", "theirs", "my", "against", "a", "by", "doing", "it",
        "how", "further", "was", "here", "than"
    ]
    text = ' '.join([word for word in text.split() if word not in stopwords])
    return re.findall("[A-Za-z]+", text)


def build_inv_ind(tokenized_dict):
    ans = {}
    for id in range(len(tokenized_dict)):
        doc = list(tokenized_dict.keys())[id]
        tmp = {}
        for word in tokenized_dict[doc]:
            if word not in tmp:
                tmp[word] = 0
            tmp[word] += 1
        for word in tmp:
            if word not in ans:
                ans[word] = []
            ans[word] += [(id, tmp[word])]
    return ans


def compute_idf(inv_ind, num_products, min_df, max_df_ratio):
    ans = {}
    for word in inv_ind.keys():
        contains = len(inv_ind[word])
        if min_df <= contains and float(
                contains) / num_products <= max_df_ratio:
            ans[word] = round(math.log2(num_products / float(1 + contains)), 2)
    return ans


def compute_norms(index, idf, num_products):
    ans = [0 for _ in range(num_products)]
    for word in index.keys():
        if word in idf:
            for pair in index[word]:
                ans[pair[0]] += (pair[1] * idf[word])**2

    for i in range(num_products):
        ans[i] = math.sqrt(ans[i])
    return ans


def acc_dot_scores(query_word_counts, index, idf):
    ans = {}
    for word in query_word_counts.keys():
        tf = query_word_counts[word]
        if word in idf:
            for pair in index[word]:
                if pair[0] not in ans:
                    ans[pair[0]] = 0
                ans[pair[0]] += tf * pair[1] * (idf[word]**2)
    return ans


def index_search(query, index, idf, doc_norms, score_func=acc_dot_scores):
    ans = []
    q = tokenize(query)
    tmp = {}
    qnorm = 0
    for word in q:
        tmp[word] = q.count(word)
        if word in idf:
            qnorm += (tmp[word] * idf[word])**2
        qnorm = math.sqrt(qnorm)
    dots = score_func(tmp, index, idf)
    for doc in range(len(doc_norms)):
        score = -1
        if doc in dots:
            score = round(float(dots[doc]) / (qnorm * doc_norms[doc]), 2)
        ans += [(score, doc)]
    ans.sort(key=lambda x: x[0], reverse=True)
    return ans


keys = [
    "product_name", "product_brand", "price", "product_review", "product_type"
]

products = f"""SELECT * FROM korean_skincare"""
products = [dict(zip(keys, i)) for i in mysql_engine.query_selector(products)]

product_names = [dic["product_name"] for dic in products]
product_revs = [dic["product_review"] for dic in products]
# create tokenized dict from product revs to input to buikd_inv_ind
tok_dict = {}
for i in range(len(products)):
    tok_dict[product_names[i]] = tokenize(product_revs[i])
inv_idx = build_inv_ind(tok_dict)
idf = compute_idf(inv_idx, len(products), 10, 0.1)
inv_idx = {key: val for key, val in inv_idx.items() if key in idf}
norms = compute_norms(inv_idx, idf, len(products))


def cosine_sim(query):
    ans = []
    # keys = [
    #     "product_name", "product_brand", "price", "product_description", "product_type"
    # ]
    # for _, id in index_search(query, inv_idx, idf, norms)[:10]:
    #     ans += [products[id]]
    # return json.dumps([dict(zip(keys, i)) for i in ans])
    for _, id in index_search(query, inv_idx, idf, norms)[:10]:
        ans += [products[id]]
    return ans


@app.route("/")
def home():
    return render_template('base.html', title="sample html")


@app.route('/product-type')
def product_type_search():
    product_type = request.args.get("product_type")
    min_price = request.args.get("product_min_price")
    max_price = request.args.get("product_max_price")
    boolean = boolean_search(product_type, min_price, max_price)

    keywords = request.args.get("keywords")
    cosine_sim = cosine_sim(keywords)

    bool_products = {dic["product_name"]: dic for dic in boolean}
    # print(bool_products)
    cosine_products = {dic["product_name"]: dic for dic in cosine_sim}
    # print(cosine_products)
    common_names = set(bool_products.keys()).intersection(
        set(cosine_products.keys()))
    result = [bool_products[name] for name in common_names]

    return result


# boolean = boolean_search(['serum', 'sun protection', 'toner'], 0, 100)

# cosine_sim = cosine_sim("I want to protect my skin spf")

# bool_products = {dic["product_name"]: dic for dic in boolean}
# # print(bool_products)
# cosine_products = {dic["product_name"]: dic for dic in cosine_sim}
# # print(cosine_products)
# common_names = set(bool_products.keys()).intersection(
#     set(cosine_products.keys()))
# result = [bool_products[name] for name in common_names]
# print(result)

app.run(debug=True)