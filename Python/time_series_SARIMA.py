import pandas as pd
import numpy as np
import sqlite3
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error
import json
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, DayLocator
from datetime import datetime

def forecast_earthquakes_sarima(magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date, sqlite_file, table_name):
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
    
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    filtered_data = data[
        (data['Mag'] >= magnitude_min) & (data['Mag'] <= magnitude_max) &
        (data['Depth'] >= depth_min) & (data['Depth'] <= depth_max) &
        (data['Date'] >= start_date) & (data['Date'] <= end_date)
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

    # Split data for training and testing
    test_data = df.iloc[-15:]
    train_data = df.iloc[:-15]

    # SARIMA model training
    order = (1, 1, 2)
    seasonal_order = (1, 0, 1, 7)
    model = SARIMAX(train_data, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
    sarima_model = model.fit()

    # Forecasting
    forecast = sarima_model.get_forecast(steps=len(test_data))
    forecast_mean = forecast.predicted_mean

    # Prepare JSON output
    json_output = []
    for date, actual, predicted in zip(test_data.index, test_data['Frequency'], forecast_mean):
        json_output.append({
            'day': date.strftime('%Y-%m-%d'),
            'actual_value': actual,
            'predicted_value': predicted
        })

    # Save JSON output to a file
    with open('forecast_results.json', 'w') as json_file:
        json.dump(json_output, json_file, indent=4)

    # Plotting
    plt.figure(figsize=(10, 5))  # Adjust the figure size as needed
    plt.plot(test_data.index, test_data['Frequency'], label='Actual Frequency', linestyle='-', marker='o')  # Actual values
    plt.plot(test_data.index, forecast_mean, label='SARIMA Forecast', color='orange', linestyle='--', marker='s')  # Predicted values
    plt.legend()
    plt.title('Actual Frequencies vs. SARIMA Predictions')
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
    month_year = df_resampled.index[-1].strftime('%B %Y')  # Get month and year of the last day
    plt.text(0.01, -0.15, month_year, transform=ax.transAxes, fontsize=10, ha='left', color='gray')  # Place text at bottom left

    plt.tight_layout()  # Adjust layout to prevent clipping of labels
    plt.show()

    # Evaluation
    mae = mean_absolute_error(test_data['Frequency'], forecast_mean)
    mape = mean_absolute_percentage_error(test_data['Frequency'], forecast_mean)
    rmse = np.sqrt(mean_squared_error(test_data['Frequency'], forecast_mean))

    print(f'MAE: {mae}')
    print(f'MAPE: {mape}')
    print(f'RMSE: {rmse}')

    return json_output

# Example usage
result = forecast_earthquakes_sarima(3.0, 7.0, 0, 70, '2020-01-01', '2024-01-01', 'Python/static/final_earthquake_catalogue_v2.db', 'earthquake_database')
print(result)
