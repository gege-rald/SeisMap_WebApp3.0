lstm


import pandas as pd
import numpy as np
import sqlite3
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.callbacks import Callback
from sklearn.metrics import mean_absolute_error, mean_squared_error
import json
from datetime import datetime
import sys

# Set the default encoding to utf-8 for print statements
sys.stdout.reconfigure(encoding='utf-8')

def forecast_earthquakes_LSTM(magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date, sqlite_file, table_name):
    def safe_print(*args, **kwargs):
        try:
            print(*args, **kwargs)
        except UnicodeEncodeError:
            print("Encoding error occurred during print operation.")

    # Connect to SQLite database
    safe_print("Connection established")
    conn = sqlite3.connect(sqlite_file)
    query = f"SELECT * FROM {table_name}"
    data = pd.read_sql(query, conn)
    conn.close()

    # Convert columns to appropriate data types
    data['Mag'] = pd.to_numeric(data['Mag'], errors='coerce')
    data['Depth'] = pd.to_numeric(data['Depth'], errors='coerce')
    data['Date_Time'] = pd.to_datetime(data['Date_Time'], errors='coerce')

    # Create 'Date' column and drop rows with missing values
    data['Date'] = data['Date_Time'].dt.date
    data = data.dropna(subset=['Mag', 'Depth', 'Date'])

    # Convert start_date and end_date to datetime objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Filter data based on specified criteria
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

    # Convert series to supervised learning format for LSTM
    def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
        n_vars = 1 if type(data) is list else data.shape[1]
        df = pd.DataFrame(data)
        cols, names = list(), list()
        # Input sequence (t-n, ... t-1)
        for i in range(n_in, 0, -1):
            cols.append(df.shift(i))
            names += [('var%d(t-%d)' % (j+1, i)) for j in range(n_vars)]
        # Forecast sequence (t, t+1, ... t+n)
        for i in range(0, n_out):
            cols.append(df.shift(-i))
            if i == 0:
                names += [('var%d(t)' % (j+1)) for j in range(n_vars)]
            else:
                names += [('var%d(t+%d)' % (j+1, i)) for j in range(n_vars)]
        # Concatenate all columns
        agg = pd.concat(cols, axis=1)
        agg.columns = names
        # Drop rows with NaN values
        if dropnan:
            agg.dropna(inplace=True)
        return agg

    # Ensure data is in numpy array format
    values = df_resampled.values
    values = values.reshape((len(values), 1))

    # Normalize features
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(values)

    # Frame as supervised learning
    reframed = series_to_supervised(scaled, 1, 1)

    # Split into train and test sets
    values = reframed.values
    n_train_days = len(values) - 15  # Keep last 15 days for testing
    train = values[:n_train_days, :]
    test = values[n_train_days:, :]

    # Split into input and output
    X_train, y_train = train[:, :-1], train[:, -1]
    X_test, y_test = test[:, :-1], test[:, -1]

    # Reshape input to be 3D [samples, timesteps, features]
    X_train = X_train.reshape((X_train.shape[0], 1, X_train.shape[1]))
    X_test = X_test.reshape((X_test.shape[0], 1, X_test.shape[1]))

    # Design LSTM network
    model = Sequential()
    model.add(LSTM(128, input_shape=(X_train.shape[1], X_train.shape[2])))
    model.add(Dense(1))
    model.compile(loss='mae', optimizer='adam')

    # Custom callback to make predictions on test data after each epoch
    class PredictionCallback(Callback):
        def __init__(self, X_test, scaler):
            self.X_test = X_test
            self.scaler = scaler
            self.predictions = []

        def on_epoch_end(self, epoch, logs=None):
            # Predict on test data
            y_pred = self.model.predict(self.X_test)
            # Inverse transform predictions
            y_pred_inv = self.scaler.inverse_transform(y_pred)
            self.predictions.append(y_pred_inv)
            # Safeguard print statement
            safe_print(f"Epoch {epoch+1}: Predictions - {y_pred_inv}")

    callback = PredictionCallback(X_test, scaler)
    history = model.fit(X_train, y_train, epochs=40, batch_size=72, validation_data=(X_test, y_test), verbose=2, shuffle=False, callbacks=[callback])

    # Evaluate predictions
    y_pred_inv = callback.predictions[-1]
    y_test_inv = scaler.inverse_transform(y_test.reshape(-1, 1))
    mae = mean_absolute_error(y_test_inv, y_pred_inv)
    rmse = np.sqrt(mean_squared_error(y_test_inv, y_pred_inv))
    safe_print(f'Mean Absolute Error (MAE): {mae}')
    safe_print(f'Root Mean Square Error (RMSE): {rmse}')

    # Prepare JSON output
    json_output = []
    for i in range(len(y_test_inv)):
        json_output.append({
            'day': df_resampled.index[-15:].date[i].strftime('%Y-%m-%d'),
            'actual_value': float(y_test_inv[i][0]),
            'predicted_value': float(y_pred_inv[i][0])
        })

    # Save JSON output to a file
    with open('forecast_results.json', 'w', encoding='utf-8') as json_file:
        json.dump(json_output, json_file, indent=4)

    return json_output

# Example usage
result = forecast_earthquakes_LSTM(3.0, 7.0, 0, 70, '2020-01-01', '2024-01-01', 'Python/static/final_earthquake_catalogue_v2.db', 'earthquake_database')
