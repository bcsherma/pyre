# -*- coding: utf-8 -*-
"""String processing helpers for pyre."""

import re
import typing
import sys

_DP = re.compile(r"([\d]+)\(([123B])\)([\d]+)(?:\(([123B])\))?")
_OUT = re.compile(r"([\d]+)")
_ERR = re.compile(r"(FL)?E(\d)")
_FC = re.compile(r"FC[\d]")
_HIT = re.compile(r"([SDT])([\d]+|(?:GR))?$")
_HR = re.compile(r"(HR?)(\d?)$")
_KW = re.compile(r"(K|W|(?:IW?))(?:\+(.*))?")
_SB = re.compile(r"SB([23H])")
_PO = re.compile(r"PO([123])\((?:(\d+)|E(\d))(?:/TH)?\)")
_CS = re.compile(r"(?:PO)?CS([23H])\((\d+)(?:E(\d))?\)")
# TODO: Parse errors specified in the advance parameters
_ADV = re.compile(r"([123B])([-X])([123H])(?:\(.*\))*")


def split_description(description: str) -> typing.Tuple[str, str, str]:
    """Split a retrosheet event description into it's components.

    The play description is made up of three sections:
        1. A description of basic play that occurred.
        2. A series of flags conveying additional information.
        3. A description of all runner advances in the play.

    Args:
        description: A description of the play.

    Returns:
        event: Description of the basic event.
        mod: Auxiliary information about the play.
        adv: Description of runner advances on the play.
    """
    start_mod = description.find("/")
    if 0 < description.find("(") < start_mod < description.find(")"):
        next_slash = description[start_mod + 1 :].find("/")
        if next_slash < 0:
            start_mod = -1
        else:
            start_mod += next_slash + 1
    if start_mod < 0:
        start_mod = len(description)
    start_adv = description.rfind(".")
    if start_adv < 0:
        start_adv = len(description)
    event = description[: min(start_mod, start_adv)].rstrip("/.")
    mod = description[start_mod:start_adv].strip("/.")
    adv = description[start_adv:].lstrip(".")
    return event, mod, adv


def parse_event(event_text: str) -> typing.Tuple[dict, set, list]:
    """Parse coded event text into a dictionary describing the event.

    This function is very long and checks the event_text against a series of
    regular expressions in order to extract its meaning.

    Args:
        event_text: A description of the basic play occurring.

    Returns:
        info: Output fields derived from the description.
        errors: A list of fielder positions with errors charged on the play.
        runner_destinations: Destination base of each runner on the play.
    """

    # These are, in order, the return values of this function.
    info = dict()
    errors = set()
    runner_destinations: typing.List[int] = [0] * 4

    # This block catches the no event.
    if event_text == "NP":
        return info, errors, runner_destinations

    # This block processes double play events.
    if match := _DP.match(event_text):
        for runner in match.group(2), match.group(4):
            if runner == "B" or runner is None:
                runner = 0
            runner = int(runner)
            runner_destinations[runner] = -1
        return info, errors, runner_destinations

    # This block processes events where the batter is out.
    if _OUT.match(event_text):
        runner_destinations[0] = -1
        return info, errors, runner_destinations

    # This block processes events where an error occurred.
    if match := _ERR.match(event_text):
        runner_destinations[0] = 1
        if match.group(1) is not None:
            info["fly"] = True
            info["foul"] = True
        errors.add(match.group(2))
        return info, errors, runner_destinations

    # This block processes hits.
    if match := _HIT.match(event_text):
        hit_code = match.group(1)
        info["hit_code"] = hit_code
        dest = {"S": 1, "D": 2, "T": 3}[hit_code]
        runner_destinations[0] = dest
        return info, errors, runner_destinations

    # This block processes fielder's choice events
    if _FC.match(event_text):
        runner_destinations[0] = 1
        return info, errors, runner_destinations

    # This block processes home run events.
    if _HR.match(event_text):
        info["hit_code"] = "H"
        runner_destinations[0] = 4
        return info, errors, runner_destinations

    # This block processes catcher interference events.
    if event_text == "C":
        info["catcher_interference"] = True
        runner_destinations[0] = 1
        return info, errors, runner_destinations

    # This block processes hit by pitch events
    if event_text == "HP":
        info["hit_by_pitch"] = True
        runner_destinations[0] = 1
        return info, errors, runner_destinations

    # This block processes strikeout and walk events.
    if match := _KW.match(event_text):
        runner_destinations[0] = -1 if match.group(1) == "K" else 1
        if match.group(2) is not None:
            info_2, err_2, rd_2 = parse_event(match.group(2))
            info.update(info_2)
            errors = errors | err_2
            runner_destinations = [
                r2 if r2 else r1 for r1, r2 in zip(runner_destinations, rd_2)
            ]
        return info, errors, runner_destinations

    # This block processes stolen bases.
    if match := _SB.match(event_text):
        base = match.group(1)
        base = 4 if base == "H" else int(base)
        runner_destinations[base - 1] = base
        return info, errors, runner_destinations

    # This block processes caught stealing events.
    if match := _CS.match(event_text):
        base = match.group(1)
        base = 4 if base == "H" else int(base)
        runner_destinations[base - 1] = -1
        if match.group(3) is not None:
            errors.add(match.group(3))
        return info, errors, runner_destinations

    # This block processes pitch out events.
    if match := _PO.match(event_text):
        base = int(match.group(1))
        if match.group(3) is None:
            runner_destinations[base] = -1
        else:
            errors.add(match.group(3))
        return info, errors, runner_destinations

    # This block processes runner events where the result is given in the
    # advancement string.
    if event_text in ["PB", "BK", "WP", "DI", "OA"]:
        code = {
            "PB": "passed_ball",
            "BK": "balk",
            "WP": "wild_pitch",
            "DI": "defensive_indifference",
            "OA": "unknown",
        }.get(event_text)
        info[code] = True
        return info, errors, runner_destinations

    print("WARNING: Unrecognized event", event_text, file=sys.stderr)
    return info, errors, runner_destinations


