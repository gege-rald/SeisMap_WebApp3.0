from flask import Flask, render_template, request, jsonify, send_from_directory
import logging
import sqlite3
from datetime import datetime
from threading import Lock
from sklearn.cluster import DBSCAN
import pandas as pd
import numpy as np
from clustering_dbscan import prfrm_clustering
from time_series_ARIMA import forecast_earthquakes_ARIMA
from time_series_SARIMA import forecast_earthquakes_sarima
from time_series_LSTM import forecast_earthquakes_LSTM
import os

app = Flask(__name__, template_folder='HTML', static_folder='static')

# Set Matplotlib to use the 'Agg' backend
import matplotlib
matplotlib.use('Agg')

# Lock for serializing access to the plotting code
plot_lock = Lock()

# Ensure logging is set up
logging.basicConfig(level=logging.DEBUG)

def init_db():
    conn = sqlite3.connect('Python/static/final_earthquake_catalogue_v2.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS earthquake_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            algorithm TEXT,
            magnitude_min REAL,
            magnitude_max REAL,
            depth_min REAL,
            depth_max REAL,
            start_date TEXT,
            end_date TEXT,
            forecast_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_last_entry():
    conn = sqlite3.connect('Python/static/final_earthquake_catalogue_v2.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM earthquake_data ORDER BY id DESC LIMIT 1')
    last_entry = cursor.fetchone()
    conn.close()
    if last_entry:
        return last_entry
    else:
        return None

def convert_to_millis(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            print(f"Error parsing date: {date_str}")
            return None
    return int(dt.timestamp() * 1000)

def update_millis(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM PRAGMA_TABLE_INFO('earthquake_database')")
    column_names = [row[0] for row in cursor.fetchall()]

    if 'Millis' not in column_names:
        cursor.execute("ALTER TABLE earthquake_database ADD COLUMN Millis INTEGER")
        conn.commit()

    cursor.execute("SELECT rowid, Date_Time FROM earthquake_database WHERE Millis IS NULL")
    for row in cursor.fetchall():
        row_id, date_str = row
        millis = convert_to_millis(date_str)
        if millis:
            cursor.execute("UPDATE earthquake_database SET Millis = ? WHERE rowid = ?", (millis, row_id))

    conn.commit()
    conn.close()

def parse_date_to_millis(date_str, format='%Y-%m-%d'):
    dt = datetime.strptime(date_str, format)
    return int(dt.timestamp() * 1000)

def get_earthquake_data(magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date):
    update_millis("Python/static/final_earthquake_catalogue_v2.db")
    conn = sqlite3.connect('Python/static/final_earthquake_catalogue_v2.db')
    cursor = conn.cursor()
    
    start_date_millis = parse_date_to_millis(start_date)
    end_date_millis = parse_date_to_millis(end_date)

    query = '''
        SELECT * FROM earthquake_database
        WHERE Mag BETWEEN ? AND ?  
        AND Depth BETWEEN ? AND ?  
        AND Millis >= ? 
        AND Millis <= ?
    '''
    cursor.execute(query, (magnitude_min, magnitude_max, depth_min, depth_max, start_date_millis, end_date_millis))
    data = cursor.fetchall()
    conn.close()
    return data

@app.route('/filter-count', methods=['GET'])
def filter_count():
    try:
        last_entry = get_last_entry()
        if not last_entry:
            raise ValueError("No data available in the database")

        id, algorithm, magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date, forecast_date = last_entry

        earthquake_data = get_earthquake_data(magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date)

        num_filtered_entries = len(earthquake_data)
        print("Number of filtered data entries:", num_filtered_entries)

        response = {
            'status': 'success',
            'message': 'Filtered data count retrieved successfully',
            'count': num_filtered_entries
        }
        return jsonify(response)
    
    except Exception as e:
        logging.error(f"Error during data filtering: {str(e)}")
        response = {
            'status': 'error',
            'message': str(e)
        }
        return jsonify(response), 500

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/perform-clustering', methods=['POST'])
def perform_clustering():
    try:
        data = request.json
        if not data:
            raise ValueError("No JSON data received")
        
        algorithm = data.get('algorithm')
        magnitude_range = data.get('magnitudeRange')
        depth_range = data.get('depthRange')
        date_range = data.get('dateRange')
        forecast_date = data.get('forecastDate')

        logging.debug(data)
        logging.debug(f"Algorithm: {algorithm}")
        logging.debug(f"Magnitude Range: Min = {magnitude_range['min']}, Max = {magnitude_range['max']}")
        logging.debug(f"Depth Range: Min = {depth_range['min']}, Max = {depth_range['max']}")
        logging.debug(f"Date Range: Start = {date_range['start']}, End = {date_range['end']}")

        start_date = datetime.strptime(date_range['start'], '%Y-%m-%d')
        end_date = datetime.strptime(date_range['end'], '%Y-%m-%d')
        forecast_millis = datetime.strptime(forecast_date, '%Y-%m-%d')  # Corrected line

        conn = sqlite3.connect('Python/static/final_earthquake_catalogue_v2.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO earthquake_data (algorithm, magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date, forecast_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (algorithm, magnitude_range['min'], magnitude_range['max'], depth_range['min'], depth_range['max'], date_range['start'], date_range['end'], forecast_date))
        conn.commit()
        conn.close()

        last_entry = get_last_entry()
        logging.debug(last_entry)
        sqlite_file = 'Python/static/final_earthquake_catalogue_v2.db'
        table_name = 'earthquake_database'  

        id, algorithm, magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date, forecast_date = last_entry
        filtered_data = get_earthquake_data(magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date)

        # Ensure thread-safe plotting with lock
        with plot_lock:
            # Perform forecasting based on the selected algorithm
            if algorithm == 'arima':
                json_output, plot_file_path =  forecast_earthquakes_ARIMA(magnitude_min, magnitude_max, depth_min, depth_max, forecast_date, sqlite_file, table_name)
            elif algorithm == 'sarima':
                json_output, plot_file_path =  forecast_earthquakes_sarima(magnitude_min, magnitude_max, depth_min, depth_max, forecast_date, sqlite_file, table_name)
            elif algorithm == 'lstm':
                json_output, plot_file_path = forecast_earthquakes_LSTM(magnitude_min, magnitude_max, depth_min, depth_max, forecast_date, sqlite_file, table_name)
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

        logging.debug(forecast_date)
        logging.debug("pass here")
        logging.debug("pass 2")
        logging.debug("pass here 1:")

        response = {
            'status': 'success',
            'forecast_results': json_output,  # Send the forecast results
            'plot_file_path': f'/static/{plot_file_path}'
        }
        return jsonify(response)
    
    except Exception as e:
        logging.error(f"Error during clustering: {str(e)}")
        response = {
            'status': 'error',
            'message': str(e)
        }
        return jsonify(response), 500


@app.route('/update-dataset', methods=['POST'])
def update_dataset():
    try:
        # check rows
        conn = sqlite3.connect('Python/static/final_earthquake_catalogue_v2.db')

        cursor = conn.cursor()
        cursor.execute("select * from PRAGMA_TABLE_INFO('earthquake_database')")
        column_names = [row[1] for row in cursor.fetchall()]
        for name in column_names:
            print("name:", name)

        conn.commit()
        conn.close()

        data = request.json.get('data')
        options = request.json.get('options')
        logging.debug(data)
        
        if not data:
            raise ValueError("No data received")
        
        conn = sqlite3.connect('Python/static/final_earthquake_catalogue_v2.db')
        conn.set_trace_callback(print)
        cursor = conn.cursor()

        if options and options.get('override'):
            cursor.execute('DELETE FROM earthquake_data')

        for row in data:
            date_time = row.get('date_time')
            latitude = row.get('latitude')
            longitude = row.get('longitude')
            depth = row.get('depth')
            magnitude = row.get('magnitude')
            location = row.get('location')

            millis = convert_to_millis(date_time)
            
            cursor.execute('''
                INSERT INTO earthquake_database (date_time, latitude, longitude, depth, mag, location, millis)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (date_time, latitude, longitude, depth, magnitude, location, millis))

        conn.commit()
        conn.close()


        response = {
            'status': 'success',
            'message': 'Dataset updated successfully'
        }
        return jsonify(response)

    except Exception as e:
        logging.error(f"Error updating dataset: {str(e)}")
        response = {
            'status': 'error',
            'message': str(e)
        }
        return jsonify(response), 500


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
