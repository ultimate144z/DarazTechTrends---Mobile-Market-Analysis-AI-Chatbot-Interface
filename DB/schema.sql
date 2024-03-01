-- Create a new database
CREATE DATABASE daraznewnew;

-- Use the newly created database
USE daraznewnew;

-- Create a table for products
CREATE TABLE products (
    product_id VARCHAR(12) PRIMARY KEY,
    name VARCHAR(2048) NOT NULL,
    price DECIMAL NOT NULL,
    score DECIMAL NOT NULL,
    image_url VARCHAR(2048) NOT NULL,
    product_url VARCHAR(2048) NOT NULL
);

-- Create a table for reviews
CREATE TABLE reviews (
    review_id VARCHAR(36) PRIMARY KEY,
    reviewer_name VARCHAR(255) NOT NULL,
    time VARCHAR(50) NOT NULL,
    text TEXT NOT NULL,
	product_id VARCHAR(12),
   
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Create a table for reviews
CREATE TABLE stats (
    product_id VARCHAR(36) PRIMARY KEY,
    seller_name VARCHAR(255) NOT NULL,
    total_reviews INT NOT NULL,
	total_questions INT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

select *from products;
select *from reviews;
select *from stats;