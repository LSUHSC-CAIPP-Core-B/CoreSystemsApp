import pandas as pd
from flask_login import current_user

from app.abstract_classes.BaseDatabaseTable import BaseDatabaseTable
from app.utils.db_utils import db_utils
from app.utils.search_utils import search_utils

class mouseTable(BaseDatabaseTable):
    """Concrete class
    
    Inherits from abstract class BaseDatabaseTable

    :param BaseDatabaseTable: Abstract Class BaseDatabaseTable
    :type BaseDatabaseTable: type
    """
    
    def display(self, Uinputs: str, sort: str) -> dict:
        # Maps sorting options to their corresponding SQL names
        sort_orders = {
            'Times Back Crossed': 'Times_Back_Crossed',
        }

        # Check if sort is in the dictionary, if not then uses default value
        order_by = sort_orders.get(sort, 'PI_Name')

        # Validate the order_by to prevent sql injection
        if order_by not in sort_orders.values():
            order_by = 'PI_Name'

        query = f"SELECT * FROM Mouse_Stock WHERE Genotype != 'N/A' ORDER BY {order_by};"

        # Creates Dataframe
        SqlData = db_utils.toDataframe(query,'db_config/CoreC.json')
        
        # * Fuzzy Search *
        # Checks whether filters are being used
        # If filters are used then implements fuzzy matching
        if len(Uinputs) != 0:
            columns_to_check = ["PI_Name", "Genotype", "Strain"]
            data = search_utils.sort_searched_data(Uinputs, columns_to_check, 50, SqlData, order_by, columns_rename={'PI_Name': 'PI', 'Mouse_Description': 'Description', 'Times_Back_Crossed': 'Times Back Crossed', 'MTA_Required': 'MTA Required'})
            data = data.to_dict(orient='records')
            # If no match is found displays empty row
            if not data:
                dataFrame = db_utils.toDataframe("SELECT * FROM Mouse_Stock WHERE Genotype = 'N/A';", 'db_config/CoreC.json')
                dataFrame.rename(columns={'PI_Name': 'PI', 'Mouse_Description': 'Description', 'Times_Back_Crossed': 'Times Back Crossed', 'MTA_Required': 'MTA Required'}, inplace=True)
                data = dataFrame.to_dict('records')
        else: # If no search filters are used
            # renaming columns and setting data variable
            SqlData.rename(columns={'PI_Name': 'PI', 'Mouse_Description': 'Description', 'Times_Back_Crossed': 'Times Back Crossed', 'MTA_Required': 'MTA Required'}, inplace=True)
            # Converts to a list of dictionaries
            data = SqlData.to_dict(orient='records')
        return data
    
    def add(self, params: dict) -> pd.DataFrame:
        user_id = current_user.id

        # SQL Add query
        query = f"INSERT INTO Mouse_Stock VALUES (null, %(PI)s, %(Genotype)s, %(Description)s, %(Strain)s, %(Times Back Crossed)s, %(MTA Required)s, {user_id});"
        db_utils.execute(query, 'db_config/CoreC.json', params=params)

        # Gets newest antibody
        query = "SELECT * FROM Mouse_Stock ORDER BY Stock_ID DESC LIMIT 1;"
        
        df = db_utils.toDataframe(query, 'db_config/CoreC.json')
        return df
    
    def change(self, params: dict) -> None:
        # SQL Change query
        query = "UPDATE Mouse_Stock SET PI_Name = %(PI)s, Genotype = %(Genotype)s, Mouse_Description = %(Description)s, Strain = %(Strain)s, Times_Back_Crossed = %(Times Back Crossed)s, MTA_Required = %(MTA Required)s WHERE Stock_ID = %(primaryKey)s;"
        db_utils.execute(query, 'db_config/CoreC.json', params=params)
    
    def delete(self, primary_key) -> None:
        idQuery = f"SELECT user_id FROM Mouse_Stock WHERE Stock_ID = {primary_key}"

        userID = db_utils.toDataframe(idQuery, 'db_config/CoreC.json')
        
        if userID.iloc[0,0] == current_user.id or current_user.is_admin:
            # SQL DELETE query
            query = "DELETE FROM Mouse_Stock WHERE Stock_ID = %s"
            db_utils.execute(query, 'db_config/CoreC.json', params=(primary_key,))
