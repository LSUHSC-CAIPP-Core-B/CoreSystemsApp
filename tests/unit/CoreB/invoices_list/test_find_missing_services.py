import pandas as pd

from app.CoreB.invoices_list.routes import find_missing_services, list_services

SERVICES_CSV = pd.DataFrame(
    {
        "Service": [
            "RNA-seq DEG Analysis",
            "Pathway Analysis (ClusterProfiler and/or 3PodR, etc.)",
            "Small RNA-seq",
        ],
        "Price": [50, 125, 50],
    }
)


def test_added_sub_service_has_no_invoice_row_yet():
    existing = {"RNA-seq DEG Analysis"}
    current = ["RNA-seq DEG Analysis", "Pathway Analysis (ClusterProfiler and/or 3PodR, etc.)"]

    missing = find_missing_services(current, existing)

    assert missing == ["Pathway Analysis (ClusterProfiler and/or 3PodR, etc.)"]


def test_nothing_missing_when_every_service_already_invoiced():
    existing = {"RNA-seq DEG Analysis", "Small RNA-seq"}
    current = ["RNA-seq DEG Analysis", "Small RNA-seq"]

    assert find_missing_services(current, existing) == []


def test_removed_sub_service_is_not_reported_as_missing():
    existing = {"RNA-seq DEG Analysis", "Small RNA-seq"}
    current = ["RNA-seq DEG Analysis"]

    assert find_missing_services(current, existing) == []


def test_all_services_missing_when_invoice_is_empty():
    current = ["RNA-seq DEG Analysis", "Small RNA-seq"]

    assert find_missing_services(current, set()) == current


def test_order_of_current_services_is_preserved():
    current = ["Small RNA-seq", "RNA-seq DEG Analysis"]

    assert find_missing_services(current, set()) == current


def test_newly_added_sub_service_flows_from_order_string_to_missing():
    # Sub-service added on the order edit page -> it now appears in the order's
    # services string, so it should be picked up as a new invoice line.
    services_str = "RNA-seq DEG Analysis, Pathway Analysis (ClusterProfiler and/or 3PodR, etc.)"
    existing = {"RNA-seq DEG Analysis"}

    services_data = list_services(services_str, SERVICES_CSV)
    missing = find_missing_services(services_data, existing)

    assert missing == ["Pathway Analysis (ClusterProfiler and/or 3PodR, etc.)"]
