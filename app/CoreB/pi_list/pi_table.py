from typing import IO, Hashable, Any

import pymysql
from app.abstract_classes.BaseDatabaseTable import BaseDatabaseTable
from app.utils.db_utils import db_utils
from app.utils.search_utils import search_utils

class PI_table(BaseDatabaseTable):
    """ Concrete class
    
    Inherits from abstract class BaseDatabaseTable

    :param BaseDatabaseTable: Abstract Class BaseDatabaseTable
    :type BaseDatabaseTable: type
    """
    def display(self, Uinputs: str, sort: str) -> list[dict[Hashable, Any]]:
        # Maps sorting options to their corresponding SQL names
        sort_orders = {
            'PI full name': 'PI full name',
            'PI ID': 'PI ID',
            'Department': 'Department',
        }

        # Check if sort is in the dictionary, if not then uses default value
        order_by = sort_orders.get(sort, 'Not Sorted')

        query = "Select * FROM pi_info;"

        # Creates Dataframe
        SqlData = db_utils.toDataframe(query,'app/Credentials/CoreB.json')
        

        # * Fuzzy Search *
        # Checks whether filters are being used
        # If filters are used then implements fuzzy matching
        if len(Uinputs) != 0:
            columns_to_check = ["PI full name", "Department"]
            
            if order_by == 'Not Sorted':
                data = search_utils.search_data(Uinputs, columns_to_check, 50, SqlData)
            else:
                data = search_utils.sort_searched_data(Uinputs, columns_to_check, 50, SqlData, order_by)
            
            # If no match is found displays empty row
            if not data:
                dataFrame = db_utils.toDataframe("Select * FROM pi_info;", 'app/Credentials/CoreB.json')
                data = dataFrame.to_dict(orient='records')
        else: # If no search filters are used
            # Converts to a list of dictionaries
            data = SqlData.to_dict(orient='records')
        return data
    
    def change(self, params):
        mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreB.json'))
        cursor = mydb.cursor()

        # SQL Change query
        query = "UPDATE pi_info SET `PI full name` = %(PI_full_name)s, `PI ID` = %(PI_ID)s, email = %(email)s, Department = %(Department)s   WHERE `index` = %(index)s;"
        #Execute SQL query
        cursor.execute(query, params)

        # Commit the transaction
        mydb.commit()

        # Commit the transaction
        cursor.close()
        mydb.close()
    
    def add(self, params):
        return super().add(params)
    
    def delete(self, primary_key):
        return super().delete(primary_key)