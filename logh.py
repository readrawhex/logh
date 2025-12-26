"""
Script for managing project hours.
"""

import json, os, sys
import argparse
from datetime import datetime


def clock_in(timesheet: list, proj: str, description: list = [], start: str = None):
    """
    Add a clock in time to timesheet

    Params:
        timesheet ([{}]) - list of dictionaries containing timesheet data
        proj (str) - project name for hours
        description ([str]) - list of strings to concat as work description
        start (str) - isoformat date string specifying start-time
    """
    if proj is None:
        raise Exception("no project name was given")
    desc = " ".join(description) if len(description) > 0 else None
    for t in timesheet:
        if t["project"] == proj:
            if t["out"] is None:
                raise Exception(
                    "already clocked in for project '{}' at '{}'".format(
                        proj,
                        datetime.fromisoformat(t["in"]).strftime("%Y-%m-%d %T"),
                    )
                )
            break
    return [
        {
            "in": (
                datetime.fromisoformat(start).isoformat()
                if start
                else datetime.now().isoformat()
            ),
            "out": None,
            "description": desc,
            "project": proj,
        }
    ] + timesheet


def clock_out(
    timesheet: list,
    proj: str,
    description: list = [],
    start: str = None,
    end: str = None,
):
    """
    Add a clock out time to timesheet

    Params:
        timesheet ([{}]) - list of dictionaries containing timesheet data
        proj (str) - project name for hours
        description ([str]) - list of strings to concat as work description
        start (str) - isoformat date string specifying start-time
        end (str) - isoformat date string specifying end-time
    """
    if proj is None:
        raise Exception("no project name was given")
    desc = " ".join(description).strip() if len(description) > 0 else None
    for t in timesheet:
        if t["project"] == proj:
            if t["out"] is not None:
                raise Exception(f"no clock-in specified for project '{proj}'")

            st = (
                datetime.fromisoformat(start)
                if start
                else datetime.fromisoformat(t["in"])
            )
            et = datetime.fromisoformat(end) if end else datetime.now()
            if et <= st:
                raise Exception("end time must be later than start time")
            t["in"] = st.isoformat()
            t["out"] = et.isoformat()

            if desc in [None, [], ""] and t["description"] is None:
                raise Exception("please specify a description of work completed")
            t["description"] = desc if desc else t["description"]
            return timesheet
    raise Exception(f"did not find a clock-in time for project '{proj}'")


def filter_timesheet(
    timesheet, project: str = None, start: str = None, end: str = None
):
    """
    Filter timesheet by project, start datetime, end datetime

    Params:
        timesheet ([{}]) - list of dictionaries containing timesheet data
        project (str) - project name to filter for
        start (str) - isoformat date string specifying start-time filter
        end (str) - isoformat date string specifying end-time filter
    """
    if project is None and start is None and end is None:
        return timesheet
    start_time = datetime.fromisoformat(start) if start else None
    end_time = datetime.fromisoformat(end) if end else None
    filtered = []
    for t in timesheet:
        if (
            (project and t["project"] != project)
            or (start_time and datetime.fromisoformat(t["in"]) < start_time)
            or (end_time and datetime.fromisoformat(t["out"]) > end_time)
        ):
            continue
        filtered = [t] + filtered
    return filtered


def remove_last(timesheet: list, project: str = None):
    """
    Remove the last timesheet entry by optional project filter

    Params:
        timesheet ([{}]) - list of dictionaries containing timesheet data
        project (str) - project name to filter for
    """
    if project is None:
        return timesheet[1:] if len(timesheet) > 1 else []
    for i, t in enumerate(timesheet):
        if t["project"] == project:
            timesheet.pop(i)
            break
    return timesheet


def status(timesheet: list, project: str = None, start: str = None, end: str = None):
    """
    Display the most recent timesheet data for each project in timesheet

    Params:
        timesheet ([{}]) - list of dictionaries containing timesheet data
        project (str) - project name to filter for
        start (str) - isoformat date string specifying start-time filter
        end (str) - isoformat date string specifying end-time filter
    """
    start_time = datetime.fromisoformat(start) if start else None
    end_time = datetime.fromisoformat(end) if end else None
    recents = {}

    if project:
        for t in timesheet:
            if t["project"] == project:
                if project not in recents.keys():
                    recents[t["project"]] = [t]
                else:
                    recents[t["project"]].append(t)
        if len(recents) == 0:
            raise Exception("no data for project '{}' found")
        recents = sorted(recents[project], key=lambda x: x["in"])
    else:
        for t in timesheet:
            if (
                (t["project"] not in recents.keys())
                and (start_time is None or start_time <= t["in"])
                and (end_time is None or t["out"] is None or end_time >= t["out"])
            ):
                recents[t["project"]] = t
        if len(recents) == 0:
            raise Exception("no data for project '{}' found")
        recents = sorted(recents.values(), key=lambda x: x["in"])

    for r in recents:
        print(
            "{:<20}: {} {}".format(
                r["project"],
                datetime.fromisoformat(r["in"]).strftime("%Y-%m-%d %T"),
                (
                    "- " + datetime.fromisoformat(r["out"]).strftime("%Y-%m-%d %T")
                    if r["out"]
                    else "<- clocked in"
                ),
            )
        )
        if r["description"] not in [None, ""]:
            print("└──{}".format(r["description"]))



def main():
    try:
        parser = argparse.ArgumentParser(description="log working hours")
        parser.add_argument(
            "-i",
            "--clock-in",
            action="store_true",
            help="mark current time as clock start",
        )
        parser.add_argument(
            "-o",
            "--clock-out",
            action="store_true",
            help="mark current time as clock end",
        )
        parser.add_argument(
            "-e", "--export", type=str, help="export timesheet data to file"
        )
        parser.add_argument(
            "-d",
            "--delete-clock-in",
            action="store_true",
            help="delete the most recent clock-in / hours",
        )
        parser.add_argument(
            "--start-time", type=str, help="specify a specific starting time"
        )
        parser.add_argument(
            "--end-time", type=str, help="specify a speicific ending time"
        )
        parser.add_argument(
            "project", nargs="?", default=None, help="project being worked on"
        )
        parser.add_argument(
            "description", nargs="*", help="description of tasks completed"
        )
        args = parser.parse_args()

        home_dir = os.environ.get("HOME", "")
        timesheet_path = os.environ.get("JSON_TIMESHEET", f"{home_dir}/timesheet.json")
        try:
            with open(timesheet_path, "r") as f:
                timesheet = json.load(f)
        except FileNotFoundError:
            print(
                f"warning: '{timesheet_path}' not found, will create new file on data write"
            )
            timesheet = []

        if args.export:
            with open(args.export, "w") as f:
                data = filter_timesheet(
                    timesheet,
                    args.project,
                    start=args.start_time,
                    end=args.end_time,
                )
                json.dump(data, f)
            return
        elif args.clock_in:
            timesheet = clock_in(
                timesheet, args.project, args.description, start=args.start_time
            )
        elif args.clock_out:
            timesheet = clock_out(
                timesheet,
                args.project,
                args.description,
                start=args.start_time,
                end=args.end_time,
            )
        elif args.delete_clock_in:
            timesheet = remove_last(timesheet, args.project)
        else:
            status(timesheet, args.project, start=args.start_time, end=args.end_time)
            return

        with open(timesheet_path, "w") as f:
            json.dump(timesheet, f)
    except Exception as e:
        raise(e)
        parser.print_help(sys.stderr)
        print(f"\nFAILED: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
