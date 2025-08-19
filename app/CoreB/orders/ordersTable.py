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

                names[['First Name', 'Last Name']] = names['PI full name'].str.split('_', expand=True, n=1)
                results = find_best_fuzzy_match(Uinputs[0], names, threshold=75) # Adjust threshold as needed

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
    
def find_best_fuzzy_match(search_term, dataframe, threshold=70):
    """Performs a fuzzy search on a SQL DataFrame using user input and specified columns,
    returns a dictionary of matching results.

    :param user_input: The user input to search for (a single name).
    :type user_input: str
    :param dataframe: The DataFrame to be searched.
    :type dataframe: pd.DataFrame
    :param columns_to_check: List of columns in the DataFrame to check for matches.
    :type columns_to_check: list[str]
    :param threshold: Minimum similarity score (0-100) required for a match, defaults to 70.
    :type threshold: int
    :return: A list of dictionaries, where each dictionary represents a matching row.
             Each dictionary will contain the original row data, the best score,
             and the column that provided the best match.
    :rtype: list[dict[Hashable, Any]]
    """
    matches_per_row = []

    for _, row in dataframe.iterrows():

        row_choices = [
            (row['First Name'], 'First Name'), 
            (row['Last Name'], 'Last Name'),   
            (row['PI full name'], 'PI full name') 
        ]

        best_score_for_row = 0
        best_matched_column = None

        for choice_str, column_name in row_choices:
            normalized_search_term = search_term.lower().strip()
            normalized_choice_str = str(choice_str).lower().strip()

            score = fuzz.token_set_ratio(normalized_search_term, normalized_choice_str)

            if score > best_score_for_row:
                best_score_for_row = score
                best_matched_column = column_name

        if best_score_for_row >= threshold:
            matches_per_row.append(
                (row['PI full name'], best_score_for_row, best_matched_column, row)
            )

    matches_per_row.sort(key=lambda x: x[1], reverse=True) # Sort by score (index 1 in tuple)

    return matches_per_row