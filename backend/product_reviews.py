import csv
import 'reviews'

field_names = ['product_id', 'review']

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

with open('product_reviews.csv', 'w',newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames = field_names)
    writer.writeheader()
    writer.writerows(reviews)