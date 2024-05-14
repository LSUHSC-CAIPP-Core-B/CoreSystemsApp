import mysql.connector as connection
from datetime import datetime
import pandas as pd
import pymysql
import json
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
    def toDataframe(query: str, params=None) -> any:
        """
        Takes in query, database, and parameter and converts query to a dataframe.
        
        query(str): query to convert to dataframe
        database_name(str): database name for connection
        param(str)or(None): Parameter to put in query

        return: dataframe from the query passed
        """

        try:
            mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreC.json', 'r'))
            # Using bind parameters to prevent SQL injection
            result_dataFrame = pd.read_sql_query(query, mydb, params=params)
            
            mydb.close()  # closes the connection
            return result_dataFrame
        except Exception as e:
            print(str(e))
            mydb.close()