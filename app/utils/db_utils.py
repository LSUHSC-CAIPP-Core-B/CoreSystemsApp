import json
import re
from datetime import datetime

import pandas as pd
import pymysql


class db_utils:
    """A utility class for database operations, including reading JSON configurations, executing SQL queries, 
    and validating date formats.
    """
    @staticmethod
    def json_Reader(path: str) -> dict:
        """Reads a JSON file from the given path and extracts the 'db_config' section.

        :param path: The file path to the JSON file.
        :type path: str
        :return: The db_config dictionary from the JSON file, or an empty dictionary if not found.
        :rtype: dict
        """
        
        with open(path, 'r') as file:
            config_data = json.load(file)
        db_config = config_data.get('db_config', {})

        return db_config
    
    @staticmethod
    def toDataframe(query: str, path: str, *, params=None) -> pd.DataFrame:
        """Executes a SQL query on a database and converts the result into a pandas DataFrame.

        :param query: The SQL query to be executed.
        :type query: str
        :param path: The file path to the JSON file containing the database connection.
        :type path: str
        :param params: Parameters to be passed with the SQL query, defaults to None
        :type params: dict, optional
        :return: The DataFrame containing the query results.
        :rtype: pd.DataFrame
        """

        try:
            mydb = pymysql.connect(**db_utils.json_Reader(path))
            result_dataFrame = pd.read_sql_query(query, mydb, params=params)
            
            mydb.close()
            return result_dataFrame
        except Exception as e:
            print(str(e))
            mydb.close()
    
    @staticmethod
    def execute(query: str, path: str, *, params=None):
        """Executes a write SQL command (INSERT, UPDATE, DELETE).

        :param query:The SQL query to be executed.
        :type query: str
        :param path: The file path to the JSON file containing the database connection.
        :type path: str
        :param params: Parameters to bind to the SQL statement, defaults to None
        :type params: dict, optional
        """
        db_config = db_utils.json_Reader(path)
        connection = pymysql.connect(**db_config)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params or {})
            connection.commit()
            connection.close()
        except Exception as e:
            print(f"[DB EXEC ERROR]: {e}")
            if connection:
                connection.rollback()
                connection.close()

    @staticmethod
    def isValidDateFormat(expiration_date: str) -> bool:
        """Checks if the given expiration date string matches the MySQL date format YYYY-MM-DD.

        :param expiration_date: Date string to be validated.
        :type expiration_date: str
        :return: True if the date string matches the "YYYY-MM-DD" format, False otherwise.
        :rtype: bool
        """

        datePattern = r"^\d{4}-\d{2}-\d{2}$"
        
        # Checks if the string matches the pattern
        if re.match(datePattern, expiration_date):
            return True
        else: # The string does not match the "YYYY-MM-DD" format
            return False

    @staticmethod
    def isValidDate(expiration_date: str) -> bool:
        """Validates whether the given expiration date string is a valid date according to the "YYYY-MM-DD" format.

        :param expiration_date: Date string to be validated.
        :type expiration_date: str
        :return:  True if the string is a valid date, False otherwise.
        :rtype: bool
        """

        try: # Tries to convert the string to a datetime object
            datetime.strptime(expiration_date, "%Y-%m-%d")
            return True
        except ValueError: # The string is in the correct format but not a valid date
            return False