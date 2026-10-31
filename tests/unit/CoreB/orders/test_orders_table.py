from unittest.mock import patch

import pandas as pd
import pytest

from app.CoreB.orders.ordersTable import ordersTable

MODULE = "app.CoreB.orders.ordersTable"

ORDERS_QUERY = "Select * FROM CoreB_Order;"
PI_NAMES_QUERY = "SELECT `PI full name` FROM pi_info"
NA_QUERY = "Select * FROM CoreB_Order WHERE `Project ID` = 'N/A';"


def _base_orders_df() -> pd.DataFrame:
    """Mirrors the shape of a `Select * FROM CoreB_Order;` result."""
    return pd.DataFrame(
        [
            {
                "index": 1,
                "PI Name": "John_Smith",
                "Project ID": "CB-001",
                "Request Date": "2024-03-01",
                "Responsible Person": "Carol",
                "Service Type": "RNA-Seq analysis",
            },
            {
                "index": 2,
                "PI Name": "   Jane_Doe",
                "Project ID": "CB-002",
                "Request Date": "2024-01-15",
                "Responsible Person": "Alice",
                "Service Type": "Protein analysis",
            },
            {
                "index": 3,
                "PI Name": "John_Smith",
                "Project ID": "CB-003",
                "Request Date": "2024-02-10",
                "Responsible Person": "Bob",
                "Service Type": "Protein analysis",
            },
            {
                "index": 4,
                "PI Name": "Bob_Jones",
                "Project ID": "",
                "Request Date": "2024-04-20",
                "Responsible Person": "Dave",
                "Service Type": "DNA-Seq analysis",
            },
        ]
    )


def _pi_names_df() -> pd.DataFrame:
    return pd.DataFrame({"PI full name": ["John_Smith", "Jane_Doe", "Bob_Jones"]})


def _na_placeholder_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "index": 999,
                "PI Name": "N/A",
                "Project ID": "N/A",
                "Request Date": "N/A",
                "Responsible Person": "N/A",
                "Service Type": "N/A",
            }
        ]
    )


def _make_fake_toDataframe(orders_df: pd.DataFrame):
    def _fake(query: str, path: str, *, params=None) -> pd.DataFrame:
        assert path == "db_config/CoreB.json"
        if query.strip() == ORDERS_QUERY:
            return orders_df.copy()
        if query.strip() == PI_NAMES_QUERY:
            return _pi_names_df()
        if query.strip() == NA_QUERY:
            return _na_placeholder_df()
        raise AssertionError(f"Unexpected query: {query}")

    return _fake


@pytest.fixture
def mock_db_utils():
    with patch(f"{MODULE}.db_utils") as mock:
        mock.toDataframe.side_effect = _make_fake_toDataframe(_base_orders_df())
        yield mock


@pytest.fixture
def orders_table():
    return ordersTable()


def _ids(result: list[dict]) -> list[str]:
    return [row["Project ID"] for row in result]


# ============================================================================
# display() - no search / sorting only
# ============================================================================
class TestDisplayNoSearch:
    def test_empty_inputs_returns_all_rows(self, orders_table, mock_db_utils):
        result = orders_table.display(["", ""], sort="", service_type="")
        assert sorted(_ids(result)) == ["", "CB-001", "CB-002", "CB-003"]

    def test_queries_orders_table(self, orders_table, mock_db_utils):
        orders_table.display(["", ""], sort="", service_type="")
        mock_db_utils.toDataframe.assert_any_call(ORDERS_QUERY, "db_config/CoreB.json")

    def test_strips_leading_whitespace(self, orders_table, mock_db_utils):
        result = orders_table.display(["", ""], sort="", service_type="")
        names = {row["PI Name"] for row in result}
        assert "Jane_Doe" in names
        assert "   Jane_Doe" not in names

    def test_unknown_sort_defaults_to_request_date_ascending(
        self, orders_table, mock_db_utils
    ):
        result = orders_table.display(["", ""], sort="bogus", service_type="")
        dates = [row["Request Date"] for row in result]
        assert dates == sorted(dates)

    def test_sort_by_request_date_is_descending(self, orders_table, mock_db_utils):
        result = orders_table.display(["", ""], sort="Request Date", service_type="")
        dates = [row["Request Date"] for row in result]
        assert dates == sorted(dates, reverse=True)

    @pytest.mark.parametrize("column", ["PI Name", "Project ID", "Responsible Person"])
    def test_sort_by_column_is_ascending(self, orders_table, mock_db_utils, column):
        result = orders_table.display(["", ""], sort=column, service_type="")
        values = [row[column] for row in result]
        assert values == sorted(values)

    def test_empty_input_list_skips_search(self, orders_table, mock_db_utils):
        result = orders_table.display([], sort="Request Date", service_type="")
        assert _ids(result) == ["CB-001", "CB-002", "CB-003", ""]
        mock_db_utils.toDataframe.assert_called_once()

    def test_empty_table_returns_na_placeholder(self, orders_table):
        empty = _base_orders_df().iloc[0:0]
        with patch(f"{MODULE}.db_utils") as mock:
            mock.toDataframe.side_effect = _make_fake_toDataframe(empty)
            result = orders_table.display(["", ""], sort="", service_type="")
        assert _ids(result) == ["N/A"]


