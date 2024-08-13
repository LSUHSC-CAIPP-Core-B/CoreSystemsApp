from typing import IO

import pymysql
from app.abstract_classes.BaseDatabaseTable import BaseDatabaseTable
from app.utils.db_utils import db_utils
from app.utils.logging_utils.logGenerator import Logger
from app.utils.search_utils import search_utils
from flask import flash
from fuzzywuzzy import fuzz
from typing_extensions import override

# Logging set up
logFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LogGenerator = Logger(logFormat=logFormat, logFile='application.log')
logger = LogGenerator.generateLogger()

class stockTable(BaseDatabaseTable):
    """ Concrete class
    
    Inherits from abstract class BaseDatabaseTable

    :param BaseDatabaseTable: Abstract Class BaseDatabaseTable
    :type BaseDatabaseTable: type
    """

    @override
    def display(self, Uinputs: str, sort: str) -> dict:
        """Filters table then displays it 

        :param Uinputs: User Inputs
        :type Uinputs: str
        :param sort: what to sort by
        :type sort: str
        :param sort_orders: Maps sorting options to their corresponding SQL names
        :type sort_orders: dict
        :return: data
        :rtype: dict
        """
        # Maps sorting options to their corresponding SQL names
        sort_orders = {
            'Product': 'Product_Name',
            'Cost': 'Unit_Price'
        }
        # Check if sort is in the dictionary, if not then uses default value
        order_by = sort_orders.get(sort, 'Quantity')

        # Validate the order_by to prevent sql injection
        if order_by not in sort_orders.values():
            order_by = 'Quantity'  
        
        # Ascending vs Descending
        if sort == "QuantityAscending":
            query = f"SELECT S.Product_Num, O.Product_Name, O.Catalog_Num , O.Company_Name, O.Unit_Price, S.Quantity FROM  Stock_Info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE O.Company_Name != 'N/A' AND O.Product_Name != '0' ORDER BY {order_by};"
        else:
            query = f"SELECT S.Product_Num, O.Product_Name, O.Catalog_Num , O.Company_Name, O.Unit_Price, S.Quantity FROM  Stock_Info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE O.Company_Name != 'N/A' AND O.Product_Name != '0' ORDER BY {order_by} DESC;"
        
        df = db_utils.toDataframe(query, 'app/Credentials/CoreC.json')
        SqlData = df
        
        # * Fuzzy Search *
        # Checks whether filters are being used
        # If filters are used then implements fuzzy matching
        if len(Uinputs) != 0:
            columns_to_check = ["Company_Name", "Product_Name"]
            print(f"Columns to check: {columns_to_check}\n Uinputs: {Uinputs}")
            data = search_utils.sort_searched_data(Uinputs, columns_to_check, 45, SqlData, order_by, {'Product_Name': 'Product', 'Catalog_Num': 'Catalog Number','Company_Name': 'Company Name', 'Unit_Price': 'Cost'})
            
            # If no match is found displays empty row
            if not data:
                dataFrame = db_utils.toDataframe("SELECT S.Product_Num, O.Product_Name, O.Catalog_Num , O.Company_Name, O.Unit_Price, S.Quantity FROM  Stock_Info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE O.Company_Name = 'N/A' ORDER BY Quantity;", 'app/Credentials/CoreC.json')
                dataFrame.rename(columns={'Product_Name': 'Product', 'Catalog_Num': 'Catalog Number','Company_Name': 'Company Name', 'Unit_Price': 'Cost'}, inplace=True)
                data = dataFrame.to_dict('records')
        else: # If no search filters are used
            # renaming columns and setting data variable
            SqlData.rename(columns={'Product_Name': 'Product', 'Catalog_Num': 'Catalog Number','Company_Name': 'Company Name', 'Unit_Price': 'Cost'}, inplace=True)
            # Converts to a list of dictionaries
            data = SqlData.to_dict(orient='records')
        return data
    
    @override
    def add(self, params: dict, Quantity: any) -> None:
        mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreC.json'))
        cursor = mydb.cursor()

        # SQL Add query
        query = "INSERT INTO Order_Info VALUES (null, %(CompanyParam)s, %(catalogNumParam)s, %(costParam)s, %(ProductParam)s);"
        query2 = "INSERT INTO Stock_Info VALUES (LAST_INSERT_ID(), %s);"
        logger.info(f"Executing queries: {query}, {query2} with params: {params}")
        #Execute SQL query
        cursor.execute(query, params)
        cursor.execute(query2, (Quantity,))

        # Commit the transaction
        mydb.commit()

        # Close the cursor and connection
        cursor.close()
        mydb.close()
    
    def change(self, params: dict, Quantity: any, primary_key:any) -> None:
        mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreC.json'))
        cursor = mydb.cursor()
        
        # SQL Change query
        query = "UPDATE Order_Info SET Company_name = %(CompanyParam)s, Catalog_Num = %(catalogNumParam)s, Unit_Price = %(costParam)s, Product_Name = %(ProductParam)s WHERE Order_Info.Product_Num = %(Pkey)s;"
        query2 = "UPDATE Stock_Info SET Quantity = %s WHERE Product_Num = %s;"
        logger.info(f"Executing queries: {query}, {query2} with params: {params}")
        #Execute SQL query
        cursor.execute(query, params)
        cursor.execute(query2, (Quantity, primary_key))

        # Commit the transaction
        mydb.commit()

        # Close the cursor and connection
        cursor.close()
        mydb.close()
    
    def delete(self, primary_key) -> None:
        mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreC.json'))
        cursor = mydb.cursor()

        # SQL DELETE query
        query = "DELETE FROM Order_Info WHERE Product_Num = %s"
        query2 = "DELETE FROM Stock_Info WHERE Product_Num = %s"
        logger.info(f"Executing queries: {query2}, {query} with params: {primary_key}")
        #Execute SQL query
        #! query2 must be executed first because of foreign key constraints
        cursor.execute(query2, (primary_key,))
        cursor.execute(query, (primary_key,))

        # Commit the transaction
        mydb.commit()

        # Close the cursor and connection
        cursor.close()
        mydb.close()

        logger.info("Deletion Complete!")

