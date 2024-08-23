from rapidfuzz import fuzz, utils
import pandas as pd

class search_utils:
    """A utility class for performing and sorting fuzzy searches on a DataFrame.
    """

    @staticmethod
    def search_data(Uinputs:list, columns_to_check:list, threshold:int, SqlData: pd.DataFrame, *, columns_rename:dict=None) -> dict:
        """Performs a fuzzy search on a SQL DataFrame using user inputs and specified columns, returning a dictionary of matching results.

        :param Uinputs: List of user inputs to search for.
        :type Uinputs: list
        :param columns_to_check: List of columns in the DataFrame to check for matches.
        :type columns_to_check: list
        :param threshold: Minimum similarity score (0-100) required for a match.
        :type threshold: int
        :param SqlData: The DataFrame to be searched.
        :type SqlData: pd.DataFrame
        :param columns_rename: Optional dictionary to rename columns in the results, defaults to None
        :type columns_rename: dict, optional
        :return: A dictionary of search results, with each user input corresponding to a list of matching rows.
        :rtype: dict
        """

        matches_per_input: list = [set() for _ in Uinputs]  # List of sets, one for each input

        for input_index, i in enumerate(Uinputs):
            for index, row in SqlData.iterrows():
                for column in columns_to_check:
                    if fuzz.ratio(i, row[column]) > threshold:
                        matches_per_input[input_index].add(index)  # Adds row index to the set for this input
                        break  # No need to check other columns for this input

        # Finds the intersection of all sets to ensure each input has at least one matching column in the row
        all_matches = set.intersection(*matches_per_input) if matches_per_input else set()
        
        if columns_rename != None:
            SqlData.rename(columns=columns_rename, inplace=True)
        
        filtered_df = SqlData.loc[list(all_matches)]
        return filtered_df.to_dict(orient='records')
    
    @staticmethod
    def sort_searched_data(Uinputs:list, columns_to_check:list, threshold:int, SqlData: pd.DataFrame, sort_by:list, *, columns_rename:dict=None) -> dict:
        """Searches and sorts data from a DataFrame based on user inputs and columns, then returns the sorted data as a dictionary.

        :param Uinputs: List of user inputs to search for in the DataFrame.
        :type Uinputs: list
        :param columns_to_check: List of columns in the DataFrame to check for matches.
        :type columns_to_check: list
        :param threshold: Minimum similarity score (0-100) required for a match.
        :type threshold: int
        :param SqlData: The DataFrame to be searched.
        :type SqlData: pd.DataFrame
        :param sort_by: List of column names to sort the search results by after searching.
        :type sort_by: list
        :param columns_rename: Optional dictionary to rename columns in the DataFrame, defaults to None
        :type columns_rename: dict, optional
        :return: A dictionary of sorted search results.
        :rtype: dict
        """
        
        result = any(s for s in Uinputs)
        # Checks if inputs are used
        # If inputs are used then search the df for a match
        # Then sort according to fuzz ratio
        if result:
            condition = False

            # Iterate over each column and its corresponding user input
            for i, v in enumerate(columns_to_check):
                SqlData[f'{v}_ratio'] = SqlData.apply(
                    lambda x: round(fuzz.ratio(utils.default_process(x[v]), utils.default_process(Uinputs[i])), 2), axis=1
                ) # Create the ratio column

            # Store Ratio column names
            rCol = [f'{i}_ratio' for i in columns_to_check]

            # Update the condition to include any ratio column exceeding the threshold
            condition = (SqlData[rCol] > threshold).any(axis=1)

            # filtered dataframe
            df = SqlData[condition]

            # Creating list for ascending/descending
            asc = [False for i in rCol]
            # adding sort_by column
            rCol.append(sort_by)
            asc.append(True) # adds sort order for sort_by column
            df = df.sort_values(by=rCol, ascending=asc)
            # Drop ratio columns
            df = df.drop(columns=rCol[0:len(rCol)-1])
            SqlData = df
        else: # inputs not used
            SqlData = SqlData.sort_values(by=[sort_by])

        # Rename columns
        if columns_rename != None:
            SqlData.rename(columns=columns_rename, inplace=True)

        return SqlData.to_dict(orient='records')