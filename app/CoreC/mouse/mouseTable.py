import pandas as pd
import pymysql
from app.abstract_classes.BaseDatabaseTable import BaseDatabaseTable
from app.utils.logging_utils.logGenerator import Logger
from app.utils.db_utils import db_utils
from flask_login import current_user

# Logging set up
logFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s - (Line: %(lineno)s [%(filename)s])'
LogGenerator = Logger(logFormat=logFormat, logFile='application.log')
logger = LogGenerator.generateLogger()

class mouseTable(BaseDatabaseTable):
    """Concrete class
    
    Inherits from abstract class BaseDatabaseTable

    :param BaseDatabaseTable: Abstract Class BaseDatabaseTable
    :type BaseDatabaseTable: type
    """
    
    def display(self, Uinputs: str, sort: str) -> dict:
        return super().display(Uinputs, sort)
    
    def add(self, params: dict) -> pd.DataFrame:
        mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreC.json'))
        cursor = mydb.cursor()

        user_id = current_user.id
        print(f"Current user id: {user_id}")

        # SQL Add query
        query = f"INSERT INTO Mouse_Stock VALUES (null, %(PI)s, %(Genotype)s, %(Description)s, %(Strain)s, %(Times Back Crossed)s, %(MTA Required)s, {user_id});"
        logger.info(f"Executing query: {query} with params: {params}")
        #Execute SQL query
        cursor.execute(query, params)

        # Commit the transaction
        mydb.commit()

        # Close the cursor and connection
        cursor.close()
        mydb.close()   

        # Gets newest antibody
        query = f"SELECT * FROM Mouse_Stock ORDER BY Stock_ID DESC LIMIT 1;"
        
        df = db_utils.toDataframe(query, 'app/Credentials/CoreC.json')
        return df
    
    def change(self, params: dict) -> None:
        return super().change(params)
    
    def delete(self, primary_key) -> None:
        return super().delete(primary_key)