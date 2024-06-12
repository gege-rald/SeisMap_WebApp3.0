import pandas as pd
import sqlite3
from statsmodels.tsa.arima.model import ARIMA
import numpy as np
import json
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, DayLocator
from datetime import datetime

def forecast_earthquakes_ARIMA(magnitude_min, magnitude_max, depth_min, depth_max, forecast_date, sqlite_file, table_name):
    # Connect to SQLite database
    print("Connection established")
    conn = sqlite3.connect(sqlite_file)
    query = f"SELECT * FROM {table_name}"
    data = pd.read_sql(query, conn)
    conn.close()
    
    data['Mag'] = pd.to_numeric(data['Mag'], errors='coerce')
    data['Depth'] = pd.to_numeric(data['Depth'], errors='coerce')
    data['Date_Time'] = pd.to_datetime(data['Date_Time'], errors='coerce')
    
    data['Date'] = data['Date_Time'].dt.date
    data = data.dropna(subset=['Mag', 'Depth', 'Date'])
    
    forecast_date = datetime.strptime(forecast_date, '%Y-%m-%d').date()
    
    filtered_data = data[
        (data['Mag'] >= magnitude_min) & (data['Mag'] <= magnitude_max) &
        (data['Depth'] >= depth_min) & (data['Depth'] <= depth_max) &
        (data['Date'] >= forecast_date)
    ]

    filtered_data = filtered_data.sort_values(by='Date_Time')

    # Resample by day and count the number of earthquakes
    filtered_data.set_index('Date_Time', inplace=True)
    df_resampled = filtered_data.resample('D').size()
    df_resampled.name = 'Frequency'
    df = df_resampled.to_frame()

    # Ensure DataFrame has a datetime index
    if not df.index.is_monotonic_increasing:
        df.sort_index(inplace=True)

    # Train ARIMA model using all data
    model = ARIMA(df, order=(1, 1, 2))
    model_fit = model.fit()

    # Forecast
    forecast_days = 15  # Forecast for the next 15 days
    forecast_dates = pd.date_range(start=forecast_date, periods=forecast_days)
    forecast_test = model_fit.forecast(steps=forecast_days)

    # Prepare JSON output
    json_output = []
    for date, value, actual_value in zip(forecast_dates, forecast_test, df['Frequency'].tail(forecast_days)):
        json_output.append({
            'date': date.strftime('%Y-%m-%d'),
            'actual_value': actual_value,
            'predicted_value': value
        })

    # Save JSON output to a file
    with open('forecast_results.json', 'w') as json_file:
        json.dump(json_output, json_file, indent=4)

    # Plotting
    plt.figure(figsize=(10, 5))  # Adjust the figure size as needed
    plt.plot(forecast_dates, df['Frequency'].tail(forecast_days), label='Actual Frequency', linestyle='-', marker='o')  # Actual values
    plt.plot(forecast_dates, forecast_test, label='ARIMA Forecast', color='orange', linestyle='--', marker='s')  # Predicted values
    plt.legend()
    plt.title('Actual Frequencies vs. ARIMA Predictions')
    plt.xlabel('Date')
    plt.ylabel('Frequency')
    plt.grid(True)

    # Customize x-axis ticks
    ax = plt.gca()
    ax.xaxis.set_major_locator(DayLocator(interval=1))
    ax.xaxis.set_major_formatter(DateFormatter('%d'))
    ax.xaxis.set_minor_locator(DayLocator())
    ax.xaxis.set_minor_formatter(DateFormatter('%d'))
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability

    # Set month and year text at the bottom left corner
    month_year = forecast_dates[0].strftime('%B %Y')  # Get month and year of the forecast start date
    plt.text(0.01, -0.15, month_year, transform=ax.transAxes, fontsize=10, ha='left', color='gray')  # Place text at bottom left

    plt.tight_layout()  # Adjust layout to prevent clipping of labels
    plot_file_path = 'Python/static/forecast_plot.png'
    plt.savefig(plot_file_path)
    plt.close()

    return json_output, plot_file_path


# # Example usage
# result = forecast_earthquakes_ARIMA(3.0, 7.0, 0, 70, '2023-11-01', 'Python/static/final_earthquake_catalogue_v2.db', 'earthquake_database')
# print(result)
