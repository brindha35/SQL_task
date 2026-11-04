SELECT 'Hello Retail Project' AS message;


CREATE TABLE customers (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    city VARCHAR(100)
);


CREATE TABLE orders (
    id INT PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    amount NUMERIC(10,2),
    ordered_at DATE
);

CREATE TABLE products (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    attrs JSONB
);


INSERT INTO customers (id, name, city)
VALUES
(1, 'Arun', 'Chennai'),
(2, 'Priya', 'Mumbai'),
(3, 'Rahul', 'Chennai'),
(4, 'Divya', 'Bangalore');

SELECT * FROM customers;

INSERT INTO orders (id, customer_id, amount, ordered_at)
VALUES
(101, 1, 700, '2026-01-05'),
(102, 1, 600, '2026-02-10'),
(103, 2, 300, '2026-01-20'),

 
(104, 3, 1200, '2026-02-15'),
(105, 3, 800, '2026-03-01'),
(106, 2, 900, '2026-03-10'),
(107, 1, 500, '2026-03-15'),
(108, 4, 1500, '2026-03-20'),
(109, 2, 400, '2026-03-25');

SELECT * FROM orders;


INSERT INTO products (id, name, attrs)
VALUES
(1, 'Laptop A', '{"brand":"Dell","ram":16}'),
(2, 'Laptop B', '{"brand":"HP","ram":8}');

SELECT * FROM products;


SELECT
    customers.id,
    customers.name,
    SUM(order.amount) AS total_sales
FROM customers 
JOIN orders 
    ON customers.id = o.customer_id
GROUP BY
    customers.id,
    customers.name
HAVING SUM(orders.amount) > 1000
ORDER BY total_sales DESC;



SELECT
    customers.id,
    customers.name,
    customers.city
FROM customers 
LEFT JOIN orders 
    ON customers.id = orders.customer_id
WHERE orders.id IS NULL;



WITH customer_sales AS (
    SELECT
        customers.id,
        customers.name,
        customers.city,
        SUM(orders.amount) AS total_sales
    FROM customers
    JOIN orders
        ON customers.id = orders.customer_id
    GROUP BY
        customers.id,
        customers.name,
        customers.city
),
ranked_customers AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY city
            ORDER BY total_sales DESC
        ) AS row_num
    FROM customer_sales
)
SELECT
    id,
    name,
    city,
    total_sales
FROM ranked_customers
WHERE row_num = 1;



SELECT
    orders.id AS order_id,
    orders.customer_id,
    orders.amount,
    orders.ordered_at,

    ROW_NUMBER() OVER (
        PARTITION BY orders.customer_id
        ORDER BY orders.ordered_at DESC
    ) AS row_number

FROM orders;



SELECT
    id,
    name,
    attrs
FROM products
WHERE attrs @> '{"brand": "Dell"}';



SELECT
    id,
    name,
    attrs ->> 'ram' AS ram
FROM products;