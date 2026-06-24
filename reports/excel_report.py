import openpyxl
from openpyxl.styles import Font, PatternFill
import psycopg2
import pandas as pd

# Pull weekly KPI summary
conn = psycopg2.connect(
    host="localhost",
    database="Salepulse",
    user="postgres",
    password="Murugansaibaba",
    port="5432"
)
df = pd.read_sql("""
    SELECT 
        d.month_name,
        SUM(f.revenue) as revenue,
        SUM(f.profit) as profit,
        ROUND(AVG(f.discount)*100,2) as avg_discount,
        SUM(f.returns) as total_returns
    FROM Fact_Sales f
    JOIN Dim_Date d ON f.date_id = d.date_id
    GROUP BY d.month_name, d.month
    ORDER BY d.month
""", conn)

# Create formatted Excel
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Weekly KPI Report"

# Header styling
header_fill = PatternFill("solid", fgColor="1F4E79")
header_font = Font(color="FFFFFF", bold=True)

headers = ['Month','Revenue','Profit',
           'Avg Discount %','Returns']
for col, header in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=header)
    cell.fill = header_fill
    cell.font = header_font

# Write data
for row_idx, row in df.iterrows():
    for col_idx, value in enumerate(row, 1):
        ws.cell(row=row_idx+2, 
                column=col_idx, value=value)

wb.save('SalesPulse_Weekly_Report.xlsx')
print("Excel report generated")