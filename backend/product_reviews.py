import product_reviews from 'reviews.json'
import pandas as pd

reviews = {}
counts = {}
for review in product_reviews:
  if review["product_id"] not in reviews:
    reviews[review["product_id"]] = review['review']
    counts[review["product_id"]] = 1
  elif review["product_id"] in reviews and counts[review["product_id"]] < 5:
    reviews[review["product_id"]] += review['review']
    counts[review["product_id"]] += 1
  else:
    pass 

df = pd.DataFrame(reviews)
print(reviews)