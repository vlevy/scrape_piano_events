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
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection = None

    def look_up_location(self, latitude: float, longitude: float, venue: str) -> bool | None:
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
            query = "SELECT venue, is_in_nyc FROM location_table WHERE latitude = %s AND longitude = %s"
            cursor = self.connection.cursor()
            cursor.execute(query, (lat_int, lon_int))
            result = cursor.fetchone()
            if not result:
                return None
            existing_venue: str = result[0]
            is_in: bool = bool(result[1])
            if not existing_venue:
                # Venue was not stored originally, so update the location with the venue
                self.set_venue(latitude, longitude, venue)
            return is_in
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None

    def store_location(self, latitude: float, longitude: float, venue: str, is_in_nyc: bool) -> None:
        """
        Stores a location in the database with the given latitude, longitude, and boolean value.

        Args:
            latitude (float): The latitude of the location.
            longitude (float): The longitude of the location.
            venue (str): The name of the venue.
            is_in_nyc (bool): The boolean value indicating whether the location is in NYC.
        """
        if self.connection is None:
            print("No database connection.")
            return
        try:
            lat_int = int(latitude * self.FIX_POINT_FACTOR)
            lon_int = int(longitude * self.FIX_POINT_FACTOR)
            query = "INSERT INTO location_table (latitude, longitude, venue, is_in_nyc) VALUES (%s, %s, %s, %s)"
            cursor = self.connection.cursor()
            cursor.execute(query, (lat_int, lon_int, venue[:255], is_in_nyc))
            self.connection.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    def remove_location(self, latitude: float, longitude: float) -> None:
        """
        Removes a location from the database by latitude and longitude.

        Args:
            latitude (float): The latitude of the location.
            longitude (float): The longitude of the location.
        """
        if self.connection is None:
            print("No database connection.")
            return
        try:
            lat_int = int(latitude * self.FIX_POINT_FACTOR)
            lon_int = int(longitude * self.FIX_POINT_FACTOR)
            query = "DELETE FROM location_table WHERE latitude = %s AND longitude = %s"
            cursor = self.connection.cursor()
            cursor.execute(query, (lat_int, lon_int))
            self.connection.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    def set_venue(self, latitude: float, longitude: float, venue: str) -> None:
        """
        Sets the venue for a location in the database by latitude and longitude.

        Args:
            latitude (float): The latitude of the location.
            longitude (float): The longitude of the location.
            venue (str): The venue name or description.
        """
        if self.connection is None:
            print("No database connection.")
            return
        try:
            lat_int = int(latitude * self.FIX_POINT_FACTOR)
            lon_int = int(longitude * self.FIX_POINT_FACTOR)
            query = "UPDATE location_table SET venue = %s WHERE latitude = %s AND longitude = %s"
            cursor = self.connection.cursor()
            cursor.execute(query, (venue, lat_int, lon_int))
            self.connection.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    def __del__(self) -> None:
        """
        Closes the database connection when the object is deleted.
        """
        if self.connection:
            self.connection.close()


"""
CREATE TABLE `location_table` (
  `id` int NOT NULL AUTO_INCREMENT,
  `latitude` int NOT NULL,
  `longitude` int NOT NULL,
  `is_in_nyc` tinyint(1) NOT NULL,
  `venue` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_latitude_longitude` (`latitude`,`longitude`)
) ENGINE=InnoDB AUTO_INCREMENT=56 DEFAULT CHARSET=utf8;
"""
