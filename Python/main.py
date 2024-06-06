from flask import Flask, render_template, request, jsonify
import logging
import sqlite3
from datetime import datetime
from sklearn.cluster import DBSCAN
import pandas as pd
import numpy as np
from datetime import datetime

app = Flask(__name__, template_folder='HTML', static_folder='static')

def init_db():
    conn = sqlite3.connect('Python/static/final_earthquake_catalogue.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS earthquake_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            algorithm TEXT,
            clusters INTEGER,
            magnitude_min REAL,
            magnitude_max REAL,
            depth_min REAL,
            depth_max REAL,
            start_date TEXT,
            end_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_last_entry():
    conn = sqlite3.connect('Python/static/final_earthquake_catalogue.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM earthquake_data ORDER BY id DESC LIMIT 1')
    last_entry = cursor.fetchone()
    conn.close()
    print(last_entry)
    if last_entry:
        return last_entry  # Return all columns
    else:
        return None

# def parse_date(date_str):
#     return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y/%m/%d')

# def get_earthquake_data(magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date):
#     conn = sqlite3.connect('Python/static/final_earthquake_catalogue.db')
#     cursor = conn.cursor()
#     print(start_date)
#     print(end_date)
#     # Ensure the dates are in 'YYYY-MM-DD' format
#     start_date_parsed = parse_date(start_date)
#     end_date_parsed = parse_date(end_date)

#     print(start_date_parsed)
#     print(end_date_parsed)
    
#     query = '''
#         SELECT * FROM earthquake_database
#         WHERE Mag BETWEEN ? AND ?  
#         AND Depth BETWEEN ? AND ?  
#         AND strftime('%Y/%m/%d', Date) >= ? 
#         AND strftime('%Y/%m/%d', Date) <= ?
#     '''
#     cursor.execute(query, (magnitude_min, magnitude_max, depth_min, depth_max, start_date_parsed, end_date_parsed))
#     #cursor.execute(query, (magnitude_min, magnitude_max, depth_min, depth_max))
#     data = cursor.fetchall()
#     conn.close()
#     return data


def parse_date_to_millis(date_str, format='%Y-%m-%d'):
    dt = datetime.strptime(date_str, format)
    return int(dt.timestamp() * 1000)

def get_earthquake_data(magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date):
    conn = sqlite3.connect('Python/static/final_earthquake_catalogue.db')
    cursor = conn.cursor()

    # Convert start_date and end_date to milliseconds
    start_date_millis = parse_date_to_millis(start_date)
    end_date_millis = parse_date_to_millis(end_date)

    query = '''
        SELECT * FROM earthquake_database
        WHERE Mag BETWEEN ? AND ?  
        AND Depth BETWEEN ? AND ?  
        AND DateMillis >= ? 
        AND DateMillis <= ?
    '''
    cursor.execute(query, (magnitude_min, magnitude_max, depth_min, depth_max, start_date_millis, end_date_millis))
    data = cursor.fetchall()
    conn.close()
    return data





@app.route('/filter-count', methods=['GET'])
def filter_count():
    try:
        # Get the last added entry from the database
        last_entry = get_last_entry()
        if not last_entry:
            raise ValueError("No data available in the database")

        # Unpack the last entry data
        id, algorithm, clusters, magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date = last_entry

        # Fetch the earthquake data based on the last entry parameters
        earthquake_data = get_earthquake_data(magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date)

        # Print the number of filtered data entries
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
        clusters = data.get('clusters')
        magnitude_range = data.get('magnitudeRange')
        depth_range = data.get('depthRange')
        date_range = data.get('dateRange')

        logging.debug(data)
        logging.debug(f"Algorithm: {algorithm}")
        logging.debug(f"Clusters: {clusters}")
        logging.debug(f"Magnitude Range: Min = {magnitude_range['min']}, Max = {magnitude_range['max']}")
        logging.debug(f"Depth Range: Min = {depth_range['min']}, Max = {depth_range['max']}")
        logging.debug(f"Date Range: Start = {date_range['start']}, End = {date_range['end']}")

        # Convert date strings to datetime objects
        start_date = datetime.strptime(date_range['start'], '%Y-%m-%d')
        end_date = datetime.strptime(date_range['end'], '%Y-%m-%d')

        # Save data to the SQLite database
        conn = sqlite3.connect('Python/static/final_earthquake_catalogue.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO earthquake_data (algorithm, clusters, magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (algorithm, clusters, magnitude_range['min'], magnitude_range['max'], depth_range['min'], depth_range['max'], date_range['start'], date_range['end']))
        conn.commit()
        conn.close()

        # Fetch the filtered data count
        filter_count()

        response = {
            'status': 'success',
            'message': 'Clustering performed successfully',
            'received_data': data
        }
        return jsonify(response)
    
    except Exception as e:
        logging.error(f"Error during clustering: {str(e)}")
        response = {
            'status': 'error',
            'message': str(e)
        }
        return jsonify(response), 500

@app.route('/train-model', methods=['GET'])
def train_model():
    try:
        # Get the last added entry from the database
        last_entry = get_last_entry()
        if not last_entry:
            raise ValueError("No data available in the database")
        
        id, algorithm, clusters, magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date = last_entry

        # Fetch the earthquake data based on the last entry parameters
        earthquake_data = get_earthquake_data(magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date)
        
        if not earthquake_data:
            raise ValueError("No earthquake data available for the given parameters")

        # Convert the data to a DataFrame
        df = pd.DataFrame(earthquake_data, columns=['id', 'date', 'latitude', 'longitude', 'depth', 'magnitude', 'location'])
        
        # Prepare the features for clustering
        features = df[['latitude', 'longitude', 'depth', 'magnitude']].values

        # Train the DBSCAN model
        dbscan = DBSCAN(eps=0.5, min_samples=5)
        labels = dbscan.fit_predict(features)
        
        # Add the cluster labels to the DataFrame
        df['cluster'] = labels

        response = {
            'status': 'success',
            'message': 'Model trained successfully',
            'clusters': df.to_dict(orient='records')
        }
        return jsonify(response)
    
    except Exception as e:
        logging.error(f"Error during model training: {str(e)}")
        response = {
            'status': 'error',
            'message': str(e)
        }
        return jsonify(response), 500
    


if __name__ == '__main__':
    init_db()  # Initialize the database and table
    last_entry = get_last_entry()
    print(last_entry)
    if last_entry:
        id, algorithm, clusters, magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date = last_entry
        filtered_data = get_earthquake_data(magnitude_min, magnitude_max, depth_min, depth_max, start_date, end_date)
        print("Number of filtered data:", len(filtered_data))
    else:
        print("No data available.")
    app.run(debug=True)
