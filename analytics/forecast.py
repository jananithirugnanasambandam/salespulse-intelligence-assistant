from prophet import Prophet
import pandas as pd
import psycopg2

conn = psycopg2.connect(
    host="localhost", database="Salepulse",
    user="postgres", password="Murugansaibaba"
)

df = pd.read_sql("""
    SELECT d.full_date AS ds,
           SUM(f.revenue) AS y
    FROM Fact_Sales f
    JOIN Dim_Date d ON f.date_id = d.date_id
    GROUP BY d.full_date
    ORDER BY d.full_date
""", conn)

ramadan = pd.DataFrame({
    'holiday':      'ramadan',
    'ds': pd.to_datetime([
        '2022-04-02','2023-03-23','2024-03-11'
    ]),
    'lower_window': 0,
    'upper_window': 30
})

model = Prophet(holidays=ramadan, yearly_seasonality=True)
model.fit(df)
future   = model.make_future_dataframe(periods=90)
forecast = model.predict(future)

forecast[['ds','yhat','yhat_lower','yhat_upper']]\
    .to_csv(r'C:\SalesPulseForecast\forecast.csv', index=False)
print("Forecast saved")