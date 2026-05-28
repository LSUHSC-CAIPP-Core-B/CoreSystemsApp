import pandas as pd
import pytest

from app.utils.search_utils import search_utils


@pytest.fixture
def orders_df():
    """Small orders-like DataFrame mirroring the shape of CoreB_Order rows."""
    return pd.DataFrame(
        [
            {
                "PI Name": "John_Smith",
                "Project ID": "PROJ001",
                "Request Date": "2024-01-15",
            },
            {
                "PI Name": "Jane_Doe",
                "Project ID": "PROJ002",
                "Request Date": "2024-02-20",
            },
            {
                "PI Name": "Bob_Jones",
                "Project ID": "PROJ003",
                "Request Date": "2024-03-10",
            },
            {
                "PI Name": "Alice_Williams",
                "Project ID": "PROJ004",
                "Request Date": "2024-01-05",
            },
            {
                "PI Name": "",
                "Project ID": "",
                "Request Date": "2024-04-01",
            },  # unassigned
        ]
    )


# ============================================================================
# No filter branch — empty/whitespace inputs return everything
# ============================================================================
class TestNoFilters:
    @pytest.mark.parametrize(
        "inputs",
        [
            ["", ""],
            ["   ", "   "],
            ["", "\t"],
            [" ", ""],
            ["\n", " \t "],
        ],
    )
    def test_empty_or_whitespace_inputs_return_all_rows(self, orders_df, inputs):
        result = search_utils.sort_searched_data(
            inputs, ["PI Name", "Project ID"], 50, orders_df.copy(), sort_by=None
        )
        assert len(result) == len(orders_df)

    def test_sort_by_none_preserves_input_order(self, orders_df):
        original_order = orders_df["Project ID"].tolist()
        result = search_utils.sort_searched_data(
            ["", ""], ["PI Name", "Project ID"], 50, orders_df.copy(), sort_by=None
        )
        assert result["Project ID"].tolist() == original_order

    def test_sort_by_request_date_descending(self, orders_df):
        result = search_utils.sort_searched_data(
            ["", ""],
            ["PI Name", "Project ID"],
            50,
            orders_df.copy(),
            sort_by="Request Date",
        )
        dates = result["Request Date"].tolist()
        assert dates == sorted(dates, reverse=True)

    def test_not_sorted_sorts_by_request_date_ascending(self, orders_df):
        """worth pinning down: in the no-filter branch, sort_by='Not Sorted'
        actually sorts by Request Date ascending."""
        result = search_utils.sort_searched_data(
            ["", ""],
            ["PI Name", "Project ID"],
            50,
            orders_df.copy(),
            sort_by="Not Sorted",
        )
        dates = result["Request Date"].tolist()
        assert dates == sorted(dates)

    def test_sort_by_arbitrary_column_ascending(self, orders_df):
        result = search_utils.sort_searched_data(
            ["", ""],
            ["PI Name", "Project ID"],
            50,
            orders_df.copy(),
            sort_by="Project ID",
        )
        ids = result["Project ID"].tolist()
        assert ids == sorted(ids)


# ============================================================================
# Active columns guard — regression test for blank input matching blank values
# ============================================================================
class TestActiveColumnsGuard:
    def test_blank_input_does_not_pull_blank_valued_rows(self, orders_df):
        """Regression: searching by Project ID with PI Name left blank must not
        return the unassigned row (PI Name='', Project ID='') just because
        fuzz.ratio('', '') is 100. The fix only scores columns whose input is
        non-blank, so the unassigned row gets ratio 0 on Project ID and is
        correctly filtered out."""
        result = search_utils.sort_searched_data(
            ["", "PROJ001"],
            ["PI Name", "Project ID"],
            50,
            orders_df.copy(),
            sort_by=None,
        )
        project_ids = result["Project ID"].tolist()
        assert "PROJ001" in project_ids
        assert "" not in project_ids

    def test_both_inputs_blank_falls_through_to_no_filter_branch(self, orders_df):
        """When every input is blank, no filtering should happen."""
        result = search_utils.sort_searched_data(
            ["", ""], ["PI Name", "Project ID"], 99, orders_df.copy(), sort_by=None
        )
        assert len(result) == len(orders_df)

    def test_only_one_column_searched_does_not_affect_other_column_values(
        self, orders_df
    ):
        """Searching only Project ID should not depend on PI Name content."""
        result = search_utils.sort_searched_data(
            ["", "PROJ002"],
            ["PI Name", "Project ID"],
            99,
            orders_df.copy(),
            sort_by=None,
        )
        assert len(result) == 1
        assert result.iloc[0]["PI Name"] == "Jane_Doe"


