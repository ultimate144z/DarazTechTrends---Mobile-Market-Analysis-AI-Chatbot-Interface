import mysql.connector
import csv

# MySQL database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'new_password',
    'database': 'daraz'  # Make sure the database 'daraz' already exists
}

# Connect to the database
try:
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Path to your CSV file
    csv_file_path = '../scraping/products_filtered.csv'

    # Open the CSV file
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)

        # Skip the header row (if any)
        next(reader)

        # Insert data into the database
        for row in reader:
            sql = """
                INSERT INTO products (product_id, name, price, score, image_url, product_url)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, row)

        # Commit the changes
        connection.commit()

except mysql.connector.Error as error:
    print(f"Error: {error}")
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("Products Inserted!")


# Connect to the database
try:
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Path to your CSV file
    csv_file_path = '../scraping/reviews.csv'

    # Open the CSV file
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)

        # Skip the header row (if any)
        next(reader)

        # Insert data into the database
        for row in reader:
            sql = """
                INSERT INTO reviews (review_id, reviewer_name, time, text, product_id)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, row)

        # Commit the changes
        connection.commit()
except mysql.connector.Error as error:
    print(f"Error: {error}")
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("Reviews Inserted!")
# Connect to the database
try:
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Path to your CSV file
    csv_file_path = '../scraping/stats.csv'

    # Open the CSV file
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)

        # Skip the header row (if any)
        next(reader)

        # Insert data into the database
        for row in reader:
            sql = """
                INSERT INTO stats (product_id, seller_name, total_reviews, total_questions)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, row)

        # Commit the changes
        connection.commit()

except mysql.connector.Error as error:
    print(f"Error: {error}")
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("Stats Inserted!")