from flask import Flask, request, jsonify
app = Flask(__name__)
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from nltk.stem import PorterStemmer
import re
import mysql.connector
from flask_cors import CORS
CORS(app)

nltk.download('stopwords')

# MySQL database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'new_password',
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

def extract_mini_price_constraint(query):
    # Split the query into words
    words = query.split()

    # Look for keywords indicating a price constraint
    keywords = ['over', 'above', 'more than']
    min_price = None

    # Regular expression to match price values with 'RS' or 'rs' or 'R.S' or 'r.s' and optional currency symbol
    price_pattern = r'(\d+(?:\.\d+)?)\s*(?:RS|R\.S|r\.s|rs)?'

    for i, word in enumerate(words):
        # Check for keywords indicating a minimum price constraint
        if word in keywords:
            # Look for the minimum price immediately following the keyword
            if i + 1 < len(words):
                try:
                    price_match = re.match(price_pattern, words[i + 1], re.IGNORECASE)
                    if price_match:
                        min_price = float(price_match.group(1))
                    break  # Stop searching when a valid minimum price is found
                except ValueError:
                    continue

    return min_price

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
    n_keywords = ['give', 'top', 'best', 'max', 'minimum', 'worst']
    n_value = None

    # Iterate through the words in the query
    for i, word in enumerate(words):
        # Check for keywords indicating an "n" value constraint
        if word in n_keywords:
            # Look for the "n" value immediately following the keyword
            if i + 1 < len(words):
                n_value_word = words[i + 1].lower()
                try:
                    # Try to parse the next word as an integer
                    n_value = int(n_value_word)
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


def fetch_stats_info(product_id):
    try:
        # Establish a connection to the MySQL database
        conn = mysql.connector.connect(**db_config)

        # Create a cursor object to execute SQL queries
        cursor = conn.cursor()

        # Execute a SQL query to fetch the required information for the given product_id
        query = """
            SELECT seller_name, total_reviews, total_questions
            FROM stats
            WHERE product_id = %s
        """
        cursor.execute(query, (product_id,))

        # Fetch the result
        result = cursor.fetchone()

        if result:
            seller_name, total_reviews, total_questions = result
            return {
                'seller_name': seller_name,
                'total_reviews': total_reviews,
                'total_questions': total_questions
            }
        else:
            # Handle the case where no stats information is found for the product_id
            return {
                'seller_name': 'N/A',
                'total_reviews': 0,
                'total_questions': 0
            }

    except mysql.connector.Error as err:
        # Handle any database-related errors
        print(f"MySQL Error: {err}")

def extract_max_price_query(query):
    keywords = ['max', 'maximum', 'high', 'highest']
    for keyword in keywords:
        if keyword in query:
            return True
    return False   

def extract_min_price_query(query):
    keywords = ['min', 'minimum', 'low', 'lowest']
    for keyword in keywords:
        if keyword in query:
            return True
    return False   


def get_max_price_products(data, max_price, top_n, brand=None):
    max_price_products = []

    if brand is not None:
        filtered_products = [item for item in data if brand.lower() in item['name'].lower()]
    else:
        filtered_products = data  # If no brand is specified, consider all products

    # Further filter based on max_price and exclude products with a score of 0
    filtered_products = [item for item in filtered_products if (max_price is None or int(item['price']) <= max_price) and float(item['score']) != 0]

    for item in filtered_products:
        price = int(item['price'])
        # Filter phones based on your maximum price criteria
        if max_price is None or price <= max_price:
            max_price_products.append(item)

    # Sort the filtered products by price in descending order
    max_price_products.sort(key=lambda x: -int(x['price']))

    # Select the top_n maximum price products
    max_price_products = max_price_products[:top_n] if top_n is not None else max_price_products

    # Return the final list of products
    return [(item['product_id'], int(item['price']), float(item['score'])) for item in max_price_products]


def get_min_price_products(data, min_price, top_n, brand=None):
    min_price_products = []

    if brand is not None:
        filtered_products = [item for item in data if brand.lower() in item['name'].lower()]
    else:
        filtered_products = data  # If no brand is specified, consider all products

    # Further filter based on min_price and exclude products with a score of 0
    filtered_products = [item for item in filtered_products if (min_price is None or int(item['price']) >= min_price) and float(item['score']) != 0]

    for item in filtered_products:
        price = int(item['price'])
        # Filter phones based on your minimum price criteria
        if min_price is None or price >= min_price:
            min_price_products.append(item)

    # Sort the filtered products by price in ascending order
    min_price_products.sort(key=lambda x: int(x['price']))

    # Select the top_n minimum price products
    min_price_products = min_price_products[:top_n] if top_n is not None else min_price_products

    # Return the final list of products
    return [(item['product_id'], int(item['price']), float(item['score'])) for item in min_price_products]

