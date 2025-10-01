-- MySQL DML Operations Test Fixture
-- Tests: INSERT, UPDATE, DELETE, SELECT with JOINs

-- Insert single row
INSERT INTO `products` (`name`, `description`, `price`, `stock`, `category`)
VALUES ('Laptop', 'High-performance laptop', 999.99, 10, 'Electronics');

-- Insert multiple rows
INSERT INTO `products` (`name`, `price`, `stock`, `category`) VALUES
    ('Mouse', 29.99, 50, 'Accessories'),
    ('Keyboard', 79.99, 30, 'Accessories'),
    ('Monitor', 299.99, 15, 'Electronics');

-- Update statement
UPDATE `products`
SET `stock` = `stock` - 1
WHERE `id` = 1 AND `stock` > 0;

-- Update with JOIN (MySQL-specific syntax)
UPDATE `products` p
INNER JOIN (
    SELECT `product_id`, SUM(`quantity`) as total_sold
    FROM `orders`
    GROUP BY `product_id`
) o ON p.`id` = o.`product_id`
SET p.`stock` = p.`stock` - o.total_sold;

-- Delete statement
DELETE FROM `products`
WHERE `stock` = 0 AND `category` = 'Discontinued';

-- SELECT with JOINs
SELECT
    u.`username`,
    p.`name` as product_name,
    o.`quantity`,
    o.`total_price`,
    o.`order_date`
FROM `orders` o
INNER JOIN `users` u ON o.`user_id` = u.`id`
INNER JOIN `products` p ON o.`product_id` = p.`id`
WHERE o.`order_date` >= DATE_SUB(NOW(), INTERVAL 30 DAY)
ORDER BY o.`order_date` DESC;

-- Subquery with IN
SELECT `name`, `price`
FROM `products`
WHERE `id` IN (
    SELECT DISTINCT `product_id`
    FROM `orders`
    WHERE `order_date` >= DATE_SUB(NOW(), INTERVAL 7 DAY)
);
