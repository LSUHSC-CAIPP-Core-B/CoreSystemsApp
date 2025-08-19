from typing import IO
from app.abstract_classes.BaseDatabaseTable import BaseDatabaseTable
from app.utils.db_utils import db_utils
from app.utils.search_utils import search_utils
from flask import flash
import pandas as pd
from rapidfuzz import process, fuzz

class ordersTable(BaseDatabaseTable):
    """ Concrete class
    
    Inherits from abstract class BaseDatabaseTable

    :param BaseDatabaseTable: Abstract Class BaseDatabaseTable
    :type BaseDatabaseTable: type
    """

    def display(self, Uinputs: str, sort: str,  service_type: str) -> dict:
        # Maps sorting options to their corresponding SQL names
        sort_orders = {
            'Request Date': 'Request Date',
            'PI Name': 'PI Name',
            'Project ID': 'Project ID',
            'Responsible Person': 'Responsible Person'
        }

        # Check if sort is in the dictionary, if not then uses default value
        order_by = sort_orders.get(sort, 'Not Sorted')

        sort_service_type = {
            'RNA-Seq analysis' : 'RNA',
            'DNA-Seq analysis' : 'DNA',
            'Protein analysis' : 'Protein',
            'Metabolite analysis' : 'Metabolite',
            'Proteomics analysis' : 'Proteomics',
            'BioRender license' : 'BioRender'
        }

        service_order_by = sort_service_type.get(service_type, 'DNA')

        query = "Select * FROM CoreB_Order;"

        # Creates Dataframe
        SqlData = db_utils.toDataframe(query,'app/Credentials/CoreB.json')

        # * Fuzzy Search *
        # Checks whether filters are being used
        # If filters are used then implements fuzzy matching
        if len(Uinputs) != 0:
            columns_to_check = ["PI Name", "Project ID"]
            # If the Project ID field is used then exact search
            if Uinputs[1] != '' and Uinputs[0] == '':
                data = search_utils.sort_searched_data(Uinputs, columns_to_check, 99, SqlData, order_by)
            elif Uinputs[0] != '': # threshold 50 for fuzz search
                names = db_utils.toDataframe('SELECT `PI full name` FROM pi_info','app/Credentials/CoreB.json')

                # Create dataframe with PI full name, First Name and Last Name
                names[['First Name', 'Last Name']] = names['PI full name'].str.split('_', expand=True, n=1)
                results = search_utils.find_best_fuzzy_match(Uinputs[0], names, threshold=75) # Adjust threshold as needed

                # If a match on first, last name or both is found
                if results:
                    Uinputs[0] = results[0][0]
                else:
                    Uinputs[0] = "N/A"
                data = search_utils.sort_searched_data(Uinputs, columns_to_check, 80, SqlData, order_by)
            else:
                data = search_utils.sort_searched_data(Uinputs, columns_to_check, 50, SqlData, order_by)
                
                # If no match is found displays empty row
                if not data:
                    dataFrame = db_utils.toDataframe("Select * FROM CoreB_Order WHERE `Project ID` = 'N/A';", 'app/Credentials/CoreB.json')
                    data = dataFrame.to_dict('records')
        else: # If no search filters are used
            # Converts to a list of dictionaries
            data = SqlData.to_dict(orient='records')
        return data
    
    def change(self, params: dict) -> None:
        return super().change(params)
    
    def add(self, params: dict) -> None:
        return super().add(params)

    def delete(self, primary_key) -> None:
        return super().delete(primary_key)