def filter_products_by_review_keyword(search_ids_data, data_n):
    filtered_products = []

    # Create a set of product IDs for faster lookups
    data_product_ids = {int(item['product_id']) for item in data_n}
    #print(data_product_ids)
    
    for product_id in search_ids_data:
        # Convert product_id to integer if it's not already
        product_id = int(product_id)
        #print(product_id)
        if product_id in data_product_ids:
            #print("True")
            filtered_products.extend([item for item in data if int(item['product_id']) == product_id])
   # print(filtered_products)
    return [(item['product_id'], int(item['price']), float(item['score'])) for item in filtered_products]


def extract_review_keyword(query):
    # Check if the query contains "review" or "reviews" as a hinting word
    if re.search(r'\breview(s)?\b', query, flags=re.IGNORECASE):
        # Extract words in quotes following "review" or "reviews"
        matches = re.findall(r'(?:review|reviews)\s*["\'](.*?)["\']', query, flags=re.IGNORECASE)
        if matches:
            return matches
        else:
            return None
    else:
        return None

def search_review_keyword(keyword_list):
    try:
        # Connect to the MySQL database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        keyword = ' '.join(keyword_list)

        # Execute the SQL query to search for reviews containing the keyword
        
        query = f"SELECT * FROM reviews WHERE text LIKE '%{keyword}%'"
        cursor.execute(query)

        # Fetch and return the results
        results = cursor.fetchall()
       
        product_ids = [result[-1] for result in results]
        return product_ids

    except mysql.connector.Error as e:
        print("MySQL error:", e)
        return []

    finally:
        # Close the database connection
        if connection:
            connection.close()

def extract_range_price_constraint(query):
    keywords = ['in-between', 'in between', 'between']
    
    for keyword in keywords:
        if keyword in query:
            # Use regular expressions to extract the price range values
            pattern = r'(\d+)\s*(?:to|and)\s*(\d+)'
            match = re.search(pattern, query, re.IGNORECASE)
            
            if match:
                # Extract and return the minimum and maximum prices as integers
                min_price = int(match.group(1))
                max_price = int(match.group(2))
                return min_price, max_price

    return None, None 

def get_products_in_price_range(data, min_price, max_price, top_n=None, brand=None):
    # First filter based on brand
    if brand is not None:
        filtered_products = [item for item in data if brand.lower() in item['name'].lower()]
    else:
        filtered_products = data  # If no brand is specified, consider all products

    # Further filter based on price range and exclude products with a score of 0
    filtered_products = [item for item in filtered_products if (min_price is None or int(item['price']) >= min_price) and
                        (max_price is None or int(item['price']) <= max_price) and
                        float(item['score']) != 0]

    # Sort the filtered products by price in ascending order
    sorted_by_price = sorted(filtered_products, key=lambda x: int(x['price']))

    # Select the top_n products in the price range
    results = sorted_by_price[:top_n] if top_n is not None else sorted_by_price
    
    # Return the final list of products
    return [(item['product_id'], int(item['price']), float(item['score'])) for item in results]

def get_above_products(data, min_price, top_n=None, brand=None):
    # First filter based on brand
    if brand is not None:
        filtered_products = [item for item in data if brand.lower() in item['name'].lower()]
    else:
        filtered_products = data  # If no brand is specified, consider all products

    # Further filter based on min_price and exclude products with a score of 0
    filtered_products = [item for item in filtered_products if (min_price is None or int(item['price']) >= min_price) and float(item['score']) != 0]

    # Sort the filtered products by price in ascending order
    sorted_by_price = sorted(filtered_products, key=lambda x: int(x['price']))

    # Select the top_n products with prices above the threshold
    above_price_products = sorted_by_price if top_n is None else sorted_by_price[:top_n]

    return [(item['product_id'], int(item['price']), float(item['score'])) for item in above_price_products]

