Run Data Quality Checks

-- Check 1: Null revenue
INSERT INTO Data_Quality_Log
    (check_name, result, status, notes)
SELECT 'Null Revenue Check',
       COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Revenue must never be NULL'
FROM Fact_Sales WHERE revenue IS NULL;

-- Check 2: Duplicate sale IDs
INSERT INTO Data_Quality_Log
    (check_name, result, status, notes)
SELECT 'Duplicate Sale ID Check',
       COUNT(*) - COUNT(DISTINCT sale_id),
       CASE WHEN COUNT(*) = COUNT(DISTINCT sale_id)
            THEN 'PASS' ELSE 'FAIL' END,
       'Every sale_id must be unique'
FROM Fact_Sales;

-- Check 3: Negative revenue
INSERT INTO Data_Quality_Log
    (check_name, result, status, notes)
SELECT 'Negative Revenue Check',
       COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Revenue must be 0 or above'
FROM Fact_Sales WHERE revenue < 0;

-- Check 4: Future dates
INSERT INTO Data_Quality_Log
    (check_name, result, status, notes)
SELECT 'Future Date Check',
       COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       'No sales should have future dates'
FROM Dim_Date WHERE full_date > CURRENT_DATE;

-- Check 5: Orphaned products
INSERT INTO Data_Quality_Log
    (check_name, result, status, notes)
SELECT 'Orphaned Product Check',
       COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Every sale must link to a valid product'
FROM Fact_Sales f
LEFT JOIN Dim_Product p ON f.product_id = p.product_id
WHERE p.product_id IS NULL;

-- Check 6: Cost vs revenue
INSERT INTO Data_Quality_Log
    (check_name, result, status, notes)
SELECT 'Cost vs Revenue Check',
       COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'WARNING' END,
       'Cost should not exceed revenue'
FROM Fact_Sales WHERE cost > revenue;

-- Check 7: Discount range
INSERT INTO Data_Quality_Log
    (check_name, result, status, notes)
SELECT 'Discount Range Check',
       COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Discount must be between 0 and 1'
FROM Fact_Sales WHERE discount < 0 OR discount > 1;

-- Check 8: Null customers
INSERT INTO Data_Quality_Log
    (check_name, result, status, notes)
SELECT 'Null Customer Check',
       COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Every sale must have a customer'
FROM Fact_Sales WHERE customer_id IS NULL;

-- Check 9: Product category completeness
INSERT INTO Data_Quality_Log
    (check_name, result, status, notes)
SELECT 'Category Completeness Check',
       COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Every product must have category and subcategory'
FROM Dim_Product
WHERE category IS NULL OR subcategory IS NULL;

-- Check 10: Zero quantity
INSERT INTO Data_Quality_Log
    (check_name, result, status, notes)
SELECT 'Zero Quantity Check',
       COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Quantity must be at least 1'
FROM Fact_Sales WHERE quantity <= 0;

View all results
SELECT check_name, result, status, run_date
FROM Data_Quality_Log
ORDER BY log_id;
