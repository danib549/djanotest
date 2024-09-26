import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('db.sqlite3')

# Create a cursor object to interact with the database
cursor = conn.cursor()

# Execute a query to retrieve the list of tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

# Fetch all table names
tables = cursor.fetchall()

# Iterate through each table and print its contents
for table in tables:
    table_name = table[0]
    print(f"\nTable: {table_name}")
    
    # Execute a query to retrieve all rows from the current table
    cursor.execute(f"SELECT * FROM {table_name}")
    
    # Fetch all rows
    rows = cursor.fetchall()
    
    # Get column names
    column_names = [description[0] for description in cursor.description]
    
    # Print column names
    print(" | ".join(column_names))
    print("-" * 80)
    
    # Print rows
    for row in rows:
        print(" | ".join(str(value) for value in row))

# Close the cursor and connection
cursor.close()
conn.close()
