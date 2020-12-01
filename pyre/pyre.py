# -*- coding: utf-8 -*-
"""Core behavior for the python retrosheet event parser (pyre).

This module contains implementation of the EventFileReader class for generating
tabular data from retrosheet event files.
"""

import re
import typing

from . import data

_DP = re.compile(r"([\d]+)\(([123B])\)([\d]+)(?:\(([123B])\))?")
_OUT = re.compile(r"([\d]+)")
_ERR = re.compile(r"E(\d)")
_HIT = re.compile(r"([SDTH]|(?:FC)|(?:FLE))([\d]|(?:GR))?")
_HR = re.compile(r"(HR?)(\d?)$")
_KW = re.compile(r"(K|W|(?:IW?))(?:\+(.*))?")
_SB = re.compile(r"(SB)([23H])")
_PO = re.compile(r"PO([123])\(E?[\d]+\)")
_CS = re.compile(r"(?:PO)?(?:CS)([23H])\((\d+)\)")
_ADV = re.compile(r"([123B])([-X])([123H])(?:\(.*\))*")


class EventFileReader:
    """Parser for retrosheet event files.

    Attributes:
        year: Year of the season for the event file.
        path: Local path to the event file.
        event_file: Open buffer reading from the event file.
        h_lineup: List containing the home lineup, indexed by position.
        v_lineup: List containing the visiting lineup, indexed by position.
        h_roster: DataFrame containg home roster.
        v_roster: DataFrame conatining the visiting roster.
        outs_in_current_inning: Number of outs in the inning being processed.
        runners_on_base: List of runners on base.
        runner_destinations: Destinations of the runners currently on base.
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
        """Reset fields that track the state of the game being parsed.

        Returns:
            None.
        """
        self.info = dict()  # Stores game data, e.g. data, weather
        self.h_lineup = [None] * 12  # Stores lineup, indexed by position
        self.v_lineup = [None] * 12
        self.h_roster = None
        self.v_roster = None
        self.home_score = 0
        self.away_score = 0
        self.outs_in_current_inning = 0
        self.runners_on_base = [None] * 4
        self.runner_destinations = [None] * 4
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
                raise("Encountered EOF while parsing new game info")
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
                pid, pos = fields[1], int(fields[5])
                lineup = self.h_lineup if int(fields[3]) else self.v_lineup
                lineup[pos - 1] = pid
                continue
            if fields[0] == "play":
                self._process_play(*fields[1:])
                yield self.current_event
                self.current_event = None

    def _process_play(self, inning: str, side: str, batter: str, count: str, pitches: str, description: str):
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
        side = int(side)
        self.runners_on_base[0] = batter
        self._generate_event(inning, side, batter, count, pitches)
        self._process_description(description)
        # Set outs to 0 if we have reached 3, a new inning is coming
        if self.outs_in_current_inning > 2:
            self.outs_in_current_inning = 0
            self.runners_on_base = 4*[None]
            self.runner_destinations = 4*[None]

    def _generate_event(self, inning: str, side: str, batter: str, count: str, pitches: str):
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
            "P": (self.v_lineup if side else self.h_lineup)[0],
            "C": (self.v_lineup if side else self.h_lineup)[1],
            "1B": (self.v_lineup if side else self.h_lineup)[2],
            "2B": (self.v_lineup if side else self.h_lineup)[3],
            "3B": (self.v_lineup if side else self.h_lineup)[4],
            "SS": (self.v_lineup if side else self.h_lineup)[5],
            "LF": (self.v_lineup if side else self.h_lineup)[6],
            "CF": (self.v_lineup if side else self.h_lineup)[7],
            "RF": (self.v_lineup if side else self.h_lineup)[8],
            "ROF": self.runners_on_base[1],
            "ROS": self.runners_on_base[2],
            "ROT": self.runners_on_base[3],
        }

    def _process_description(self, description: str):
        """Update current_event dictionary based on play description.

        The play description is made up of three sections:
            1) A description of basic play that occurred.
            2) A series of flags conveying additional information.
            3) A description of all runner advances in the play.

        This method separates the text and makes calls to other methods to
        separately process the 3 sections.

        Args:
            description: A description of the play.

        Returns:
            None.
        """
        self.current_event["description"] = description
        start_mod = description.find("/")
        if start_mod < 0:
            start_mod = len(description)
        start_adv = description.rfind(".")
        if start_adv < 0:
            start_adv = len(description)
        event = description[:min(start_mod, start_adv)].rstrip('/.')
        mod = description[start_mod:start_adv].strip('/.')
        adv = description[start_adv:].lstrip('.')
        self.runner_destinations = 4*[None]
        self._process_event_text(event)
        self._process_modifier_text(mod)
        self._process_advance_text(adv)
        self._update_runners()

    def _update_runners(self):
        """Update current runner positions given the known runner destinations.

        This method assumes that the runner_destinations field accurately 
        desribes the runner positions for the following play.

        Returns:
            None.
        """
        for base in 3, 2, 1, 0:
            dest = self.runner_destinations[base]
            if dest is None:
                continue
            if dest < 0:
                self.outs_in_current_inning += 1
                self.runners_on_base[base] = None
            if dest < 4:
                self.runners_on_base[dest] = self.runners_on_base[base]
            else:
                self.runners_on_base[base] = None
        self.current_event["BAT_DEST"] = self.runner_destinations[0]
        self.current_event["ROF_DEST"] = self.runner_destinations[1]
        self.current_event["ROS_DEST"] = self.runner_destinations[2]
        self.current_event["ROT_DEST"] = self.runner_destinations[3]

    def _process_event_text(self, event: str):
        """Process the basic description of a play.

        Args:
            event: Coded description of the play.

        Returns:
            None.
        """
        if match := _DP.match(event):
            for runner in match.group(2), match.group(4):
                if runner == "B" or runner is None:
                    runner = 0
                runner = int(runner)
                self.runner_destinations[runner] = -1
        elif match := _OUT.match(event):
            self.runner_destinations[0] = -1
        elif match := _ERR.match(event):
            self.runner_destinations[0] = 1
            self._add_error(match.group(1))
        elif match := _HIT.match(event):
            self.current_event["hit_code"] = match.group(1)
            dest = {"S": 1, "D": 2, "T": 3}.get(match.group(1))
            self.runner_destinations[0] = dest
        elif match := _HR.match(event):
            self.runner_destinations[0] = 4
        elif event == "C":
            self.runner_destinations[0] = 1
        elif event == "HP":
            self.runner_destinations[0] = 1
        elif event == "NP":
            pass
        elif match := _KW.match(event):
            self.runner_destinations[0] = -1 if match.group(1) == "K" else 1
            if match.group(2) is not None:
                self._process_event_text(str(match.group(2)))
        elif match := _SB.match(event):
            base = match.group(1)
            base = 4 if base == "H" else int(base)
            self.runner_destinations[base-1] = base
        elif match := _CS.match(event):
            base = match.group(1)
            base = 4 if base == "H" else int(base)
            self.runner_destinations[base - 1] = -1
        elif match := _PO.match(event):
            base = int(match.group(1))
            self.runner_destinations[base] = -1
        elif event in ["PB", "BK", "WP", "DI", "OA"]:
            pass
        else:
            print("WARNING: Unrecognized event", event)

    def _process_modifier_text(self, mod: str):
        """Process all modifiers for the current play.

        Args:
            mod: A string containing a series of modifiers.

        Returns:
            None.
        """
        if not mod:
            return
        mods = mod.split("/")
        for mod in mods:
            if mod == "AP":
                self.current_event["appealed"] = True
            elif mod == "BP":
                self.current_event["bunt"] = True
                self.current_event["fly"] = True
            elif mod == "GP":
                self.current_event["bunt"] = True
            elif mod == "BGDP":
                self.current_event["bunt"] = True
                self.current_event["double_play"] = True
            elif mod == "BINT":
                self.current_event["batter_interference"] = True
            elif mod == "BL":
                self.current_event["bunt"] = True
            elif mod == "BPDP":
                self.current_event["bunt"] = True
                self.current_event["fly"] = True
                self.current_event["double_play"] = True
            elif mod == "BR":
                self.current_event["runner_hit"] = True
            elif mod == "C":
                self.current_event["called_third"] = True
            elif mod == "DP":
                self.current_event["double_play"] = True
            elif match := _ERR.match(mod):
                self._add_error(match.group(1))
            elif mod == "F":
                self.current_event["fly"] = True
            elif mod == "FDP":
                self.current_event["fly"] = True
                self.current_event["double_play"] = True
            elif mod == "FINT":
                self.current_event["fan_interference"] = True
            elif mod == "FL":
                self.current_event["foul"] = True
            elif mod == "FO":
                self.current_event["force"] = True
            elif mod == "G":
                self.current_event["ground"] = True
            elif mod == "GDP":
                self.current_event["ground"] = True
                self.current_event["double_play"] = True
            elif mod == "GTP":
                self.current_event["ground"] = True
                self.current_event["triple_play"] = True
            elif mod == "IF":
                self.current_event["infield_fly"] = True
            elif mod == "INT":
                self.current_event["interference"] = True
            elif mod == "IPHR":
                self.current_event["in_the_park_hr"] = True
            elif mod == "L":
                self.current_event["line_drive"] = True
            elif mod == "LDP":
                self.current_event["line_drive"] = True
                self.current_event["double_play"] = True
            elif mod == "LTP":
                self.current_event["line_drive"] = True
                self.current_event["triple_play"] = True
            elif mod == "P":
                self.current_event["pop_fly"] = True
            elif mod == "SF":
                self.current_event["sac_fly"] = True
            elif mod == "SH":
                self.current_event["sac_bunt"] = True
            elif mod == "TP":
                self.current_event["triple_play"] = True

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

    def _process_advance_text(self, adv: str):
        """Process a coded description of runner advancement on the play.

        Args:
            adv: Coded description of all runner advances.

        Returns:
            None.
        """
        if not adv:
            return
        advances = adv.split(";")
        for advance in advances:
            if match := _ADV.match(advance):
                start, success, finish = match.groups()
                start = 0 if start == "B" else int(start)
                success = success == "-"
                finish = 4 if finish == "H" else int(finish)
                self.runner_destinations[start] = finish if success else -1
            else:
                print("WARNING: unable to match advance string:", advance)
