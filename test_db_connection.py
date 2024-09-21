import mysql.connector
from mysql.connector import Error

def test_db_connection():
    connection = None  # Initialize the connection variable
    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",  # Replace with your server IP
            user="root",            # Username
            password="Slidefire556556",            # No password
            database="4050_test"    # Replace with your database name, if needed
        )

        if connection.is_connected():
            print("Connected to MySQL database")

    except Error as e:
        print(f"Error: {e}")

    finally:
        if connection is not None and connection.is_connected():
            connection.close()
            print("MySQL connection is closed")

if __name__ == "__main__":
    test_db_connection()