def answer_user_query(query, data):
    query = query.lower()
    tokens = tokenizer.tokenize(query)
    query_words = [ps.stem(word) for word in tokens if word not in stop_words]

    has_above_price = extract_mini_price_constraint(query)
    has_max_price_query = extract_max_price_query(query)
    has_min_price_query = extract_min_price_query(query)
    max_price = extract_price_constraint(query)
    top_n = extract_top_n(query)
    brand = extract_brand(query, tokenizer)
    minr_price, maxr_price = extract_range_price_constraint(query)
    print("range price:" + str(minr_price) + "-" + str(maxr_price))
    print("brand:", str(brand))
    is_best_query = "best" in query or "top" in query  # Check if "best" is in the query
    is_worst_query = "worst" in query  # Check if "worst" is in the query
    print("worst query:", str(is_worst_query))
    print("price:", str(max_price))
    print("top_n:", str(top_n))

    review_keyword = extract_review_keyword(query)
    if minr_price is not None and maxr_price is not None:
        results = get_products_in_price_range(data, minr_price, maxr_price, top_n, brand)
    elif has_above_price:
        results = get_above_products(data, has_above_price, top_n, brand)
    elif is_best_query:
        results = get_best_products(data, max_price, top_n, brand)
    elif is_worst_query:
        results = get_worst_products(data, max_price, top_n, brand)
    elif review_keyword:
       # print("lsssssssss")
        review_products_ids = search_review_keyword(review_keyword)
        results = filter_products_by_review_keyword(review_products_ids, data)
    elif has_max_price_query:
        results = get_max_price_products(data, max_price, top_n, brand)
    elif has_min_price_query:
        results = get_min_price_products(data, max_price, top_n, brand)
        
    else:
        # Search for a product by name
        product_name_query = ' '.join(query_words)
        print(query_words)
        results = []

        for item in data:
            product_name = item['name'].lower()
           
            if product_name_query in product_name:
                results.append((item['product_id'], int(item['price']), 0))  # Score set to 0 for name-based search

        # Sort the results by price in ascending order
        results.sort(key=lambda x: (x[1], -x[2]))

        if review_keyword:
            review_products_ids = search_review_keyword(review_keyword)
            results = filter_products_by_review_keyword(review_products_ids, results)
        #print(results)
    
    return [item[0] for item in results]
  # Extract product_id from the results
@app.route('/query_products', methods=['POST'])
def query_products():
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': '*',
    }
    try:
        user_query = request.json['query']
        user_query = user_query.replace('?', '')  # Remove the question mark

        # Call the answer_user_query function to get results
        results = answer_user_query(user_query, data)

        if results:
            stats = get_stats(results)
            response = {
                'message': f"Based on user query, the top {len(results)} products are:",
                'products': [],
                'stats': stats  # Initialize 'stats' as a dictionary
            }

            for (index, product_id) in enumerate(results):
                product = [item for item in data if item['product_id'] == product_id][0]
                product_info = {
                    'product_id': product['product_id'],
                    'product_name': product['name'],
                    'product_price': product['price'],
                    'product_score': product['score'],
                    'product_img': product['image_url'],
                    'product_url': product['product_url']
                }
                product_stats = fetch_stats_info(product_id)
                product_info.update(product_stats)
                
                response['products'].append(product_info)

            return jsonify(response), 200, headers
        else:
            return jsonify({'message': 'No relevant products found for the query.'}), 404, headers

    except Exception as e:
        return jsonify({'error': str(e)}), 500, headers

def get_stats(stats_data_n):
    stats_data = fetch_combined_data(stats_data_n)

    total_listings = len(stats_data)
    if total_listings == 0:
        return {'message': 'No listings available.'}, 404

    total_price = sum(float(item['price']) for item in stats_data)
    average_price = total_price / total_listings

    total_ratings = sum(float(item['score']) for item in stats_data)
    average_ratings = total_ratings / total_listings

    total_reviews = sum(int(item['total_reviews']) for item in stats_data)
    average_review_count = total_reviews / total_listings

    stats = {
        'average_price': format(average_price, '.2f'),
        'average_ratings': format(average_ratings, '.2f'),
        'average_review_count': format(average_review_count, '.2f'),
        'total_listings': total_listings
    }
    
    return stats


def fetch_combined_data(stats_ids):
    combined_data = []
    
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # SQL query to join data from "products" and "stats" tables for specific product IDs
        sql = """
            SELECT 
                p.product_id, p.name, p.price, p.score, p.image_url, p.product_url, 
                s.seller_name, s.total_reviews, s.total_questions
            FROM products p
            JOIN stats s ON p.product_id = s.product_id
            WHERE p.product_id IN (%s)
        """
        # Create a string with placeholders for the product IDs
        placeholders = ', '.join(['%s' for _ in stats_ids])
        formatted_sql = sql % placeholders

        cursor.execute(formatted_sql, tuple(stats_ids))
        columns = [column[0] for column in cursor.description]
        
        for row in cursor.fetchall():
            combined_data.append(dict(zip(columns, row)))

    except mysql.connector.Error as error:
        print(f"Error: {error}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")
    
    return combined_data

# Call the fetch_combined_data function to get the combined data


if __name__ == '__main__':
    app.run(debug=True)