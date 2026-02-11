from app.utils.string_utils import string_utils

def test_isValidInput():
    assert string_utils.isValidInput("Hello", "Hellso") is True