import pytest
from app.utils.db_utils import db_utils

# ============================================================================
# isValidDateFormat — regex check
# ============================================================================
class TestIsValidDateFormat:
    @pytest.mark.parametrize("date_str", [
        "2024-01-15",
        "0001-01-01",
        "9999-12-31"
    ])
    def test_formed_strings(self, date_str):
        assert db_utils.isValidDateFormat(date_str) is True

    @pytest.mark.parametrize("date_str", [
        "2024/01/15",          # slashes
        "2024.01.15",          # dots
        "2024_01_15",          # underscores
        "01-15-2024",          # MM-DD-YYYY
        "15-01-2024",          # DD-MM-YYYY
        "2024-1-15",           # month not zero-padded
        "2024-01-5",           # day not zero-padded
        "24-01-15",            # 2 digit year
        "20245-01-15",         # 5 digit year
        "2024-01",             # incomplete
        "2024",                # year only
        "2024-01-15 ",         # trailing space
        " 2024-01-15",         # leading space
        "2024-01-15T00:00",    # time appended
        "2024-01-15extra",     # trailing garbage
        "abcd-ef-gh",          # letters in numeric slots
        "",                    # empty string
    ])
    def test_malformed_strings(self, date_str):
        assert db_utils.isValidDateFormat(date_str) is False

# ============================================================================
# isValidDate — calendar correctness check
# ============================================================================
class TestIsValidDate:
    @pytest.mark.parametrize("date_str", [
        "2024-01-15",
        "2024-12-31",
        "2024-01-01",
        "1999-06-30",
    ])
    def test_ordinary_real_dates(self, date_str):
        assert db_utils.isValidDate(date_str) is True

    @pytest.mark.parametrize("date_str", [
        "2024-02-29",   # divisible by 4, not by 100
        "2000-02-29",   # divisible by 400 (century leap rule)
        "2400-02-29",   # also divisible by 400
    ])
    def test_leap_year_february_29(self, date_str):
        assert db_utils.isValidDate(date_str) is True

    @pytest.mark.parametrize("date_str", [
        "2023-02-29",   # not divisible by 4
        "2100-02-29",   # divisible by 100, NOT by 400, not a leap year
        "1900-02-29",   # same: century rule excludes it
        "2024-02-30",   # February never has 30
        "2024-02-31",   # February never has 31
    ])
    def test_invalid_february_dates(self, date_str):
        assert db_utils.isValidDate(date_str) is False

    @pytest.mark.parametrize("date_str", [
        "2024-04-31",   # April has 30
        "2024-06-31",   # June has 30
        "2024-09-31",   # September has 30
        "2024-11-31",   # November has 30
    ])
    def test_30_day_months_rejecting_day_31(self, date_str):
        assert db_utils.isValidDate(date_str) is False

    @pytest.mark.parametrize("date_str", [
        "2024-13-01",   # month 13
        "2024-00-15",   # month 0
        "2024-99-15",   # month 99
        "2024-01-32",   # day 32
        "2024-01-00",   # day 0
        "2024-01-99",   # day 99
    ])
    def test_out_of_range_components(self, date_str):
        assert db_utils.isValidDate(date_str) is False

    @pytest.mark.parametrize("date_str", [
        "not a date",
        "",
        "2024",
        "2024-01",
        "2024/01/15",
        "Jan 15, 2024",
        "15/01/2024",
    ])
    def test_garbage_inputs(self, date_str):
        assert db_utils.isValidDate(date_str) is False