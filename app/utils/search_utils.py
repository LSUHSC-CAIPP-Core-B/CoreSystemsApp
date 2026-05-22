from typing import Any, Hashable

import pandas as pd
from rapidfuzz import fuzz, utils


class search_utils:
    """A utility class for performing and sorting fuzzy searches on a DataFrame."""

    @staticmethod
    def search_data(
        Uinputs: list[Any],
        columns_to_check: list[str],
        threshold: int,
        SqlData: pd.DataFrame,
        *,
        columns_rename: dict[str] = None,
    ) -> list[dict[Hashable, Any]]:
        """Performs a fuzzy search on a SQL DataFrame using user inputs and specified columns, returning a dictionary of matching results.

        :param Uinputs: List of user inputs to search for.
        :type Uinputs: list[Any]
        :param columns_to_check: List of columns in the DataFrame to check for matches.
        :type columns_to_check: list[str]
        :param threshold: Minimum similarity score (0-100) required for a match.
        :type threshold: int
        :param SqlData: The DataFrame to be searched.
        :type SqlData: pd.DataFrame
        :param columns_rename: Optional dictionary to rename columns in the results, defaults to None
        :type columns_rename: dict[str], optional
        :return: A dictionary of search results, with each user input corresponding to a list of matching rows.
        :rtype: list[dict[Hashable, Any]]
        """

        matches_per_input: list = [
            set() for _ in Uinputs
        ]  # List of sets, one for each input

        for input_index, i in enumerate(Uinputs):
            for index, row in SqlData.iterrows():
                for column in columns_to_check:
                    if fuzz.ratio(i, row[column]) > threshold:
                        matches_per_input[input_index].add(
                            index
                        )  # Adds row index to the set for this input
                        break  # No need to check other columns for this input

        # Finds the intersection of all sets to ensure each input has at least one matching column in the row
        all_matches = (
            set.intersection(*matches_per_input) if matches_per_input else set()
        )

        if columns_rename is not None:
            SqlData.rename(columns=columns_rename, inplace=True)

        filtered_df = SqlData.loc[list(all_matches)]
        return filtered_df.to_dict(orient="records")

    @staticmethod
    def sort_searched_data(
        Uinputs: list[Any],
        columns_to_check: list[str],
        threshold: int,
        SqlData: pd.DataFrame,
        sort_by: list[str] = None,
        *,
        columns_rename: dict[str] = None,
    ) -> list[dict[Hashable, Any]]:
        """Searches and sorts data from a DataFrame based on user inputs and columns, then returns the sorted data as a dictionary.

        :param Uinputs: List of user inputs to search for in the DataFrame.
        :type Uinputs: list[Any]
        :param columns_to_check: List of columns in the DataFrame to check for matches.
        :type columns_to_check: list[str]
        :param threshold: Minimum similarity score (0-100) required for a match.
        :type threshold: int
        :param SqlData: The DataFrame to be searched.
        :type SqlData: pd.DataFrame
        :param sort_by: List of column names to sort the search results by after searching.
        :type sort_by: list[str]
        :param columns_rename: Optional dictionary to rename columns in the DataFrame, defaults to None
        :type columns_rename: dict[str], optional
        :return: A dictionary of sorted search results.
        :rtype: list[dict[Hashable, Any]]
        """

        result = any(s for s in Uinputs)
        # Checks if inputs are used
        # If inputs are used then search the df for a match
        # Then sort according to fuzz ratio
        if result:
            condition = False

            # Iterate over each column and its corresponding user input
            for i, v in enumerate(columns_to_check):
                SqlData[v] = SqlData[v].astype(str)

                SqlData[f"{v}_ratio"] = SqlData.apply(
                    lambda x: round(
                        fuzz.ratio(
                            utils.default_process(x[v]),
                            utils.default_process(Uinputs[i]),
                        ),
                        2,
                    ),
                    axis=1,
                )  # Create the ratio column

            # Store Ratio column names
            rCol = [f"{i}_ratio" for i in columns_to_check]

            # Update the condition to include any ratio column exceeding the threshold
            condition = (SqlData[rCol] > threshold).any(axis=1)

            # filtered dataframe
            df = SqlData[condition]

            # Creating list for ascending/descending
            asc = [False for i in rCol]
            # adding sort_by column
            rCol.append(sort_by)
            asc.append(True)  # adds sort order for sort_by column

            if sort_by == "Request Date":
                df.sort_values(by=rCol, ascending=False, inplace=True)
            elif sort_by == "Not Sorted" or sort_by is None:
                df
            else:
                df.sort_values(by=rCol, ascending=asc, inplace=True)

            # Drop ratio columns
            SqlData = df.drop(columns=rCol[0 : len(rCol) - 1])
        else:  # inputs not used
            if sort_by == "Request Date":
                SqlData.sort_values(by=[sort_by], ascending=False, inplace=True)
            elif sort_by == "Not Sorted":
                SqlData.sort_values(by=["Request Date"], ascending=True, inplace=True)
            elif sort_by is None:
                SqlData
            else:
                SqlData.sort_values(by=[sort_by], inplace=True)

        # Rename columns
        if columns_rename is not None:
            SqlData.rename(columns=columns_rename, inplace=True)

        return SqlData

    @staticmethod
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
        matches = []

        for _, row in dataframe.iterrows():
            full_name = str(row["PI full name"]).replace("_", " ")

            score = fuzz.token_set_ratio(
                search_term,
                full_name,
                processor=utils.default_process,  # lowercases, strips, normalizes punctuation
            )

            if score >= threshold:
                matches.append((row["PI full name"], score, row))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
