#! /usr/bin/env python3

# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2020 Arm Ltd

import requests
import json
import collections
import datetime

def call(method, **args):
    BASE = "https://bugzilla.yoctoproject.org/jsonrpc.cgi"
    params = {'method': method, 'params': json.dumps([args,])}
    r = requests.get(BASE, params=params)
    return r.json()

# TODO: harvest bug IDs from Bug.search and then call a batch Bug.history once

def get_resolved_date(bugid):
    result = call("Bug.history", ids=[bugid])
    history = result["result"]["bugs"][0]["history"]
    for event in reversed(history):
        for change in event["changes"]:
            if change["field_name"] == "bug_status" and change["added"] == "RESOLVED":
                return event["when"]
    return None

# added, removed
bins = collections.defaultdict(lambda: [0,0])

# Make a bin from a date string
def week_from_date(s):
    # fromisoformat() doesn't like the Z at the end
    dt = datetime.datetime.fromisoformat(s[:-1])
    dt = dt.date()
    # Google Sheets doesn't handle year-week
    #year, week, day = dt.date().isocalendar()
    #return f"{year}-{week:02}"
    dt -= datetime.timedelta(days=dt.isoweekday() - 1)
    return dt.isoformat()

result = call("Bug.search", whiteboard="AB-INT")
for bug in result["result"]["bugs"]:
    week = week_from_date(bug['creation_time'])
    bins[week][0] += 1

    if not bug["is_open"]:
        week = week_from_date(get_resolved_date(bug["id"]))
        bins[week][1] += 1

count = 0
print("Date\tAdded\tRemoved\tCount")
for week in sorted(bins):
    added, removed = bins[week]
    count += added - removed
    print(f"{week}\t{added}\t{removed}\t{count}")
