import pandas as pd

from app.CoreB.invoices_list.routes import find_stale_services

KNOWN_SERVICES = [
    "RNA-seq DEG Analysis",
    "Pathway Analysis (ClusterProfiler and/or 3PodR, etc.)",
    "Small RNA-seq",
    "BioRender license",
]


def test_removed_sub_service_is_stale():
    existing = {"RNA-seq DEG Analysis", "Pathway Analysis (ClusterProfiler and/or 3PodR, etc.)"}
    current = ["RNA-seq DEG Analysis"]

    stale = find_stale_services(existing, current, KNOWN_SERVICES)

    assert stale == ["Pathway Analysis (ClusterProfiler and/or 3PodR, etc.)"]


def test_nothing_stale_when_selections_match():
    existing = {"RNA-seq DEG Analysis", "Small RNA-seq"}
    current = ["RNA-seq DEG Analysis", "Small RNA-seq"]

    assert find_stale_services(existing, current, KNOWN_SERVICES) == []


def test_added_sub_service_is_not_stale():
    existing = {"RNA-seq DEG Analysis"}
    current = ["RNA-seq DEG Analysis", "Small RNA-seq"]

    assert find_stale_services(existing, current, KNOWN_SERVICES) == []


def test_all_services_discount_row_is_never_stale():
    existing = {"RNA-seq DEG Analysis", "All services discount"}
    current = ["RNA-seq DEG Analysis"]

    assert find_stale_services(existing, current, KNOWN_SERVICES) == []


def test_unrecognised_service_row_is_left_alone():
    existing = {"Some custom manual line item"}
    current = ["RNA-seq DEG Analysis"]

    assert find_stale_services(existing, current, KNOWN_SERVICES) == []


def test_all_sub_services_removed():
    existing = {"RNA-seq DEG Analysis", "Small RNA-seq"}

    stale = find_stale_services(existing, [], KNOWN_SERVICES)

    assert sorted(stale) == ["RNA-seq DEG Analysis", "Small RNA-seq"]


def test_accepts_pandas_series_for_known_services():
    known = pd.Series(KNOWN_SERVICES)
    existing = {"Small RNA-seq"}

    assert find_stale_services(existing, ["RNA-seq DEG Analysis"], known) == ["Small RNA-seq"]
