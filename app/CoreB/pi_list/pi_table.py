from typing import Hashable, Any, Union

import pandas as pd
from app.abstract_classes.BaseDatabaseTable import BaseDatabaseTable
from app.utils.db_utils import db_utils
from app.utils.search_utils import search_utils
from rapidfuzz import process, fuzz

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
        order_by = sort_orders.get(sort, 'Original')

        query = "Select * FROM pi_info;"

        # Creates Dataframe
        SqlData = db_utils.toDataframe(query,'db_config/CoreB.json')

        def build_data(Uinputs) -> Union[pd.DataFrame, list[dict[Hashable, Any]]]:
            '''
            * Fuzzy Search
            * Checks whether filters are being used
            * If filters are used then implements fuzzy matching
            '''

            if Uinputs[0] != '' or Uinputs[1] != '' or order_by == 'Original':
                columns_to_check = ["PI full name", "Department"]
                
                if order_by == 'Original':
                    if Uinputs[0] != '':
                        names = db_utils.toDataframe('SELECT `PI full name` FROM pi_info','db_config/CoreB.json')

                        # Create dataframe with PI full name, First Name and Last Name
                        names[['First Name', 'Last Name']] = names['PI full name'].str.split('_', expand=True, n=1)
                        results = search_utils.find_best_fuzzy_match(Uinputs[0], names, threshold=75) # Adjust threshold as needed

                        # If a match on first, last name or both is found
                        if results:
                            Uinputs[0] = results[0][0]
                        else:
                            Uinputs[0] = "N/A"

                        data = search_utils.sort_searched_data(Uinputs, columns_to_check, 80, SqlData)
                        data.to_dict(orient='records')
                    else: #If dept is searched for
                        data = search_utils.sort_searched_data(Uinputs, columns_to_check, 80, SqlData)
                else:
                    names = db_utils.toDataframe('SELECT `PI full name` FROM pi_info','db_config/CoreB.json')

                    # Create dataframe with PI full name, First Name and Last Name
                    names[['First Name', 'Last Name']] = names['PI full name'].str.split('_', expand=True, n=1)
                    results = search_utils.find_best_fuzzy_match(Uinputs[0], names, threshold=75) # Adjust threshold as needed

                    # If a match on first, last name or both is found
                    if results:
                        Uinputs[0] = results[0][0]
                    else:
                        Uinputs[0] = "N/A"
                    data = search_utils.sort_searched_data(Uinputs, columns_to_check, 80, SqlData, order_by)
                
                # If no match is found displays empty row
                if data.empty:
                    dataFrame = db_utils.toDataframe("Select * FROM pi_info WHERE Department = 'N/A';", 'db_configCoreB.json')
                    data = dataFrame.to_dict(orient='records')
                    return data
                else:
                    if Uinputs[1] == '': #If dept is searched for
                        data = data.to_dict(orient='records')
                        return data
                    else:
                        return data
            else: # If no search filters are used
                # Converts to a list of dictionaries
                data = SqlData.sort_values(by='Department').to_dict(orient='records')
                return data

        data = pd.DataFrame()
        # match department
        if Uinputs[1] != '':
            match = department_match(SqlData, Uinputs[1])

            if not match.empty:
                for i in range(len(match)):
                    Uinputs[1] = match.iloc[i,0]
                    data = pd.concat([data, build_data(Uinputs)], ignore_index=True)
                if order_by == "Original":
                    data = data.to_dict(orient='records')
                else:
                    data = data.sort_values(by=order_by).to_dict(orient='records')
        else:
            data = build_data(Uinputs)

        return data
    
    def change(self, params):
        # SQL Change query
        query = "UPDATE pi_info SET `PI full name` = %(PI_full_name)s, `PI ID` = %(PI_ID)s, email = %(email)s, Department = %(Department)s   WHERE `index` = %(index)s;"
        db_utils.execute(query, 'db_config/CoreB.json', params=params)
    
    def add(self, params):
        # SQL Add query
        query = "INSERT INTO pi_info VALUES (null, %(PI_full_name)s, %(PI_ID)s, %(email)s, %(Department)s);"
        db_utils.execute(query, 'db_config/CoreB.json', params=params)

        # Gets newest antibody
        query = f"SELECT * FROM pi_info ORDER BY `index` DESC LIMIT 1;"
        
        df = db_utils.toDataframe(query, 'db_config/CoreB.json')
        return df
    
    def delete(self, primary_key):
        # SQL DELETE query
        query = "DELETE FROM pi_info WHERE `index` = %s"

        db_utils.execute(query, 'db_config/CoreB.json', params=(primary_key,))

def department_match(df, value):
    dept_df = pd.DataFrame(df['Department'])
    # Split Department column by multiple delimiters using a regex
    dept_df['Department_List'] = dept_df['Department'].str.split(r',\s*|\s+and\s+|\s+', regex=True)
    df_exploded = dept_df.explode('Department_List')

    # Fuzzy matching
    choices = df_exploded['Department_List'].unique().tolist()
    results = process.extract(value, choices, scorer=fuzz.WRatio, score_cutoff=85)

    # Get a list of the department names that matched
    matched_departments = [item[0] for item in results]

    # Filter the exploded DataFrame to find the original records
    fuzzy_matched_df = df_exploded[df_exploded['Department_List'].isin(matched_departments)]

    # strip dataframe
    df_stripped = fuzzy_matched_df.select_dtypes('object')
    df_stripped['Department'] = df_stripped['Department'].str.strip()

    # drop any duplicates
    final_results = df_stripped.drop_duplicates(subset=['Department'], keep='first')
    return final_results