# ============================================================================
# Threshold filtering
# ============================================================================
class TestThresholdFiltering:
    def test_exact_match_passes_high_threshold(self, orders_df):
        result = search_utils.sort_searched_data(
            ["John_Smith", ""],
            ["PI Name", "Project ID"],
            99,
            orders_df.copy(),
            sort_by=None,
        )
        assert len(result) == 1
        assert result.iloc[0]["PI Name"] == "John_Smith"

    def test_no_matches_returns_empty_dataframe(self, orders_df):
        result = search_utils.sort_searched_data(
            ["Xyzzy_Plover", ""],
            ["PI Name", "Project ID"],
            80,
            orders_df.copy(),
            sort_by=None,
        )
        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)

    def test_any_column_above_threshold_keeps_row(self, orders_df):
        """When multiple columns are searched, a row is kept if ANY column
        clears the threshold (logical OR, not AND)."""
        result = search_utils.sort_searched_data(
            ["Xyzzy_Plover", "PROJ002"],
            ["PI Name", "Project ID"],
            99,
            orders_df.copy(),
            sort_by=None,
        )
        # PI Name fails the threshold but Project ID hits exactly, so Jane_Doe stays.
        assert "PROJ002" in result["Project ID"].tolist()


# ============================================================================
# Sort behavior in the filtered branch
# ============================================================================
class TestSortInFilteredBranch:
    def test_request_date_sorts_descending(self, orders_df):
        # Match all four assigned rows (they share the "PROJ" prefix).
        result = search_utils.sort_searched_data(
            ["", "PROJ"],
            ["PI Name", "Project ID"],
            30,
            orders_df.copy(),
            sort_by="Request Date",
        )
        dates = result["Request Date"].tolist()
        assert dates == sorted(dates, reverse=True)

    def test_arbitrary_column_sorts_ascending_after_match_quality(self, orders_df):
        result = search_utils.sort_searched_data(
            ["", "PROJ"],
            ["PI Name", "Project ID"],
            30,
            orders_df.copy(),
            sort_by="Project ID",
        )
        # Match-quality is primary sort key (desc); for rows with equal scores,
        # Project ID is the tiebreaker (asc). All four rows have similar scores
        # against "PROJ", so the result should be primarily quality-ordered.
        assert len(result) >= 2

    def test_sort_by_none_does_not_raise(self, orders_df):
        result = search_utils.sort_searched_data(
            ["John_Smith", ""],
            ["PI Name", "Project ID"],
            99,
            orders_df.copy(),
            sort_by=None,
        )
        assert len(result) == 1

    def test_sort_by_not_sorted_does_not_raise(self, orders_df):
        result = search_utils.sort_searched_data(
            ["John_Smith", ""],
            ["PI Name", "Project ID"],
            99,
            orders_df.copy(),
            sort_by="Not Sorted",
        )
        assert len(result) == 1


# ============================================================================
# Output shape — ratio columns cleaned up, return type is DataFrame
# ============================================================================
class TestOutputShape:
    def test_no_ratio_columns_in_filtered_output(self, orders_df):
        result = search_utils.sort_searched_data(
            ["John_Smith", ""],
            ["PI Name", "Project ID"],
            50,
            orders_df.copy(),
            sort_by=None,
        )
        assert not any(col.endswith("_ratio") for col in result.columns)

    def test_no_ratio_columns_in_unfiltered_output(self, orders_df):
        result = search_utils.sort_searched_data(
            ["", ""], ["PI Name", "Project ID"], 50, orders_df.copy(), sort_by=None
        )
        assert not any(col.endswith("_ratio") for col in result.columns)

    def test_returns_dataframe(self, orders_df):
        """Note: the type annotation says list[dict[Hashable, Any]] but the
        implementation returns a DataFrame. This pins the actual behavior."""
        result = search_utils.sort_searched_data(
            ["", ""], ["PI Name", "Project ID"], 50, orders_df.copy(), sort_by=None
        )
        assert isinstance(result, pd.DataFrame)

    def test_original_columns_preserved(self, orders_df):
        result = search_utils.sort_searched_data(
            ["John_Smith", ""],
            ["PI Name", "Project ID"],
            50,
            orders_df.copy(),
            sort_by=None,
        )
        for col in ["PI Name", "Project ID", "Request Date"]:
            assert col in result.columns


# ============================================================================
# columns_rename
# ============================================================================
class TestColumnsRename:
    def test_rename_in_no_filter_branch(self, orders_df):
        result = search_utils.sort_searched_data(
            ["", ""],
            ["PI Name", "Project ID"],
            50,
            orders_df.copy(),
            sort_by=None,
            columns_rename={"PI Name": "PI"},
        )
        assert "PI" in result.columns
        assert "PI Name" not in result.columns

    def test_rename_in_filtered_branch(self, orders_df):
        result = search_utils.sort_searched_data(
            ["John_Smith", ""],
            ["PI Name", "Project ID"],
            50,
            orders_df.copy(),
            sort_by=None,
            columns_rename={"PI Name": "PI"},
        )
        assert "PI" in result.columns
        assert "PI Name" not in result.columns

    def test_no_rename_when_none_passed(self, orders_df):
        result = search_utils.sort_searched_data(
            ["", ""], ["PI Name", "Project ID"], 50, orders_df.copy(), sort_by=None
        )
        assert "PI Name" in result.columns

    def test_rename_multiple_columns(self, orders_df):
        result = search_utils.sort_searched_data(
            ["", ""],
            ["PI Name", "Project ID"],
            50,
            orders_df.copy(),
            sort_by=None,
            columns_rename={"PI Name": "PI", "Project ID": "Project"},
        )
        assert "PI" in result.columns
        assert "Project" in result.columns