# ============================================================================
# display() - Project ID exact search
# ============================================================================
class TestDisplayProjectIdSearch:
    def test_exact_project_id_returns_only_that_order(
        self, orders_table, mock_db_utils
    ):
        result = orders_table.display(["", "CB-002"], sort="", service_type="")
        assert _ids(result) == ["CB-002"]

    def test_project_id_search_is_case_insensitive(self, orders_table, mock_db_utils):
        result = orders_table.display(["", "cb-002"], sort="", service_type="")
        assert _ids(result) == ["CB-002"]

    def test_partial_project_id_does_not_match(self, orders_table, mock_db_utils):
        result = orders_table.display(["", "CB-00"], sort="", service_type="")
        assert result == []

    def test_project_id_search_skips_pi_lookup(self, orders_table, mock_db_utils):
        orders_table.display(["", "CB-002"], sort="", service_type="")
        mock_db_utils.toDataframe.assert_called_once()


# ============================================================================
# display() - PI name fuzzy search
# ============================================================================
class TestDisplayNameSearch:
    def test_matching_name_returns_that_pis_orders(self, orders_table, mock_db_utils):
        result = orders_table.display(["John Smith", ""], sort="", service_type="")
        assert sorted(_ids(result)) == ["CB-001", "CB-003"]

    def test_misspelled_name_still_matches(self, orders_table, mock_db_utils):
        result = orders_table.display(["Jon Smth", ""], sort="", service_type="")
        assert sorted(_ids(result)) == ["CB-001", "CB-003"]

    def test_name_search_looks_up_pi_names(self, orders_table, mock_db_utils):
        orders_table.display(["John Smith", ""], sort="", service_type="")
        mock_db_utils.toDataframe.assert_any_call(
            PI_NAMES_QUERY, "db_config/CoreB.json"
        )

    def test_unmatched_name_returns_no_rows(self, orders_table, mock_db_utils):
        result = orders_table.display(["Zzqx Plmk", ""], sort="", service_type="")
        assert result == []

    def test_name_search_respects_request_date_sort(
        self, orders_table, mock_db_utils
    ):
        result = orders_table.display(
            ["John Smith", ""], sort="Request Date", service_type=""
        )
        assert _ids(result) == ["CB-001", "CB-003"]


# ============================================================================
# display() - service type filter
# ============================================================================
class TestDisplayServiceFilter:
    def test_filters_by_service_type(self, orders_table, mock_db_utils):
        result = orders_table.display(
            ["", ""], sort="", service_type="Protein analysis"
        )
        assert sorted(_ids(result)) == ["CB-002", "CB-003"]

    def test_unknown_service_type_returns_all(self, orders_table, mock_db_utils):
        result = orders_table.display(["", ""], sort="", service_type="bogus")
        assert len(result) == 4

    def test_known_service_with_no_orders_returns_empty(
        self, orders_table, mock_db_utils
    ):
        result = orders_table.display(
            ["", ""], sort="", service_type="BioRender license"
        )
        assert result == []

    def test_service_filter_combines_with_name_search(
        self, orders_table, mock_db_utils
    ):
        result = orders_table.display(
            ["John Smith", ""], sort="", service_type="Protein analysis"
        )
        assert _ids(result) == ["CB-003"]


# ============================================================================
# change() / add() / delete() - not implemented yet
# ============================================================================
class TestMutations:
    def test_change_not_implemented(self, orders_table):
        with pytest.raises(NotImplementedError):
            orders_table.change({})

    def test_add_not_implemented(self, orders_table):
        with pytest.raises(NotImplementedError):
            orders_table.add({})

    def test_delete_not_implemented(self, orders_table):
        with pytest.raises(NotImplementedError):
            orders_table.delete(1)
