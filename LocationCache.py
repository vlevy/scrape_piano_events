import mysql.connector


class LocationCache:
    """The LocationCache class provides a simple interface to a MySQL database for storing and looking up locations by latitude and longitude."""

    FIX_POINT_FACTOR: int = 10**5

    def __init__(self, host: str, user: str, password: str, database: str) -> None:
        """
        Initializes the LocationCache with database connection parameters and connects to the database.

        Args:
            host (str): The database host.
            user (str): The database user.
            password (str): The database password.
            database (str): The database name.
        """

        self.host: str = host
        self.user: str = user
        self.password: str = password
        self.database: str = database
        self.connection: mysql.connector.connection.MySQLConnection | None = None
        self._connect_to_db()

    def _connect_to_db(self) -> None:
        """
        Connects to the MySQL database using the provided connection parameters.
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host, user=self.user, password=self.password, database=self.database
            )
            self.cursor = self.connection.cursor()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection = None

    def look_up_location(self, latitude: float, longitude: float) -> bool | None:
        """
        Looks up a location in the database by latitude and longitude.

        Args:
            latitude (float): The latitude of the location.
            longitude (float): The longitude of the location.

        Returns:
            bool | None: The boolean value if a match is found, otherwise None.
        """
        if self.connection is None:
            print("No database connection.")
            return None
        try:
            lat_int = int(latitude * self.FIX_POINT_FACTOR)
            lon_int = int(longitude * self.FIX_POINT_FACTOR)
            query = "SELECT is_in_nyc FROM location_table WHERE latitude = %s AND longitude = %s"
            self.cursor.execute(query, (lat_int, lon_int))
            result = self.cursor.fetchone()
            if result:
                return bool(result[0])  # Return the boolean value
            return None
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None

    def store_location(self, latitude: float, longitude: float, is_in_nyc: bool) -> None:
        """
        Stores a location in the database with the given latitude, longitude, and boolean value.

        Args:
            latitude (float): The latitude of the location.
            longitude (float): The longitude of the location.
            is_in_nyc (bool): The boolean value indicating whether the location is in NYC.
        """
        if self.connection is None:
            print("No database connection.")
            return
        try:
            lat_int = int(latitude * self.FIX_POINT_FACTOR)
            lon_int = int(longitude * self.FIX_POINT_FACTOR)
            query = "INSERT INTO location_table (latitude, longitude, is_in_nyc) VALUES (%s, %s, %s)"
            self.cursor.execute(query, (lat_int, lon_int, is_in_nyc))
            self.connection.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    def __del__(self) -> None:
        """
        Closes the database connection when the object is deleted.
        """
        if self.connection:
            self.cursor.close()
            self.connection.close()
