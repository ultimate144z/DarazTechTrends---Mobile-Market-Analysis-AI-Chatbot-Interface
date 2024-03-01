import csv
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from nltk.stem import PorterStemmer
import re
import mysql.connector

nltk.download('stopwords')

# MySQL database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'daraz'  # Make sure the database 'daraz' already exists
}

data = []
# Connect to the database
try:
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Define a function to retrieve product data from the database
    def fetch_product_data():
        sql = "SELECT * FROM products"
        cursor.execute(sql)
        columns = [column[0] for column in cursor.description]
        product_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return product_data

    # Retrieve product data from the database
    data = fetch_product_data()

except mysql.connector.Error as error:
    print(f"Error: {error}")
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")

# Preprocess the data
stop_words = set(stopwords.words('english'))
tokenizer = RegexpTokenizer(r'\w+')
ps = PorterStemmer()

# Tokenize, remove stopwords, and stem the text data
for item in data:
    text = item['name'] + ' ' + item['product_url']
    words = tokenizer.tokenize(text.lower())
    filtered_words = [ps.stem(word) for word in words if word not in stop_words]
    item['processed_text'] = ' '.join(filtered_words)

def extract_price_constraint(query):
    # Split the query into words
    words = query.split()

    # Look for keywords indicating a price constraint
    keywords = ['under', 'in', 'for']
    max_price = None

    # Regular expression to match price values with 'RS' or 'rs' or 'R.S' or 'r.s' and optional currency symbol
    price_pattern = r'(\d+(?:\.\d+)?)\s*(?:RS|R\.S|r\.s|rs)?'

    for i, word in enumerate(words):
        # Check for keywords indicating a price constraint
        if word in keywords:
            # Look for the maximum price immediately following the keyword
            if i + 1 < len(words):
                try:
                    price_match = re.match(price_pattern, words[i + 1], re.IGNORECASE)
                    if price_match:
                        max_price = float(price_match.group(1))
                    break  # Stop searching when a valid price is found
                except ValueError:
                    continue

    return max_price


def extract_top_n(query):
    words = query.split()
    n_keywords = ['top', 'best', 'max', 'minimum']
    n_value = None
    for i, word in enumerate(words):
        # Check for keywords indicating an "n" value constraint
        if word in n_keywords:
            # Look for the "n" value immediately following the keyword
            if i + 1 < len(words):
                try:
                    n_value_word = words[i + 1].lower()
                    if n_value_word.isnumeric():
                        n_value = int(n_value_word)
                    else:
                        # Set n_value to 1 for queries like "best phone" without specifying n
                        n_value = 1
                    break  # Stop searching when a valid "n" value is found
                except ValueError:
                    continue
    return n_value

def get_best_products(data, max_price, top_n, brand=None):
    # First filter based on brand
    if brand is not None:
        filtered_products = [item for item in data if brand.lower() in item['name'].lower()]
    else:
        filtered_products = data  # If no brand is specified, consider all products

    # Further filter based on max_price and exclude products with a score of 0
    filtered_products = [item for item in filtered_products if (max_price is None or int(item['price']) <= max_price) and float(item['score']) != 0]

    # Sort the filtered products by score in descending order
    sorted_by_score = sorted(filtered_products, key=lambda x: -float(x['score']))

    # Select the top_n best-scored products
    best_scored_products = sorted_by_score[:top_n] if top_n is not None else sorted_by_score

    # Sort the best-scored products by price in ascending order
    final_results = sorted(best_scored_products, key=lambda x: int(x['price']))

    # Return the final list of products
    return [(item['product_id'], int(item['price']), float(item['score'])) for item in final_results]


def get_worst_products(data, max_price, top_n, brand=None):
    # First filter based on brand
    if brand is not None:
        filtered_products = [item for item in data if brand.lower() in item['name'].lower()]
    else:
        filtered_products = data  # If no brand is specified, consider all products

    # Further filter based on max_price and exclude products with a score of 0
    filtered_products = [item for item in filtered_products if (max_price is None or int(item['price']) <= max_price) and float(item['score']) != 0]

    # Sort the filtered products by score in ascending order
    sorted_by_score = sorted(filtered_products, key=lambda x: float(x['score']))

    # Select the top_n worst-scored products
    worst_scored_products = sorted_by_score[:top_n] if top_n is not None else sorted_by_score

    # Sort the worst-scored products by price in descending order
    final_results = sorted(worst_scored_products, key=lambda x: -int(x['price']))

    # Return the final list of products
    return [(item['product_id'], int(item['price']), float(item['score'])) for item in final_results]


def extract_brand(query, tokenizer):
    brand_keywords = ['brand', 'of', 'by', 'built by', 'made by']
    tokens = tokenizer.tokenize(query)

    for i, word in enumerate(tokens):
        if word.lower() in brand_keywords and i + 1 < len(tokens):
            # Assume the next token is the brand name
            return tokens[i + 1]
    return None


def answer_user_query(query, data):
    query = query.lower()
    tokens = tokenizer.tokenize(query)
    query_words = [ps.stem(word) for word in tokens if word not in stop_words]
    
    max_price = extract_price_constraint(query)
    top_n = extract_top_n(query)
    brand = extract_brand(query, tokenizer)
    print("brand:", str(brand))
    is_best_query = "best" in query  # Check if "best" is in the query
    is_worst_query = "worst" in query  # Check if "worst" is in the query
    print("worst query:", str(is_worst_query))
    print("price:", str(max_price))
    print("top_n:", str(top_n))

    if is_best_query:
        results = get_best_products(data, max_price, top_n, brand)
    elif is_worst_query:
        results = get_worst_products(data, max_price, top_n, brand)
    else:
        # Continue with the original logic for other queries
        results = []

        for item in data:
            product_id = item['product_id']
            product_text = item['processed_text']
            price = int(item['price'])
            score = sum(1 for word in query_words if word in product_text)

            if (max_price is None or price <= max_price) and (top_n is None or len(results) < top_n):
                results.append((product_id, price, score))

        # Sort the results by price in ascending order and score in descending order
        results.sort(key=lambda x: (x[1], -x[2]))

    return results
 

user_query = "What are top 5 best phones under 30000"
user_query = user_query.replace('?', '')  # Remove the question mark
results = answer_user_query(user_query, data)

if results:
    print(f"Based on user query, the top {len(results)} products are:")
    for i, (product_id, price, score) in enumerate(results):
        product = [item for item in data if item['product_id'] == product_id][0]
        print(f"{i+1}. Product ID: {product['product_id']}")
        print(f"   Product Name: {product['name']}")
        print(f"   Product Price: {product['price']}")
        print(f"   Product Score: {product['score']}")
        print(f"   Product Image URL: {product['image_url']}")
        print(f"   Product URL: {product['product_url']}")
        print()
else:
    print("No relevant products found for the query.")
