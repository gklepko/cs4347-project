from dotenv import load_dotenv
import os
import csv
import mysql.connector

load_dotenv()  # Load environment variables from .env file

def insert_into_table(csv_path, table_name):
    # --- configure this for your environment ---
    conn = mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASS", "your_password"),
        database=os.environ.get("MYSQL_DB", "LIBMS"),
    )
    cursor = conn.cursor()

    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                raise ValueError("CSV file must have a header row.")

            columns = reader.fieldnames  # header row
            # Build: INSERT INTO table_name (`col1`,`col2`,...) VALUES (%s, %s, ...)
            col_list = ", ".join(f"`{col}`" for col in columns)
            placeholders = ", ".join(["%s"] * len(columns))

            # Use INSERT IGNORE so MySQL skips rows that violate constraints 
            # (e.g., duplicate primary/unique keys) instead of throwing an error.
            sql = f"INSERT IGNORE INTO {table_name} ({col_list}) VALUES ({placeholders})"

            # Insert each row
            for row in reader:
                # Keep column order consistent with header
                values = [
                    (row[col] if row[col] != "" else None)  # treat empty as NULL
                    for col in columns
                ]
                cursor.execute(sql, values)

        conn.commit()

    finally:
        cursor.close()
        conn.close()

def main():
    print("What csv are you inserting into the database?")
    input_path = input()
    if os.path.exists(input_path):
        print("What table is this being inserted into?")
        table = input()
        insert_into_table(input_path, table)

    else:
        print("Path of the provided file is invalid.")

if __name__ == "__main__":
    main()