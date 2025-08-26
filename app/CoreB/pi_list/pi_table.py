from typing import IO, Hashable, Any

import pandas as pd
import pymysql
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
        SqlData = db_utils.toDataframe(query,'app/Credentials/CoreB.json')

        # match department
        if Uinputs[1]:
            match = department_match(SqlData, Uinputs[1])

            if not match.empty:
                Uinputs[1] = match.iloc[0,0]

        # * Fuzzy Search *
        # Checks whether filters are being used
        # If filters are used then implements fuzzy matching
        if len(Uinputs) != 0:
            columns_to_check = ["PI full name", "Department"]
            
            if order_by == 'Original':
                if Uinputs[0] != '':
                    names = db_utils.toDataframe('SELECT `PI full name` FROM pi_info','app/Credentials/CoreB.json')

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
                else:
                    data = search_utils.sort_searched_data(Uinputs, columns_to_check, 80, SqlData)
                    data.to_dict(orient='records')
            else:
                if Uinputs[0] != '':
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
                data.to_dict(orient='records')
            
            # If no match is found displays empty row
            if data.empty:
                dataFrame = db_utils.toDataframe("Select * FROM pi_info WHERE Department = 'N/A';", 'app/Credentials/CoreB.json')
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
        mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreB.json'))
        cursor = mydb.cursor()

        # SQL Add query
        query = "INSERT INTO pi_info VALUES (null, %(PI_full_name)s, %(PI_ID)s, %(email)s, %(Department)s);"
        #Execute SQL query
        cursor.execute(query, params)

        # Commit the transaction
        mydb.commit()

        # Close the cursor and connection
        cursor.close()
        mydb.close()   

        # Gets newest antibody
        query = f"SELECT * FROM pi_info ORDER BY `index` DESC LIMIT 1;"
        
        df = db_utils.toDataframe(query, 'app/Credentials/CoreB.json')
        return df
    
    def delete(self, primary_key):
        mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreB.json'))
        cursor = mydb.cursor()

        # SQL DELETE query
        query = "DELETE FROM pi_info WHERE `index` = %s"

        #Execute SQL query
        cursor.execute(query, (primary_key,))

        # Commit the transaction
        mydb.commit()

        # Close the cursor and connection
        cursor.close()
        mydb.close()

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