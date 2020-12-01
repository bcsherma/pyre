# -*- coding: utf-8 -*-
"""Library for downloading and storing retrosheet event files for parsing."""

import os
import urllib.request

import pandas as pd

# Base URLs for data sources.
_EVENT_URL = "https://raw.githubusercontent.com/chadwickbureau/retrosheet/master/event/regular/"
_ROSTER_URL = "https://raw.githubusercontent.com/chadwickbureau/retrosheet/master/rosters/"

# Directory in which to store downloaded data.
_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".pyre/")
if not os.path.isdir(_CACHE_DIR):
    os.mkdir(_CACHE_DIR)

# Column names for the roster file.
_ROSTER_COL_NAMES = ["id", "first_name",
                     "last_name", "bats", "throws", "pos", "team"]


def get_roster(year: int, team: str) -> pd.DataFrame:
    """Download (if necessary) roster file and load as a DataFrame.

    Args:
        year: Year to load roster from.
        team: Team to load roster of.

    Returns:
        Roster as a DataFrame.
    """
    roster_file = f"{team}{year}.ROS"
    full_path = _CACHE_DIR + roster_file
    if not os.path.isfile(full_path):
        urllib.request.urlretrieve(_ROSTER_URL + roster_file, full_path)
    return pd.read_csv(full_path, names=_ROSTER_COL_NAMES, index_col="id")


def get_event_file(year: int, team: str, league: str) -> str:
    """Download (if necessary) and return the local location of an event file.

    Args:
        year: Year to load event file from.
        team: Team to load event file for.
        league: 'N' if team played in national league, 'A' if American.

    Returns:
        Location of event file on local system.
    """
    if league not in ("A", "N"):
        raise Exception()
    event_file = f"{year}{team}.EV{league}"
    full_path = _CACHE_DIR + event_file
    if not os.path.isfile(full_path):
        urllib.request.urlretrieve(_EVENT_URL + event_file, full_path)
    return full_path
