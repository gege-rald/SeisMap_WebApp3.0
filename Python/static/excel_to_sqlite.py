import sqlite3
import pandas as pd
from datetime import datetime


def parse_date_time(date_time_str):
    # Remove non-breaking space (if present)
    date_time_str = date_time_str.strip("\xa0")

    # Define formats for full and abbreviated months
    date_formats = [
        "%d %B %Y - %I:%M %p",  # Full month name (e.g., 31 December 2017)
        "%d %b %Y - %I:%M %p"   # Abbreviated month name (e.g., 31 Dec 2017)
    ]

    for date_format in date_formats:
        try:
            return datetime.strptime(date_time_str, date_format)
        except ValueError:
            pass  # Try the next format if parsing fails

    # Handle parsing error (log the error or return a default value)
    print(f"Error parsing date: {date_time_str}")
    return None  # Or any other default value for invalid dates


def create_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS earthquake_database (
            Date_Time TEXT,
            Latitude REAL,
            Longitude REAL,
            Depth REAL,
            Mag REAL,
            Location TEXT
        )
    ''')
    conn.commit()


def insert_data(conn, data):
    cursor = conn.cursor()
    for row in data.itertuples(index=False):
        try:
            date_time = parse_date_time(row.Date_Time)
            if date_time:  # Check if parsing was successful (not None)
                cursor.execute('''
                    INSERT INTO earthquake_database (Date_Time, Latitude, Longitude, Depth, Mag, Location)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (date_time, row.Latitude, row.Longitude, row.Depth, row.Mag, row.Location))
        except Exception as e:
            # Handle other potential errors (e.g., database insertion errors)
            print(f"Error inserting data: {e}")
    conn.commit()


def excel_to_sqlite(excel_file, db_file_path):
    # Read Excel file
    df = pd.read_excel(excel_file)

    # Connect to SQLite database
    conn = sqlite3.connect(db_file_path)

    # Create table if not exists
    create_table(conn)

    # Insert data into database with error handling
    insert_data(conn, df)

    # Close connection
    conn.close()


# Specify the paths to the Excel file and the desired database file location
excel_file = "Python/static/final_earthquake_catalogue.xlsx"
db_file_path = "Python/static/final_earthquake_catalogue_v2.db"

# Call the function with the specified file paths
excel_to_sqlite(excel_file, db_file_path)
