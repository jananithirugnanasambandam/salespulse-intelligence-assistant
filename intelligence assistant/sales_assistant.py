import psycopg2
import sys
import json

question = sys.argv[1] if len(sys.argv) > 1 else ""

try:

    conn = psycopg2.connect(
        host="localhost",
        database="Salepulse",
        user="postgres",
        password="Murugansaibaba"
    )

    cur = conn.cursor()

    # ------------------------------------
    # 1. Why did sales drop in March?
    # ------------------------------------
    if question == "Why did sales drop in March?":

        cur.execute("""
            SELECT
                d.year,
                SUM(f.revenue) revenue
            FROM Fact_Sales f
            JOIN Dim_Date d
                ON f.date_id = d.date_id
            WHERE d.month_name = 'March'
            GROUP BY d.year
            ORDER BY d.year DESC
            LIMIT 2
        """)

        rows = cur.fetchall()

        if len(rows) >= 2:
            current = rows[0][1]
            previous = rows[1][1]

            change = ((current - previous) / previous) * 100

            answer = (
                f"March revenue changed by {change:.1f}% "
                f"compared to the previous year. "
                f"Further investigation into category and store performance is recommended."
            )
        else:
            answer = "Not enough March history available."

    # ------------------------------------
    # 2. Declining category
    # ------------------------------------
    elif question == "Which product category is declining?":

        cur.execute("""
            SELECT
                p.category,
                SUM(f.revenue) revenue
            FROM Fact_Sales f
            JOIN Dim_Product p
                ON f.product_id = p.product_id
            GROUP BY p.category
            ORDER BY revenue ASC
            LIMIT 1
        """)

        category, revenue = cur.fetchone()

        answer = (
            f"{category} is currently the lowest performing category "
            f"with revenue of AED {revenue:,.0f}. "
            f"Consider reviewing pricing, promotions, and inventory."
        )

    # ------------------------------------
    # 3. Total revenue
    # ------------------------------------
    elif question == "What is total revenue this year?":

        cur.execute("""
            SELECT SUM(f.revenue)
            FROM Fact_Sales f
            JOIN Dim_Date d
                ON f.date_id = d.date_id
            WHERE d.year = (
                SELECT MAX(year)
                FROM Dim_Date
            )
        """)

        revenue = cur.fetchone()[0]

        answer = (
            f"Total revenue for the latest year is "
            f"AED {revenue:,.0f}."
        )

    # ------------------------------------
    # 4. Highest revenue city
    # ------------------------------------
    elif question == "Which city has highest revenue?":

        cur.execute("""
            SELECT
                s.city,
                SUM(f.revenue) revenue
            FROM Fact_Sales f
            JOIN Dim_Store s
                ON f.store_id = s.store_id
            GROUP BY s.city
            ORDER BY revenue DESC
            LIMIT 1
        """)

        city, revenue = cur.fetchone()

        answer = (
            f"{city} generated the highest revenue "
            f"at AED {revenue:,.0f}."
        )

    # ------------------------------------
    # 5. Churn risk customers
    # ------------------------------------
    elif question == "Which customers are at churn risk?":

        cur.execute("""
            SELECT COUNT(*)
            FROM Fact_Customer_Activity
            WHERE is_churned = TRUE
        """)

        count = cur.fetchone()[0]

        answer = (
            f"There are {count:,} customers "
            f"currently classified as churn risk."
        )

    # ------------------------------------
    # 6. Focus next month
    # ------------------------------------
    elif question == "What should I focus on next month?":

        cur.execute("""
            SELECT
                p.category,
                SUM(f.profit) profit
            FROM Fact_Sales f
            JOIN Dim_Product p
                ON f.product_id = p.product_id
            GROUP BY p.category
            ORDER BY profit DESC
            LIMIT 1
        """)

        category, profit = cur.fetchone()

        answer = (
            f"Focus on {category}. "
            f"It generated AED {profit:,.0f} profit "
            f"and is the strongest growth opportunity."
        )

    # ------------------------------------
    # 7. Store below target
    # ------------------------------------
    elif question == "Which store is below target?":

        cur.execute("""
            SELECT
                s.store_name,
                SUM(f.revenue) revenue
            FROM Fact_Sales f
            JOIN Dim_Store s
                ON f.store_id = s.store_id
            GROUP BY s.store_name
            ORDER BY revenue ASC
            LIMIT 1
        """)

        store, revenue = cur.fetchone()

        answer = (
            f"{store} has the lowest revenue "
            f"at AED {revenue:,.0f}."
        )

    # ------------------------------------
    # 8. Return rate
    # ------------------------------------
    elif question == "What is the return rate by category?":

        cur.execute("""
            SELECT
                p.category,
                ROUND(
                    SUM(f.returns)::numeric /
                    NULLIF(SUM(f.quantity),0) * 100,
                    2
                ) return_rate
            FROM Fact_Sales f
            JOIN Dim_Product p
                ON f.product_id = p.product_id
            GROUP BY p.category
            ORDER BY return_rate DESC
            LIMIT 1
        """)

        category, rate = cur.fetchone()

        answer = (
            f"{category} has the highest return rate "
            f"at {rate}%."
        )

    else:
        answer = "Please select a valid question."

    print(json.dumps({
        "answer": answer
    }))

    conn.close()

except Exception as e:
    print(json.dumps({
        "answer": str(e)
    }))