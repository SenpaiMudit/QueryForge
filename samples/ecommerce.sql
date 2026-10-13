-- Sample E-Commerce Database for QueryForge
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    country TEXT,
    city TEXT,
    loyalty_level TEXT
);

INSERT INTO customers (name, email, country, city, loyalty_level) VALUES
('John Doe', 'john@example.com', 'USA', 'New York', 'Gold'),
('Sara Connor', 'sara@example.com', 'USA', 'Los Angeles', 'Platinum'),
('Alex Chen', 'alex@example.com', 'Canada', 'Toronto', 'Silver'),
('Maria Garcia', 'maria@example.com', 'Spain', 'Madrid', 'Gold'),
('Liam Wilson', 'liam@example.com', 'UK', 'London', 'Bronze'),
('Yuki Tanaka', 'yuki@example.com', 'Japan', 'Tokyo', 'Platinum'),
('Emma Watson', 'emma@example.com', 'UK', 'Manchester', 'Silver'),
('Carlos Rossi', 'carlos@example.com', 'Italy', 'Milan', 'Gold');

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    category TEXT,
    price REAL,
    stock INTEGER
);

INSERT INTO products (product_name, category, price, stock) VALUES
('Mechanical Keyboard', 'Electronics', 129.99, 45),
('Wireless Mouse', 'Electronics', 49.99, 120),
('USB-C Monitor 27"', 'Electronics', 349.50, 30),
('Ergonomic Chair', 'Furniture', 289.00, 15),
('Standing Desk', 'Furniture', 499.00, 8),
('Noise Cancelling Headphones', 'Audio', 199.99, 60),
('Studio Microphone', 'Audio', 149.00, 25),
('Webcam 4K', 'Electronics', 89.99, 50);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    order_date TEXT,
    total_amount REAL,
    status TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

INSERT INTO orders (customer_id, order_date, total_amount, status) VALUES
(1, '2024-01-15', 179.98, 'Delivered'),
(2, '2024-01-18', 499.00, 'Delivered'),
(3, '2024-01-22', 129.99, 'Delivered'),
(4, '2024-02-01', 349.50, 'Delivered'),
(1, '2024-02-10', 199.99, 'Delivered'),
(5, '2024-02-14', 49.99, 'Shipped'),
(6, '2024-02-20', 648.99, 'Delivered'),
(7, '2024-03-01', 149.00, 'Processing'),
(8, '2024-03-05', 289.00, 'Shipped'),
(2, '2024-03-12', 399.50, 'Delivered');

CREATE TABLE IF NOT EXISTS order_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    unit_price REAL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 129.99),
(1, 2, 1, 49.99),
(2, 5, 1, 499.00),
(3, 1, 1, 129.99),
(4, 3, 1, 349.50),
(5, 6, 1, 199.99),
(6, 3, 1, 349.50),
(6, 4, 1, 289.00),
(7, 7, 1, 149.00),
(8, 4, 1, 289.00),
(9, 6, 2, 199.99);
