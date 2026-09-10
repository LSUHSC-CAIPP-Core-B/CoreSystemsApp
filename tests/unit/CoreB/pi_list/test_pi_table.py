from unittest.mock import patch

import pandas as pd
import pytest

from app.CoreB.pi_list.pi_table import PI_table, department_match

MODULE = "app.CoreB.pi_list.pi_table"


def _base_pi_df() -> pd.DataFrame:
    """Mirrors the shape of a `Select * FROM pi_info;` result."""
    return pd.DataFrame(
        [
            {
                "index": 1,
                "PI full name": "John_Smith",
                "PI ID": "P001",
                "email": "john@example.com",
                "Department": "Biology",
            },
            {
                "index": 2,
                "PI full name": "Jane_Doe",
                "PI ID": "P002",
                "email": "jane@example.com",
                "Department": "Chemistry",
            },
            {
                "index": 3,
                "PI full name": "Bob_Jones",
                "PI ID": "P003",
                "email": "bob@example.com",
                "Department": "Biology",
            },
            {
                "index": 4,
                "PI full name": "Alice_Williams",
                "PI ID": "P004",
                "email": "alice@example.com",
                "Department": "Physics",
            },
        ]
    )


def _na_placeholder_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "index": 999,
                "PI full name": "N/A",
                "PI ID": "N/A",
                "email": "N/A",
                "Department": "N/A",
            }
        ]
    )


def _last_row_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "index": 5,
                "PI full name": "New_PI",
                "PI ID": "P005",
                "email": "new@example.com",
                "Department": "Biology",
            }
        ]
    )


def _fake_toDataframe(query: str, path: str, *, params=None) -> pd.DataFrame:
    assert path == "db_config/CoreB.json"
    if "Department = 'N/A'" in query:
        return _na_placeholder_df().copy()
    if query.strip() == "SELECT `PI full name` FROM pi_info":
        return _base_pi_df()[["PI full name"]].copy()
    if "ORDER BY `index` DESC LIMIT 1" in query:
        return _last_row_df().copy()
    if query.strip() == "Select * FROM pi_info;":
        return _base_pi_df().copy()
    raise AssertionError(f"Unexpected query: {query}")


@pytest.fixture
def mock_db_utils():
    with patch(f"{MODULE}.db_utils") as mock:
        mock.toDataframe.side_effect = _fake_toDataframe
        yield mock


@pytest.fixture
def pi_table():
    return PI_table()


# ============================================================================
# display() - no search / sorting only
# ============================================================================
class TestDisplayNoSearch:
    def test_no_search_no_sort_returns_all_rows(self, pi_table, mock_db_utils):
        result = pi_table.display(["", ""], sort="")
        assert len(result) == 4
        names = {row["PI full name"] for row in result}
        assert names == {"John_Smith", "Jane_Doe", "Bob_Jones", "Alice_Williams"}

    def test_sort_by_pi_full_name_orders_alphabetically(self, pi_table, mock_db_utils):
        result = pi_table.display(["", ""], sort="PI full name")
        names = [row["PI full name"] for row in result]
        assert names == sorted(names)

    def test_unrecognized_sort_falls_back_to_original(self, pi_table, mock_db_utils):
        result = pi_table.display(["", ""], sort="not a real sort option")
        assert len(result) == 4


# ============================================================================
# display() - PI name fuzzy search
# ============================================================================
class TestDisplayNameSearch:
    def test_matching_name_returns_only_that_pi(self, pi_table, mock_db_utils):
        result = pi_table.display(["John Smith", ""], sort="")
        assert len(result) == 1
        assert result[0]["PI full name"] == "John_Smith"

    def test_no_fuzzy_match_returns_na_placeholder(self, pi_table, mock_db_utils):
        result = pi_table.display(["Zzqx Plmk", ""], sort="")
        assert len(result) == 1
        assert result[0]["Department"] == "N/A"


