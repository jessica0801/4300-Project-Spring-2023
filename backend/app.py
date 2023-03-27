import json
import os
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
MYSQL_DATABASE = "productsdb"

mysql_engine = MySQLDatabaseHandler(MYSQL_USER, MYSQL_USER_PASSWORD,
                                    MYSQL_PORT, MYSQL_DATABASE)

# Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
mysql_engine.load_file_into_db()

# mysql_engine.load_file_into_db('skincare_products_clean.csv')

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


@app.route("/")
def home():
    return render_template('base.html', title="sample html")


@app.route("/products")
def episodes_search():
    text = request.args.get("product_name")
    return sql_search(text)

def tokenize(text):
    """text is a string. tokenize(text) cleans the text and removes stopwords 
    and punctuations.
    returns: list of words"""
    text = ''.join([word for word in text if word not in string.punctuation])
    text = text.lower()
    stopwords = ["ourselves", "hers", "between", "yourself", "but", "again", "there", 
                 "about", "once", "during", "out", "very", "having", "with", "they", 
                 "own", "an", "be", "some", "for", "do", "its", "yours", "such", 
                 "into", "of", "most", "itself", "other", "off", "is", "s", "am", 
                 "or", "who", "as", "from", "him", "each", "the", "themselves", 
                 "until", "below", "are", "we", "these", "your", "his", "through",
                "don", "nor", "me", "were", "her", "more", "himself", "this", "down",
                "should", "our", "their", "while", "above", "both", "up", "to", "ours", 
                "had", "she", "all", "no", "when", "at", "any", "before", "them", "same",
                "and", "been", "have", "in", "will", "on", "does", "yourselves", "then", 
                "that", "because", "what", "over", "why", "so", "can", "did", "not", "now",
                "under", "he", "you", "herself", "has", "just", "where", "too", "only", 
                "myself", "which", "those", "i", "after", "few", "whom", "t", "being", "if", 
                "theirs", "my", "against", "a", "by", "doing", "it", "how", "further", "was", 
                "here", "than"]
    text = ' '.join([word for word in text.split() if word not in stopwords])
    return re.findall("[A-Za-z]+" ,text)


def build_inv_ind(tokenized_dict):
    ans = {}
    for id in range(len(tokenized_dict)):
        doc = tokenized_dict.keys()[id]
        tmp = {}
        for word in tokenized_dict[doc]:
            if word not in tmp:
                tmp[word]=0
            tmp[word]+=1
        for word in tmp:
            if word not in ans:
                ans[word] = []
            ans[word] += [(id, tmp[word])]
    return ans

def compute_idf(inv_ind, num_products, min_df, max_df_ratio):
    ans = {}
    for word in inv_ind.keys():
        contains = len(inv_ind[word])
        if min_df <= contains and float(contains)/num_products <= max_df_ratio:
            ans[word]= round(math.log2(num_products / float(1+contains)),2)
    return ans

def compute_norms(index, idf, num_products):
    ans = [0 for _ in num_products]
    for word in index.keys():
        if word in idf:
            for pair in index[word]:
                ans[pair[0]] += (pair[1] * idf[word])**2
    
    for i in range(num_products):
        ans[i] = math.sqrt(ans[i])
    return ans

#query_word_counts: example_query_words = {"like": 2, "mother": 1, "daughter": 1}
def acc_dot_scores(query_word_counts, index, idf):
    ans={}
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
            score = round(float(dots[doc])/ (qnorm * doc_norms[doc]), 2)
        ans += [(score, doc)]
    ans.sort(key = lambda x: x[0], reverse = True)
    return ans
        

# name_tokens= {name:tokenize(name) for name in names}
def cosine_sim(product):
    ans = []
    product_name = product.product_name
    products= f"""SELECT * FROM products WHERE LOWER( product_name )"""
    products_name = [prod.product_name for prod in products]
    inv_idx = build_inv_ind(products_name)
    idf = compute_idf(inv_idx, len(products_name), 10, 0.1)
    inv_idx = {key: val for key, val in inv_idx.items()
           if key in idf} 
    norms = compute_norms(inv_idx, idf, len(products_name))
    for _, id in index_search(product_name, inv_idx, idf, norms)[:10]:
        ans+=[products_name[id]]
    return ans

app.run(debug=True)