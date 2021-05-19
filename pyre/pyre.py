# -*- coding: utf-8 -*-
"""Core behavior for the python retrosheet event parser (pyre).

This module contains implementation of the EventFileReader class for generating
tabular data from retrosheet event files.
"""

import typing

import pandas as pd

from . import data, retrostr


class EventFileReader:
    """Parser for retrosheet event files.

    Attributes:
        year: Year of the season for the event file.
        path: Local path to the event file.
        event_file: Open buffer for reading from the event file.
        h_lineup: List containing the home lineup, indexed by position.
        v_lineup: List containing the visiting lineup, indexed by position.
        h_roster: DataFrame containing home roster.
        v_roster: DataFrame containing the visiting roster.
        outs_in_current_inning: Number of outs in the inning being processed.
        runners_on_base: List of runners on base.
        runner_dest: Destinations of the runners currently on base.
        current_game: Dictionary of information about the game being processed.
        current_event: Dictionary of information about the play being processed.
    """

    def __init__(self, team: str, year: int, league: str):
        """Creates a reader for the given event file.

        Args:
            team: 3 letter code for the team whose file should be read.
            year: Year of the event file to be read.
            league: 'A' or 'N', depending on which league the team plays for.

        Returns:
            None.
        """
        self.year = year
        self.path = data.get_event_file(year, team, league)
        self.event_file = None
        self._reset_state()

    def data_frame(self) -> pd.DataFrame:
        """Parse the event file and return data frame.

        Returns:
            Pandas DataFrame of event file data.
        """
        return pd.DataFrame(self.parse())

    def parse(self):
        """Executes parsing of the event file and generates tabular data.

        Yields:
            Tabular data entry for each play that occurs in the event file.
        """
        self._reset_state()
        with open(self.path) as infile:
            while True:
                line = infile.readline()
                if not line:
                    return
                fields = line.strip().split(",")
                if fields[0] == "id":
                    self._new_game(fields[1], infile)
                    yield from self._read_game(infile)

    def _reset_state(self):
        """Reset fields that track the state of the game currently being parsed.

        Returns:
            None.
        """
        self.info = dict()  # Stores game data, e.g. data, weather
        self.h_lineup = [""] * 12  # Stores lineup, indexed by position
        self.v_lineup = [""] * 12
        self.h_roster = None
        self.v_roster = None
        self.h_score = 0
        self.v_score = 0
        self.outs_in_current_inning = 0
        self.runners_on_base = [""] * 4
        self.runner_dest = [0] * 4
        self.current_game = None
        self.current_event = None

    def _new_game(self, game_id: str, infile: typing.TextIO):
        """Consumes lines describing game metadata from the event file.

        Args:
            game_id: Identifier for the game.
            infile: Open buffer reading the event file.

        Returns:
            None.
        """
        self.current_game = {"id": game_id}
        while True:
            prev_loc = infile.tell()
            line = infile.readline()
            if not line:
                raise Exception("Encountered EOF while parsing new game info")
            fields = line.strip().split(",")
            if fields[0] not in ("version", "info"):
                infile.seek(prev_loc)
                return
            if fields[0] == "info":
                field, value = fields[1:]
                self.current_game[field] = value
                if field == "visteam":
                    self.v_roster = data.get_roster(self.year, value)
                elif field == "hometeam":
                    self.h_roster = data.get_roster(self.year, value)

    def _read_game(self, infile: typing.TextIO):
        """Read events and generate data until a new game is declared in the file.

        Args:
            infile: An open buffer reading the event file.

        Yields:
            A row of tabular data for every play in the game.
        """
        while True:
            prev_loc = infile.tell()
            line = infile.readline()
            if not line:
                return
            fields = line.strip().split(",")
            if fields[0] == "id":
                infile.seek(prev_loc)
                return
            if fields[0] in ["start", "sub"]:
                pid: str = fields[1]
                pos: int = int(fields[5])
                lineup = self.h_lineup if int(fields[3]) else self.v_lineup
                lineup[pos - 1] = pid
                continue
            if fields[0] == "play":
                self._process_play(*fields[1:])
                yield self.current_event
                self.current_event = None

    def _process_play(
        self,
        inning: str,
        side: int,
        batter: str,
        count: str,
        pitches: str,
        description: str,
    ):
        """Interpret play information to update the next generated entry.

        Args:
            inning: Current inning of play.
            side: 0 if home team batting else 1.
            batter: ID of the current batter.
            count: 2 character string containing number of balls and strikes
                when the play occurred, e.g., "32" means the play occurred on a
                full count.
            pitches: Sequence of pitches leading to the play.
            description: Retrosheet formatted event description.

        Returns:
            None.
        """
        self.runners_on_base[0] = batter
        self._generate_event(inning, side, batter, count, pitches)
        self._process_description(description)
        # Set outs to 0 if we have reached 3, a new inning is coming
        if self.outs_in_current_inning > 2:
            self.outs_in_current_inning = 0
            self.runners_on_base = 4 * [""]
            self.runner_dest = 4 * [0]

    def _generate_event(
        self, inning: str, side: int, batter: str, count: str, pitches: str
    ):
        """Resets the current_event field to partially describe the new play.

        Args:
            inning: Current inning of play.
            side: 0 if home team batting else 1.
            batter: ID of the current batter.
            count: 2 character string containing number of balls and strikes
                when the play occurred, e.g., "32" means the play occurred on a
                full count.
            pitches: Sequence of pitches leading to the play.

        Returns:
            None.
        """
        def_lineup = self.v_lineup if side else self.h_lineup
        self.current_event = {
            "game_id": self.current_game["id"],
            "visteam": self.current_game["visteam"],
            "hometeam": self.current_game["hometeam"],
            "inning": inning,
            "batting_team": self.current_game["hometeam" if side else "visteam"],
            "outs": self.outs_in_current_inning,
            "balls": int(count[0]),
            "strikes": int(count[1]),
            "pitches": pitches,
            "batter": batter,
            "P": def_lineup[0],
            "C": def_lineup[1],
            "1B": def_lineup[2],
            "2B": def_lineup[3],
            "3B": def_lineup[4],
            "SS": def_lineup[5],
            "LF": def_lineup[6],
            "CF": def_lineup[7],
            "RF": def_lineup[8],
            "ROF": self.runners_on_base[1],
            "ROS": self.runners_on_base[2],
            "ROT": self.runners_on_base[3],
        }

    def _process_description(self, description: str):
        """Update current_event dictionary based on play description.

        This method separates the text and makes calls to other methods to
        separately process the 3 sections.

        Args:
            description: A description of the play.

        Returns:
            None.
        """
        self.runner_dest = 4 * [0]
        event, mod, adv = retrostr.split_description(description)
        info, errors, dest = retrostr.parse_event(event)
        self._update_destinations(dest)
        self.current_event.update(info)
        new_info, new_errors = retrostr.parse_modifiers(mod)
        errors |= new_errors
        self.current_event.update(new_info)
        self._update_destinations(retrostr.parse_advance(adv))
        for e in errors:
            self._add_error(e)

    def _update_destinations(self, destinations):
        """Update the runner_destinations field using the given list."""
        for i in range(4):
            self.runner_dest[i] = destinations[i] or self.runner_dest[i]

    def _update_runners(self):
        """Update current runner positions given the known runner destinations.

        This method assumes that the runner_destinations field accurately
        describes the runner positions for the following play.

        Returns:
            None.
        """
        for base in 3, 2, 1, 0:
            dest = self.runner_dest[base]
            if dest is None:
                continue
            if dest < 0:
                self.outs_in_current_inning += 1
                self.runners_on_base[base] = ""
            elif dest < 4:
                self.runners_on_base[dest] = self.runners_on_base[base]
            else:
                self.runners_on_base[base] = ""
        self.current_event["BAT_DEST"] = self.runner_dest[0]
        self.current_event["ROF_DEST"] = self.runner_dest[1]
        self.current_event["ROS_DEST"] = self.runner_dest[2]
        self.current_event["ROT_DEST"] = self.runner_dest[3]

    def _add_error(self, charged: str):
        """Record an error on the play.

        Args:
            charged: Position # of player charged with error.

        Returns:
            None.
        """
        error_cnt = 1
        while True:
            if self.current_event.get(f"error_{error_cnt}"):
                error_cnt += 1
                continue
            self.current_event[f"error_{error_cnt}"] = charged
            break

    def _add_putout(self, responsible: str):
        """Record a putout in the current_event dictionary.

        Args:
            responsible: Position # of player responsible for putout.

        Returns:
            None.
        """
        po_cnt = 1
        while True:
            if self.current_event.get(f"putout_{po_cnt}"):
                po_cnt += 1
                continue
            self.current_event[f"putout_{po_cnt}"] = responsible
            break
