-- Test 1: Revenue by month
SELECT d.year, d.month_name,
       ROUND(SUM(f.revenue),2) AS total_revenue
FROM Fact_Sales f
JOIN Dim_Date d ON f.date_id = d.date_id
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month
LIMIT 12;

-- Test 2: Top 5 products
SELECT p.product_name,
       ROUND(SUM(f.revenue),2) AS revenue
FROM Fact_Sales f
JOIN Dim_Product p ON f.product_id = p.product_id
GROUP BY p.product_name
ORDER BY revenue DESC
LIMIT 5;

-- Test 3: Revenue by UAE city
SELECT s.city,
       ROUND(SUM(f.revenue),2) AS revenue
FROM Fact_Sales f
JOIN Dim_Store s ON f.store_id = s.store_id
GROUP BY s.city
ORDER BY revenue DESC;