# ============================================================================
# display() - Department fuzzy search
# ============================================================================
class TestDisplayDepartmentSearch:
    def test_matching_department_returns_matching_pis(self, pi_table, mock_db_utils):
        result = pi_table.display(["", "Biology"], sort="")
        names = {row["PI full name"] for row in result}
        assert names == {"John_Smith", "Bob_Jones"}

    def test_no_department_match_returns_na_placeholder(self, pi_table, mock_db_utils):
        result = pi_table.display(["", "Nonexistent Dept Zzqx"], sort="")
        assert len(result) == 1
        assert result[0]["Department"] == "N/A"

    def test_department_search_respects_sort(self, pi_table, mock_db_utils):
        result = pi_table.display(["", "Biology"], sort="PI full name")
        names = [row["PI full name"] for row in result]
        assert names == sorted(names)


# ============================================================================
# change() / add() / delete()
# ============================================================================
class TestMutations:
    def test_change_executes_update_with_given_params(self, pi_table, mock_db_utils):
        params = {
            "PI_full_name": "John_Smith",
            "PI_ID": "P001",
            "email": "john@example.com",
            "Department": "Biology",
            "index": 1,
        }
        pi_table.change(params)

        mock_db_utils.execute.assert_called_once()
        args, kwargs = mock_db_utils.execute.call_args
        assert "UPDATE pi_info SET" in args[0]
        assert args[1] == "db_config/CoreB.json"
        assert kwargs["params"] == params

    def test_add_inserts_then_returns_newest_row(self, pi_table, mock_db_utils):
        params = {
            "PI_full_name": "New_PI",
            "PI_ID": "P005",
            "email": "new@example.com",
            "Department": "Biology",
        }
        result = pi_table.add(params)

        mock_db_utils.execute.assert_called_once()
        exec_args, exec_kwargs = mock_db_utils.execute.call_args
        assert "INSERT INTO pi_info VALUES" in exec_args[0]
        assert exec_kwargs["params"] == params

        mock_db_utils.toDataframe.assert_called_once()
        query_arg = mock_db_utils.toDataframe.call_args[0][0]
        assert "ORDER BY `index` DESC LIMIT 1" in query_arg

        assert isinstance(result, pd.DataFrame)
        assert result.iloc[0]["PI full name"] == "New_PI"

    def test_delete_executes_delete_with_primary_key(self, pi_table, mock_db_utils):
        pi_table.delete(42)

        mock_db_utils.execute.assert_called_once()
        args, kwargs = mock_db_utils.execute.call_args
        assert "DELETE FROM pi_info WHERE `index` = %s" in args[0]
        assert args[1] == "db_config/CoreB.json"
        assert kwargs["params"] == (42,)


# ============================================================================
# department_match()
# ============================================================================
class TestDepartmentMatch:
    def test_exact_match_scores_highest_and_first(self):
        df = pd.DataFrame({"Department": ["Biology", "Biol", "Neuroscience"]})
        result = department_match(df, "Biology", threshold=0)
        assert result["Department"].tolist() == ["Biology", "Biol", "Neuroscience"]

    def test_dedupes_repeated_department_values(self):
        df = pd.DataFrame(
            {"Department": ["Biology", "Biology", "Biology", "Chemistry"]}
        )
        result = department_match(df, "Biology", threshold=50)
        assert result["Department"].tolist() == ["Biology"]

    def test_ignores_blank_and_nan_departments(self):
        df = pd.DataFrame({"Department": ["Biology", None, "", "   "]})
        result = department_match(df, "Biology")
        assert result["Department"].tolist() == ["Biology"]

    def test_no_match_returns_empty_dataframe(self):
        df = pd.DataFrame({"Department": ["Biology", "Chemistry", "Physics"]})
        result = department_match(df, "Zzqx Plmk", threshold=50)
        assert result.empty
        assert list(result.columns) == ["Department"]

    def test_threshold_filters_out_weak_matches(self):
        df = pd.DataFrame({"Department": ["Biology", "Neuroscience"]})
        loose = department_match(df, "Neurosci", threshold=50)
        strict = department_match(df, "Neurosci", threshold=95)
        assert "Neuroscience" in loose["Department"].tolist()
        assert strict.empty
