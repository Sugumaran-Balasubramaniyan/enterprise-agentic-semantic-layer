"""Unit tests for the EASL command-line interface."""

from __future__ import annotations

import json

import pytest

from semantic_layer.cli import build_parser, main


def test_cli_parser_subcommands_registered() -> None:
    parser = build_parser()
    subparsers_action = next(
        action for action in parser._actions if action.dest == "command"
    )
    assert "query" in subparsers_action.choices
    assert "ask" in subparsers_action.choices
    assert "serve" in subparsers_action.choices
    assert "validate" in subparsers_action.choices
    assert "info" in subparsers_action.choices
    assert "demo" in subparsers_action.choices


def test_cli_info_command(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["info"])
    assert rc == 0
    captured = capsys.readouterr().out
    assert "ENTERPRISE AGENTIC SEMANTIC LAYER (EASL) - REGISTRY INFO" in captured
    assert "ACDOCAFinancials" in captured
    assert "ciferp:BusinessPartner" in captured


def test_cli_ask_command(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["ask", "What are the prerequisite notes required for SAP Note 3109922?"])
    assert rc == 0
    captured = capsys.readouterr().out
    assert "EASL KNOWLEDGE GRAPH AQR REASONING" in captured
    assert "SUCCESS" in captured
    assert "SPARQL" in captured


def test_cli_ask_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["ask", "What are the prerequisite notes required for SAP Note 3109922?", "--json"])
    assert rc == 0
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert data["status"] == "SUCCESS"
    assert "sparql" in data


def test_cli_query_command(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main([
        "query",
        "Find French automotive business partners with at least three qualifying financial postings in the last 12 months and total debit loss above EUR 20,000.",
    ])
    assert rc == 0
    captured = capsys.readouterr().out
    assert "EASL GOVERNED QUERY RESULT" in captured
    assert "COMPILED SQL:" in captured
    assert "RESULT ROWS:" in captured
    assert "FR_001" in captured


def test_cli_query_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main([
        "query",
        "Find French automotive business partners with at least three qualifying financial postings in the last 12 months and total debit loss above EUR 20,000.",
        "--json",
    ])
    assert rc == 0
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert "compiled_query" in data
    assert "provenance" in data
    assert len(data["result"]) > 0


def test_cli_no_args_shows_help(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main([])
    assert rc == 1
    captured = capsys.readouterr()
    assert "usage:" in captured.out or "usage:" in captured.err
