import pandas as pd
import numpy as np
import sqlite3
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.callbacks import Callback
from sklearn.metrics import mean_absolute_error, mean_squared_error
import json
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, DayLocator
from datetime import datetime
import os
from threading import Lock  # For thread-safe plotting

# Set the default encoding to utf-8 for print statements
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Lock for serializing access to the plotting code
plot_lock = Lock()

def forecast_earthquakes_LSTM(magnitude_min, magnitude_max, depth_min, depth_max, forecast_date, sqlite_file, table_name):
    def safe_print(*args, **kwargs):
        try:
            print(*args, **kwargs)
        except UnicodeEncodeError:
            print("Encoding error occurred during print operation.")

    try:
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

        # Convert forecast_date to datetime object
        forecast_date = datetime.strptime(forecast_date, '%Y-%m-%d').date()

        # Filter data based on specified criteria
        filtered_data = data[
            (data['Mag'] >= magnitude_min) & (data['Mag'] <= magnitude_max) &
            (data['Depth'] >= depth_min) & (data['Depth'] <= depth_max) &
            (data['Date'] <= forecast_date)
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

        # Prepare JSON output with stripped decimal values
        json_output = []
        for i in range(len(y_test_inv)):
            json_output.append({
                'day': df_resampled.index[-15:].date[i].strftime('%Y-%m-%d'),
                'actual_value': int(y_test_inv[i][0]),
                'predicted_value': int(y_pred_inv[i][0])
            })

        # Save JSON output to a file
        json_output_file = 'forecast_results.json'
        with open(json_output_file, 'w', encoding='utf-8') as json_file:
            json.dump(json_output, json_file, indent=4)

        # Plotting
        with plot_lock:
            plt.clf()  # Clear the current figure
            plt.figure(figsize=(8, 6))  # Adjust the figure size as needed
            plt.plot(df_resampled.index[-15:], y_test_inv, label='Actual Frequency', linestyle='-', marker='o')  # Actual values
            plt.plot(df_resampled.index[-15:], y_pred_inv, label='LSTM Forecast', color='orange', linestyle='--', marker='s')  # Predicted values
            plt.legend()
            plt.title('Actual Frequencies vs. LSTM Predictions')
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
            month_year = df_resampled.index[-15:].date[0].strftime('%B %Y')  # Get month and year of the forecast start date
            plt.text(0.01, -0.15, month_year, transform=ax.transAxes, fontsize=10, ha='left', color='gray')  # Place text at bottom left

            plt.tight_layout()  # Adjust layout to prevent clipping of labels
            plot_file_path = 'forecast_plot.png'
            plt.savefig(os.path.join('Python/static', plot_file_path))
            plt.close()

        return json_output, plot_file_path

    except Exception as e:
        safe_print(f"Error in LSTM forecasting: {str(e)}")
        return None, None

# Example usage
# forecast_date = '2023-12-16'
# result, plot_path = forecast_earthquakes_LSTM(3.0, 7.0, 0, 70, forecast_date, 'Python/static/final_earthquake_catalogue_v2.db', 'earthquake_database')
# if result is not None:
#     print(f"LSTM forecast JSON output saved to 'forecast_results.json' and plot saved to
