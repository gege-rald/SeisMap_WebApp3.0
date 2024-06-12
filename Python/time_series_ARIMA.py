import os
import pandas as pd
import sqlite3
from statsmodels.tsa.arima.model import ARIMA
import numpy as np
import json
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, DayLocator
from datetime import datetime
from threading import Lock

# Set Matplotlib to use the 'Agg' backend
import matplotlib
matplotlib.use('Agg')

# Lock for serializing access to the plotting code
plot_lock = Lock()

def forecast_earthquakes_ARIMA(magnitude_min, magnitude_max, depth_min, depth_max, forecast_date, sqlite_file, table_name):
    # Connect to SQLite database
    conn = sqlite3.connect(sqlite_file)
    query = f"SELECT * FROM {table_name}"
    data = pd.read_sql(query, conn)
    conn.close()
    
    # Clean and preprocess data
    data['Mag'] = pd.to_numeric(data['Mag'], errors='coerce')
    data['Depth'] = pd.to_numeric(data['Depth'], errors='coerce')
    data['Date_Time'] = pd.to_datetime(data['Date_Time'], errors='coerce')
    data['Date'] = data['Date_Time'].dt.date
    data = data.dropna(subset=['Mag', 'Depth', 'Date'])
    
    # Filter data based on input parameters
    forecast_date = datetime.strptime(forecast_date, '%Y-%m-%d').date()
    filtered_data = data[
        (data['Mag'] >= magnitude_min) & (data['Mag'] <= magnitude_max) &
        (data['Depth'] >= depth_min) & (data['Depth'] <= depth_max)
    ]
    
    # Ensure filtered_data has datetime index
    filtered_data.set_index('Date_Time', inplace=True)
    
    # Resample by day and count the number of earthquakes
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

    # Round the predicted values
    forecast_test_rounded = forecast_test.round()

    # Prepare JSON output
    json_output = []
    for date, value in zip(forecast_dates, forecast_test_rounded):
        # Fetch actual value from df_resampled for the corresponding date
        actual_value = int(df_resampled.loc[date]) if date in df_resampled.index else None
        json_output.append({
            'date': date.strftime('%Y-%m-%d'),
            'actual_value': actual_value,
            'predicted_value': int(value)  # Ensure the value is an integer
        })

    # Save JSON output to a file
    json_output_file = 'Python/static/forecast_results.json'
    with open(json_output_file, 'w') as json_file:
        json.dump(json_output, json_file, indent=4)

    # Plotting
    with plot_lock:
        plt.clf()  # Clear the current figure
        plt.figure(figsize=(8, 6))  # Adjust the figure size as needed
        actual_values = [int(df_resampled.loc[date]) if date in df_resampled.index else np.nan for date in forecast_dates]
        plt.plot(forecast_dates, actual_values, label='Actual Frequency', linestyle='-', marker='o')  # Actual values
        plt.plot(forecast_dates, forecast_test_rounded, label='ARIMA Forecast', color='orange', linestyle='--', marker='s')  # Predicted values
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
        plot_file_path = 'forecast_plot.png'
        plt.savefig(os.path.join('Python/static', plot_file_path))
        plt.close()

    return json_output, plot_file_path
