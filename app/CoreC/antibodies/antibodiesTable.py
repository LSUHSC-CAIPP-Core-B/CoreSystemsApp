from typing import IO
from typing_extensions import override

from flask import flash, redirect, url_for

from app.abstract_classes.BaseDatabaseTable import BaseDatabaseTable
from app.utils.db_utils import db_utils
from app.utils.search_utils import search_utils
import pymysql


class antibodiesTable(BaseDatabaseTable):
    """_summary_

    :param BaseDatabaseTable: _description_
    :type BaseDatabaseTable: _type_
    """   
    @override
    def display(self, Uinputs: str, sort: str, sort_orders: dict) -> dict:
        # Check if sort is in the dictionary, if not then uses default value
    
        order_by = sort_orders.get(sort, 'Target_Name')

        # Validate the order_by to prevent sql injection
        if order_by not in sort_orders.values():
            order_by = 'Target_Name'  

        query = f"SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 ORDER BY {order_by};"


        # Creates Dataframe
        df = db_utils.toDataframe(query,'app/Credentials/CoreC.json')

        SqlData = df
        
        # * Fuzzy Search *
        # Checks whether filters are being used
        # If filters are used then implements fuzzy matching
        if len(Uinputs) != 0:
            columns_to_check = ["Company_name", "Target_Name", "Target_Species"]
            data = search_utils.search_data(Uinputs, columns_to_check, 70, SqlData)
            
            # If no match is found displays empty row
            if not data:
                dataFrame = db_utils.toDataframe("SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 0 AND Catalog_Num = 'N/A' ORDER BY Target_Name;", 'app/Credentials/CoreC.json')
                dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
                data = dataFrame.to_dict('records')
        else: # If no search filters are used
            # renaming columns and setting data variable
            SqlData.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
            # Converts to a list of dictionaries
            data = SqlData.to_dict(orient='records')
        return data

    def add(self, **kwargs) -> None:
        for name, value in kwargs.items():
            if name == 'catalog_num':
                raise NotImplementedError
                     

    def change(self) -> None:
        pass
    
    def delete(self, primary_key) -> None:
        mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreC.json'))
        cursor = mydb.cursor()

        # SQL DELETE query
        query = "DELETE FROM Antibodies_Stock WHERE Stock_ID = %s"

        #Execute SQL query
        cursor.execute(query, (primary_key,))

        # Commit the transaction
        mydb.commit()

        # Close the cursor and connection
        cursor.close()
        mydb.close()
