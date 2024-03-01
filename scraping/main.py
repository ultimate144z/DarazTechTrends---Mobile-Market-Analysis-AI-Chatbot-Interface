from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
import re
import time
import uuid

service = Service(executable_path="chromedriver.exe")
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)
driver.implicitly_wait(10)

# Define a keyword dictionary of filter words
filter_keywords = ["charger", "case", "cover", "earphones", "accessory", "screen protector"]

def scrape_products(products_csv_filename, url, add_header):
    driver.get(url)
    # Open CSV file to store product details
    with open(products_csv_filename, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if add_header:
            writer.writerow(['product_id', 'name', 'price', 'score', 'image_url', 'product_url'])
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        product_elements = soup.find_all('div', class_='gridItem--Yd0sa')

        for product_element in product_elements:
            try:
                product_id = product_element['data-item-id']
                product_name = product_element.find('div', {'class': 'title--wFj93'}).get_text(strip=True).replace('"','')
                
                # Check if any filter keyword is in the product name, skip if found
                if any(keyword in product_name.lower() for keyword in filter_keywords):
                    continue
                
                product_price_raw = product_element.find('div', {'class': 'price--NVB62'}).get_text(strip=True)
                product_price = int(product_price_raw.replace('Rs.', '').replace(',', '').strip())
                element = WebDriverWait(driver, 20).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "#id-img"))
                    )
                product_image_url = element.get_attribute("src")
                product_link = "https:" + product_element.find('a', {'id': 'id-a-link'})['href']
                rating_elements = product_element.find_all('i', class_=re.compile('star-icon--k88DV star-'))
                if rating_elements:
                    total_rating = sum(int(re.search(r'star-(\d+)--', rating['class'][1]).group(1)) for rating in rating_elements)
                    average_rating = total_rating / len(rating_elements)
                else:
                    average_rating = "0.0"
            
                writer.writerow([product_id, product_name, product_price, average_rating, product_image_url, product_link])

            except Exception as e:
                #print(f"Error: {e}")
                continue

def add_review_id_to_products(csv_filename):
    # Open the CSV file in append mode to add new reviews
    with open('reviews.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['review_id', 'review_name', 'time', 'text', 'product_id'])  # Write headers

    # Open the stats CSV file for writing
    with open('stats.csv', 'w', newline='', encoding='utf-8') as stats_file:
        stats_writer = csv.writer(stats_file)
        stats_writer.writerow(['product_id', 'seller_name', 'total_reviews', 'total_questions'])

    # Read the existing CSV file
    with open(csv_filename, 'r', newline='', encoding='utf-8') as read_file:
        reader = csv.reader(read_file)
        headers = next(reader)
        for row in reader:
            # Assuming the URL is the last element in the row
            product_url = row[-1]
           
            driver.get(product_url)
            time.sleep(5)  # Wait for the page to load

            # Use BeautifulSoup to parse the page
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            review_elements = soup.find_all('div', class_='review-item')
            total_reviews_element = soup.select_one('#module_product_review_star_1 > div > a:nth-child(2)')
            total_reviews = 0
            if total_reviews_element:
                total_reviews_text = total_reviews_element.get_text(strip=True)
                match = re.search(r'\d+', total_reviews_text)
                if match:
                    total_reviews = match.group()
                    print(total_reviews)

            # Find total_questions element
            total_questions_ele = soup.select_one('#module_product_review_star_1 > div > a:nth-child(4)')
            total_questions_element = 0
            if total_questions_ele:
                total_questions_text = total_questions_ele.get_text(strip=True)
                match = re.search(r'\d+', total_questions_text)
                if match:
                    total_questions_element = match.group()
                    print(total_questions_element)

            seller_name_element = soup.find('a', class_='pdp-link pdp-link_size_l pdp-link_theme_black seller-name__detail-name')
            if seller_name_element:
                seller_name = seller_name_element.text
            else:
                seller_name = 'N/A'
                
            # Write to the stats CSV file
            with open('stats.csv', 'a', newline='', encoding='utf-8') as stats_file:
                stats_writer = csv.writer(stats_file)
                stats_writer.writerow([row[0], seller_name, total_reviews, total_questions_element])

            with open('reviews.csv', 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                for review_element in review_elements:
                    try:
                        review_id = str(uuid.uuid4())
                        reviewer_name = review_element.find('div', {'class': 'user'}).get_text(strip=True)
                        review_time = review_element.find('div', {'class': 'time'}).get_text(strip=True)
                        review_text = review_element.find('div', {'class': 'review-content-sl'}).get_text(strip=True).replace('\n', '').replace(',', '')
                        product_id = row[0]
                        new_row = [review_id, reviewer_name, review_time, review_text, product_id]
                        
                        writer.writerow(new_row)  # Append the new review to the CSV
                    except Exception as e:
                        print(f"Error: {e}")
                        continue

import pandas as pd

def filter_from_csv(file_path, output_file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)

    # Remove duplicates based on 'product_id'
    df.drop_duplicates(subset='product_id', keep='first', inplace=True)

    # Save the updated DataFrame to a new CSV file
    df.to_csv(output_file_path, index=False)

csv_file = 'products.csv'
base_url = "https://www.daraz.pk/smartphones/?page="
for page_number in range(1, 6):
    url = f"{base_url}{page_number}&sort=order"
    if page_number == 1:
        add_header = True
    else:
        add_header = False

    scrape_products(csv_file, url, add_header)
    time.sleep(3)

output_products = 'products_filtered.csv'
filter_from_csv(csv_file, output_products)

print("Products Scraped!, Now Gathering Reviews for Each Product")
add_review_id_to_products(output_products)

