import os
from typing import List

import mysql.connector


def retrieve_upcoming_urls() -> List[str]:
    """Retrieve the URLs of the upcoming events from a MySQL database view"""
    # Reading database credentials from environment variables
    host = os.getenv("WEBSITE_DB_HOST")
    user = os.getenv("WEBSITE_DB_USER")
    password = os.getenv("WEBSITE_DB_PASSWORD")
    database = os.getenv("WEBSITE_DB_NAME")
    view_name = "upcoming_events_view"

    # Print out all connection parameters for debugging
    print(f"host: {host}, user: {user}, password: {password}, database: {database}")
    print(f"Reading existing URLs from the database")
    try:
        # Connect to the database
        connection = mysql.connector.connect(host=host, user=user, password=password, database=database)
        cursor = connection.cursor()
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return list()

    rows = list()
    try:
        # Query the database
        cursor.execute(f"SELECT event_url FROM {view_name}")
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Error querying the database: {e}")
        return list()
    finally:
        # Close the connection
        cursor.close()
        connection.close()

    if not rows:
        return list()

    # Return the URLs
    return [row[0] for row in rows]
