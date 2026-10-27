"""Tests for the CLI's Report.

These tests were generated automatically by Claude Opus 5.
"""

import json

from nova.galaxy.cli.report import Report


def test_text_starts_with_the_title() -> None:
    report = Report(title="Connected to Galaxy", payload={"user": "tester"})

    assert report.get_text().splitlines()[0] == "Connected to Galaxy"


def test_text_indents_each_scalar_under_the_title() -> None:
    report = Report(title="Connected to Galaxy", payload={"url": "https://galaxy.example", "version": 24})

    assert report.get_text() == "\n".join(
        [
            "Connected to Galaxy",
            "  url: https://galaxy.example",
            "  version: 24",
        ]
    )


def test_text_puts_a_nested_dict_beneath_its_key() -> None:
    report = Report(title="Report", payload={"version": {"major": "24.1", "extra": {"commit": "abc123"}}})

    assert report.get_text() == "\n".join(
        [
            "Report",
            "  version:",
            "    major: 24.1",
            "    extra:",
            "      commit: abc123",
        ]
    )


def test_text_marks_list_entries_with_a_dash() -> None:
    report = Report(title="Report", payload={"stores": ["first", "second"]})

    assert report.get_text() == "\n".join(
        [
            "Report",
            "  stores:",
            "    - first",
            "    - second",
        ]
    )


def test_text_expands_a_dict_inside_a_list() -> None:
    report = Report(title="Report", payload={"stores": [{"name": "first"}]})

    assert report.get_text() == "\n".join(
        [
            "Report",
            "  stores:",
            "    -",
            "      name: first",
        ]
    )


def test_text_keeps_an_empty_container_on_the_line_of_its_key() -> None:
    report = Report(title="Report", payload={"user": {}, "stores": []})

    assert report.get_text() == "\n".join(
        [
            "Report",
            "  user: {}",
            "  stores: []",
        ]
    )


def test_text_of_an_empty_report_is_just_the_title() -> None:
    assert Report(title="Nothing to report").get_text() == "Nothing to report"


def test_str_is_the_text_rendering() -> None:
    report = Report(title="Report", payload={"user": {"name": "tester"}})

    assert str(report) == report.get_text()


def test_json_holds_the_payload_without_the_title() -> None:
    payload = {"url": "https://galaxy.example", "version": {"major": "24.1"}, "stores": []}
    report = Report(title="Connected to Galaxy", payload=payload)

    assert json.loads(report.get_json()) == payload
    assert "Connected to Galaxy" not in report.get_json()


def test_json_of_an_empty_report_is_an_empty_object() -> None:
    assert json.loads(Report(title="Nothing to report").get_json()) == {}


def test_reports_do_not_share_a_default_payload() -> None:
    first = Report(title="First")
    second = Report(title="Second")

    first.payload["url"] = "https://galaxy.example"

    assert second.payload == {}
