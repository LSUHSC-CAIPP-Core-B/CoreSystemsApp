from typing import Hashable, Any, Union

import pandas as pd
from app.abstract_classes.BaseDatabaseTable import BaseDatabaseTable
from app.utils.db_utils import db_utils
from app.utils.search_utils import search_utils
from rapidfuzz import process, fuzz


class PI_table(BaseDatabaseTable):
    """Concrete class

    Inherits from abstract class BaseDatabaseTable

    :param BaseDatabaseTable: Abstract Class BaseDatabaseTable
    :type BaseDatabaseTable: type
    """

    def display(self, Uinputs: str, sort: str) -> list[dict[Hashable, Any]]:
        # Maps sorting options to their corresponding SQL names
        sort_orders = {
            "PI full name": "PI full name",
            "PI ID": "PI ID",
            "Department": "Department",
        }
        order_by = sort_orders.get(sort, "Original")

        SqlData = db_utils.toDataframe("Select * FROM pi_info;", "db_config/CoreB.json")

        def build_data(Uinputs) -> pd.DataFrame:
            """Always returns a DataFrame."""
            # No search and no real sort: return as is
            if Uinputs[0] == "" and Uinputs[1] == "" and order_by != "Original":
                return SqlData.sort_values(by=order_by)

            columns_to_check = ["PI full name", "Department"]
            sort_arg = None if order_by == "Original" else order_by

            if Uinputs[0] != "":
                names = db_utils.toDataframe(
                    "SELECT `PI full name` FROM pi_info", "db_config/CoreB.json"
                )
                names[["First Name", "Last Name"]] = names["PI full name"].str.split(
                    "_", expand=True, n=1
                )
                results = search_utils.find_best_fuzzy_match(
                    Uinputs[0], names, threshold=75
                )

                if results:
                    matched_full_name = [r[0] for r in results]
                    filtered_SqlData = SqlData[
                        SqlData["PI full name"].isin(matched_full_name)
                    ].copy()

                    dept_input = Uinputs[1] if len(Uinputs) > 1 else ""
                    data = search_utils.sort_searched_data(
                        ["", dept_input],
                        columns_to_check,
                        80,
                        filtered_SqlData,
                        sort_arg,
                    )
                else:
                    data = SqlData.iloc[0:0].copy()
            else:
                data = search_utils.sort_searched_data(
                    Uinputs, columns_to_check, 80, SqlData, sort_arg
                )

            # No matches: return "N/A" placeholder row as a DataFrame
            if data.empty:
                return db_utils.toDataframe(
                    "Select * FROM pi_info WHERE Department = 'N/A';",
                    "db_config/CoreB.json",
                )
            return data

        # Department search: fuzzy expand and union the results
        if Uinputs[1] != "":
            match = department_match(SqlData, Uinputs[1])

            if match.empty:
                # No department fuzzy-match at all -> return N/A placeholder
                empty = db_utils.toDataframe(
                    "Select * FROM pi_info WHERE Department = 'N/A';",
                    "db_config/CoreB.json",
                )
                return empty.to_dict(orient="records")

            data = pd.DataFrame()
            for i in range(len(match)):
                Uinputs[1] = match.iloc[i, 0]
                data = pd.concat([data, build_data(Uinputs)], ignore_index=True)

            data.drop_duplicates(subset=["index"], inplace=True)

            if order_by != "Original":
                data = data.sort_values(by=order_by)
            return data.to_dict(orient="records")

        # No department search
        return build_data(Uinputs).to_dict(orient="records")

    def change(self, params):
        # SQL Change query
        query = "UPDATE pi_info SET `PI full name` = %(PI_full_name)s, `PI ID` = %(PI_ID)s, email = %(email)s, Department = %(Department)s   WHERE `index` = %(index)s;"
        db_utils.execute(query, "db_config/CoreB.json", params=params)

    def add(self, params):
        # SQL Add query
        query = "INSERT INTO pi_info VALUES (null, %(PI_full_name)s, %(PI_ID)s, %(email)s, %(Department)s);"
        db_utils.execute(query, "db_config/CoreB.json", params=params)

        # Gets newest antibody
        query = "SELECT * FROM pi_info ORDER BY `index` DESC LIMIT 1;"

        df = db_utils.toDataframe(query, "db_config/CoreB.json")
        return df

    def delete(self, primary_key):
        # SQL DELETE query
        query = "DELETE FROM pi_info WHERE `index` = %s"

        db_utils.execute(query, "db_config/CoreB.json", params=(primary_key,))


def department_match(df, value):
    dept_df = pd.DataFrame(df["Department"])
    # Split Department column by multiple delimiters using a regex
    dept_df["Department_List"] = dept_df["Department"].str.split(
        r",\s*|\s+and\s+|\s+", regex=True
    )
    df_exploded = dept_df.explode("Department_List")

    # Fuzzy matching
    choices = df_exploded["Department_List"].unique().tolist()
    results = process.extract(value, choices, scorer=fuzz.WRatio, score_cutoff=85)

    # Get a list of the department names that matched
    matched_departments = [item[0] for item in results]

    # Filter the exploded DataFrame to find the original records
    fuzzy_matched_df = df_exploded[
        df_exploded["Department_List"].isin(matched_departments)
    ]

    # strip dataframe
    df_stripped = fuzzy_matched_df.select_dtypes("object")
    df_stripped["Department"] = df_stripped["Department"].str.strip()

    # drop any duplicates
    final_results = df_stripped.drop_duplicates(subset=["Department"], keep="first")
    return final_results
