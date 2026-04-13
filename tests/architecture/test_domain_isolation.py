from pytest_archon import archrule


def test_ariadne_domain_isolation():
    (
        archrule("Ariadne Domain Isolation")
        .match("src.automation.ariadne*")
        .should_not_import("src.automation.motors*")
        .should_not_import("requests*")
        .should_not_import("httpx*")
        .check("src.automation")
    )


def test_executors_are_dumb():
    (
        archrule("Dumb Executors")
        .match("src.automation.motors*")
        .should_not_import("src.automation.ariadne.models*")
        .check("src.automation")
    )
