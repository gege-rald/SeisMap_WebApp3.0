import sqlite3
from datetime import datetime

# Function to convert date string to milliseconds
def date_to_millis(date_str, format='%m/%d/%Y'):
    dt = datetime.strptime(date_str, format)
    return int(dt.timestamp() * 1000)

def update_dates_to_millis():
    conn = sqlite3.connect('Python/static/final_earthquake_catalogue.db')
    cursor = conn.cursor()
    
    # Check if DateMillis column already exists
    cursor.execute("PRAGMA table_info(earthquake_database)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'DateMillis' not in columns:
        # Add a new column for date in milliseconds if it doesn't exist
        cursor.execute('ALTER TABLE earthquake_database ADD COLUMN DateMillis INTEGER')
    
    # Select all rows to update the new column with converted date values
    cursor.execute('SELECT id, Date FROM earthquake_database')
    rows = cursor.fetchall()
    
    # Convert each date to milliseconds and update the database
    for row in rows:
        id = row[0]
        date_str = row[1]
        try:
            date_millis = date_to_millis(date_str, '%m/%d/%Y')
            cursor.execute('UPDATE earthquake_database SET DateMillis = ? WHERE id = ?', (date_millis, id))
        except ValueError:
            print(f"Error converting date {date_str} for id {id}")
    
    conn.commit()
    conn.close()

# Run the update function
update_dates_to_millis()