def parse_modifiers(modifiers: str) -> typing.Tuple[dict, set]:
    """Process coded description of event modifiers.

    Args:
        modifiers: A coded string describing all event modifiers.

    Returns:
        modifier_dict: A tabular representation of the event modifiers.
        errors: A set of player positions charged with errors.
    """
    if not modifiers:
        return dict(), set()
    mod_list = modifiers.split("/")
    modifier_dict = {}
    errors = set()
    for mod in mod_list:
        if mod == "AP":
            modifier_dict["appealed"] = True
        elif mod == "BP":
            modifier_dict["bunt"] = True
            modifier_dict["fly"] = True
        elif mod == "GP":
            modifier_dict["bunt"] = True
        elif mod == "BGDP":
            modifier_dict["bunt"] = True
            modifier_dict["double_play"] = True
        elif mod == "BINT":
            modifier_dict["batter_interference"] = True
        elif mod == "BL":
            modifier_dict["bunt"] = True
        elif mod == "BPDP":
            modifier_dict["bunt"] = True
            modifier_dict["fly"] = True
            modifier_dict["double_play"] = True
        elif mod == "BR":
            modifier_dict["runner_hit"] = True
        elif mod == "C":
            modifier_dict["called_third"] = True
        elif mod == "DP":
            modifier_dict["double_play"] = True
        elif match := _ERR.match(mod):
            errors.add(match.group(2))
        elif mod == "F":
            modifier_dict["fly"] = True
        elif mod == "FDP":
            modifier_dict["fly"] = True
            modifier_dict["double_play"] = True
        elif mod == "FINT":
            modifier_dict["fan_interference"] = True
        elif mod == "FL":
            modifier_dict["foul"] = True
        elif mod == "FO":
            modifier_dict["force"] = True
        elif mod == "G":
            modifier_dict["ground"] = True
        elif mod == "GDP":
            modifier_dict["ground"] = True
            modifier_dict["double_play"] = True
        elif mod == "GTP":
            modifier_dict["ground"] = True
            modifier_dict["triple_play"] = True
        elif mod == "IF":
            modifier_dict["infield_fly"] = True
        elif mod == "INT":
            modifier_dict["interference"] = True
        elif mod == "IPHR":
            modifier_dict["in_the_park_hr"] = True
        elif mod == "L":
            modifier_dict["line_drive"] = True
        elif mod == "LDP":
            modifier_dict["line_drive"] = True
            modifier_dict["double_play"] = True
        elif mod == "LTP":
            modifier_dict["line_drive"] = True
            modifier_dict["triple_play"] = True
        elif mod == "P":
            modifier_dict["pop_fly"] = True
        elif mod == "SF":
            modifier_dict["sac_fly"] = True
        elif mod == "SH":
            modifier_dict["sac_bunt"] = True
        elif mod == "TP":
            modifier_dict["triple_play"] = True
    return modifier_dict, errors


def parse_advance(advance: str):
    """Process a coded description of runner advancement on the play.

    Args:
        advance: Coded description of all runner advances.

    Returns:
        destinations: A list of 4 numbers describing the destination of each
            runner.
    """
    destinations = [0] * 4
    if not advance:
        return destinations
    advances = advance.split(";")
    for advance in advances:
        if match := _ADV.match(advance):
            start, success, finish = match.groups()
            start_base = 0 if start == "B" else int(start)
            success = success == "-"
            finish = 4 if finish == "H" else int(finish)
            destinations[start_base] = finish if success else -1
        else:
            print("WARNING: unable to match advance string:", advance, file=sys.stderr)
    return destinations
