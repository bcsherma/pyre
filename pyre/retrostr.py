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
_ADV = re.compile(r"([123B])([-X])([123H])(\(.*\))*")


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
    match = _DP.match(event_text)
    if match:
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
    match = _ERR.match(event_text)
    if match:
        runner_destinations[0] = 1
        if match.group(1) is not None:
            info["FOUL_FL"] = 1
        errors.add(match.group(2))
        return info, errors, runner_destinations

    # This block processes hits.
    match = _HIT.match(event_text)
    if match:
        hit = match.group(1)
        code = {"S": 1, "D": 2, "T": 3}[hit]
        info["HIT_FL"] = code
        runner_destinations[0] = code
        return info, errors, runner_destinations

    # This block processes fielder's choice events
    if _FC.match(event_text):
        runner_destinations[0] = 1
        return info, errors, runner_destinations

    # This block processes home run events.
    if _HR.match(event_text):
        info["HIT_FL"] = 4
        runner_destinations[0] = 4
        return info, errors, runner_destinations

    # This block processes catcher interference events.
    if event_text == "C":
        # TODO: Record interference in event type
        runner_destinations[0] = 1
        return info, errors, runner_destinations

    # This block processes hit by pitch events
    if event_text == "HP":
        # TODO: Record hit by pitch in event type
        runner_destinations[0] = 1
        return info, errors, runner_destinations

    # This block processes strikeout and walk events.
    match = _KW.match(event_text)
    if match:
        if match.group(1) == "K":
            runner_destinations[0] = -1
            # TODO: Record strikeout in event type
        else:
            runner_destinations[0] = 1
            # TODO: Record walk in event type
        if match.group(2) is not None:
            info_2, err_2, rd_2 = parse_event(match.group(2))
            info.update(info_2)
            errors = errors | err_2
            runner_destinations = [
                r2 if r2 else r1 for r1, r2 in zip(runner_destinations, rd_2)
            ]
        return info, errors, runner_destinations

    # This block processes stolen bases.
    match = _SB.match(event_text)
    if match:
        base = match.group(1)
        base = 4 if base == "H" else int(base)
        runner_destinations[base - 1] = base
        return info, errors, runner_destinations

    # This block processes caught stealing events.
    match = _CS.match(event_text)
    if match:
        base = match.group(1)
        base = 4 if base == "H" else int(base)
        runner_destinations[base - 1] = -1
        if match.group(3) is not None:
            errors.add(match.group(3))
        return info, errors, runner_destinations

    # This block processes pitch out events.
    match = _PO.match(event_text)
    if match:
        base = int(match.group(1))
        if match.group(3) is None:
            runner_destinations[base] = -1
        else:
            errors.add(match.group(3))
        return info, errors, runner_destinations

    if event_text == "WP":  # Wild pitch
        info["WP_FL"] = 1
        return info, errors, runner_destinations

    if event_text == "PB":  # Passed ball
        info["PB_FL"] = 1
        return info, errors, runner_destinations

    # TODO: Process balk, unknown, and defensive indifference in event code
    # Codes are BK, DI, OA
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
        if mod == "BP":
            modifier_dict["BUNT_FL"] = 0
            modifier_dict["BATTEDBALL_CD"] = "F"
        elif mod == "GP":
            modifier_dict["BUNT_FL"] = 1
        elif mod == "BGDP":
            modifier_dict["BUNT_FL"] = 1
            modifier_dict["DP_FL"] = 1
        elif mod == "BL":
            modifier_dict["BUNT_FL"] = 1
        elif mod == "BPDP":
            modifier_dict["BUNT_FL"] = 1
            modifier_dict["BATTEDBALL_CD"] = "F"
            modifier_dict["BATTEDBALL_CD"] = "F"
            modifier_dict["DP_FL"] = 1
        elif mod == "DP":
            modifier_dict["DP_FL"] = 1
        elif _ERR.match(mod):
            match = _ERR.match(mod)
            errors.add(match.group(2))
        elif mod == "F":
            modifier_dict["BATTEDBALL_CD"] = "F"
        elif mod == "FDP":
            modifier_dict["BATTEDBALL_CD"] = "F"
            modifier_dict["DP_FL"] = 1
        elif mod == "FINT":
            # This is code for fan interference, which is not expressed in
            # the output of BEVENT or cwevent
            pass
        elif mod == "FL":
            modifier_dict["FOUL_FL"] = 1
        elif mod == "G":
            modifier_dict["BATTEDBALL_CD"] = "G"
        elif mod == "GDP":
            modifier_dict["BATTEDBALL_CD"] = "G"
            modifier_dict["DP_FL"] = 1
        elif mod == "GTP":
            modifier_dict["BATTEDBALL_CD"] = "G"
            modifier_dict["TP_FL"] = 1
        elif mod == "IF":
            modifier_dict["BATTEDBALL_CD"] = "F"
        elif mod == "INT":
            # TODO: This should be reflected in the event code.
            pass
        elif mod == "L":
            modifier_dict["BATTEDBALL_CD"] = "L"
        elif mod == "LDP":
            modifier_dict["BATTEDBALL_CD"] = "L"
            modifier_dict["DP_FL"] = 1
        elif mod == "LTP":
            modifier_dict["BATTEDBALL_CD"] = "L"
            modifier_dict["TP_FL"] = 1
        elif mod == "P":
            modifier_dict["BATTEDBALL_CD"] = "F"
        elif mod == "SF":
            modifier_dict["SF_FL"] = 1
        elif mod == "SH":
            modifier_dict["BUNT_FL"] = 1
        elif mod == "TP":
            modifier_dict["TP_FL"] = 1
    return modifier_dict, errors


def parse_advance(advance: str) -> typing.Tuple[dict, set, list]:
    """Process a coded description of runner advancement on the play.

    Args:
        advance: Coded description of all runner advances.

    Returns:
        info: Output fields derived from the description.
        errors: A list of fielder positions with errors charged on the play.
        destinations: Destination base of each runner on the play.
    """
    # These are, in order, the return values of this function.
    info = dict()
    errors = set()
    destinations: typing.List[int] = [0] * 4
    if not advance:
        return info, errors, destinations
    advances = advance.split(";")
    for advance in advances:
        match = _ADV.match(advance)
        if match:
            start, success, finish, aux = match.groups()
            start_base = 0 if start == "B" else int(start)
            success = success == "-"
            finish = 4 if finish == "H" else int(finish)
            destinations[start_base] = finish if success else -1
            if aux is not None:
                for match in re.findall(
                    r"\((?:(\d+)|(UR|NR|/TH)|(?:\d*E(\d+)))(/TH)?\)", aux
                ):
                    play, mod, err, th_mod = match
                    if err:
                        errors.add(err)
                        destinations[start_base] = finish  # Error negates out
                    if th_mod:
                        pass  # TODO: diff. between fielding/throwing err
                    if play:
                        pass  # TODO: record putout
                    if mod:
                        pass  # TODO: recognize unearned and no-rbi runs
        else:
            print("WARNING: unable to match advance string:", advance, file=sys.stderr)
    return info, errors, destinations
