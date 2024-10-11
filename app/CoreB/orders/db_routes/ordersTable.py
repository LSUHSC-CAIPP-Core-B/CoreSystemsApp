from typing import IO
from app.abstract_classes.BaseDatabaseTable import BaseDatabaseTable
from app.utils.db_utils import db_utils
from app.utils.search_utils import search_utils

class ordersTable(BaseDatabaseTable):
    """ Concrete class
    
    Inherits from abstract class BaseDatabaseTable

    :param BaseDatabaseTable: Abstract Class BaseDatabaseTable
    :type BaseDatabaseTable: type
    """

    
    def display(self, Uinputs: str, sort: str) -> dict:
        # Maps sorting options to their corresponding SQL names
        sort_orders = {
            'Request Date': 'Request Date',
            'PI Name': 'PI Name',
            'Project ID': 'Project ID',
            'Responsible Person': 'Reponsible Person'
        }

        # Check if sort is in the dictionary, if not then uses default value
        order_by = sort_orders.get(sort, 'Not Sorted')

        if order_by == 'Not Sorted':
            print(f"order_by = {order_by}")
            query = "Select * FROM CoreB_Order;"
        else:
            print(f"Else\norder_by = {order_by}")
            query = f"Select * FROM CoreB_Order ORDER BY '{order_by}';"
        # Creates Dataframe
        SqlData = db_utils.toDataframe(query,'app/Credentials/CoreB.json')
        print(f"Dataframe:\n{SqlData}")

        # * Fuzzy Search *
        # Checks whether filters are being used
        # If filters are used then implements fuzzy matching
        if len(Uinputs) != 0:
            columns_to_check = ["service_type", "pi_name"]
            data = search_utils.sort_searched_data(Uinputs, columns_to_check, 50, SqlData, order_by)
            
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
    
    def add(self, params: dict) -> None:
        return super().add(params)
    
    def change(self, params: dict) -> None:
        return super().change(params)

    def delete(self, primary_key) -> None:
        return super().delete(primary_key)