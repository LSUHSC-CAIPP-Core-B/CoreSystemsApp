import mysql.connector as connection
from datetime import datetime
import pandas as pd
import pymysql
import json
import re
class db_utils:
    @staticmethod
    def json_Reader(path: str, mode: str) -> any:
        '''
        Takes in path to json file and file mode like 'r','w','a'
        '''
        with open(path, mode) as file:
            config_data = json.load(file)
        db_config = config_data.get('db_config')
        db_config
        db_config = config_data.get('db_config', {})

        return db_config
    
    @staticmethod
    def toDataframe(query: str, path: str, params=None) -> any:
        """
        Takes in query, database, and parameter and converts query to a dataframe.

        return: dataframe from the query passed
        """

        try:
            mydb = pymysql.connect(**db_utils.json_Reader(path, 'r'))
            result_dataFrame = pd.read_sql_query(query, mydb, params=params)
            
            mydb.close()
            return result_dataFrame
        except Exception as e:
            print(str(e))
            mydb.close()
    
    def isValidDateFormat(expiration_date: str) -> bool:
        '''
        Takes in expiration date to check if valid format for mysql.
        datePattern defines regex pattern for "YYYY-MM-DD"
        '''

        datePattern = r"^\d{4}-\d{2}-\d{2}$"
        
        # Checks if the string matches the pattern
        if re.match(datePattern, expiration_date):
            return True
        else: # The string does not match the "YYYY-MM-DD" format
            return False

    def isValidDate(expiration_date: str) -> bool:
        '''
        Takes in expiration date to check if valid date for mysql.
        '''
        try: # Tries to convert the string to a datetime object
            datetime.strptime(expiration_date, "%Y-%m-%d")
            return True
        except ValueError: # The string is in the correct format but not a valid date
            return False