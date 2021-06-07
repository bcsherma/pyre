# -*- coding: utf-8 -*-
"""Tests for the retrostr module."""

import pytest
from pyre import retrostr


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("S7", ("S7", "", "")),
        ("D8/E2/G.1-3;2-H", ("D8", "E2/G", "1-3;2-H")),
        ("48.1-3", ("48", "", "1-3")),
        ("HR/F", ("HR", "F", "")),
        ("PO2(E2/TH).2-3", ("PO2(E2/TH)", "", "2-3")),
    ],
)
def test_split_desc(test_input, expected):
    """Test the split_description function."""
    assert retrostr.split_description(test_input) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("NP", ({}, set(), [0, 0, 0, 0])),
        ("64(2)3", ({}, set(), [-1, 0, -1, 0])),
        ("43", ({}, set(), [-1, 0, 0, 0])),
        ("E4", ({}, set("4"), [1, 0, 0, 0])),
        ("S8", ({"HIT_FL": 1}, set(), [1, 0, 0, 0])),
        ("D8", ({"HIT_FL": 2}, set(), [2, 0, 0, 0])),
        ("T8", ({"HIT_FL": 3}, set(), [3, 0, 0, 0])),
        ("HR", ({"HIT_FL": 4}, set(), [4, 0, 0, 0])),
        ("C", ({}, set(), [1, 0, 0, 0])),
        ("HP", ({}, set(), [1, 0, 0, 0])),
        ("K", ({}, set(), [-1, 0, 0, 0])),
        ("W", ({}, set(), [1, 0, 0, 0])),
        ("SB3", ({}, set(), [0, 0, 3, 0])),
        ("CS2(1)", ({}, set(), [0, -1, 0, 0])),
        ("PO3(2)", ({}, set(), [0, 0, 0, -1])),
        ("PO2(E2/TH)", ({}, set("2"), [0, 0, 0, 0])),
    ],
)
def test_parse_event(test_input, expected):
    """Test the parse_event function."""
    assert retrostr.parse_event(test_input) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("E7", ({}, set("7"))),
    ],
)
def test_parser_modifiers(test_input, expected):
    """Test the parser_modifiers function"""
    assert retrostr.parse_modifiers(test_input) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("", (dict(), set(), [0, 0, 0, 0])),
        ("1-2", (dict(), set(), [0, 2, 0, 0])),
        ("2-3;3XH", (dict(), set(), [0, 0, 3, -1])),
        ("BX2(7E4)", (dict(), set("4"), [2, 0, 0, 0])),
    ],
)
def test_parse_advance(test_input, expected):
    assert retrostr.parse_advance(test_input) == expected
