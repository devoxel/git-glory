#!/bin/env python3
"""git-glory

git-glory walks your git and counts the lines of code done by contributers
then prints them out all pretty like.

it's something i whipped up for a quick one off, may improve if im bothered.
"""

import os
import sys
import re
import os.path
import subprocess
from collections import defaultdict

import texttable

# TODO: This should be a flag
EXCLUDE_SET = set([".git", "__pycache__", "build_out",
                   ".circleci", "node_modules"])
FNULL = open(os.devnull, 'w')
email_re = re.compile(r"<([\w\.-]+@[\w\.-]+)>")


def exclude(directory):
    for e in EXCLUDE_SET:
        if e in directory:
            return True
    return False


def files(top):
    files = set()
    for dirpath, dirnames, filenames in os.walk(top):
        if exclude(dirpath):
            continue
        for f in filenames:
            files.add((dirpath, f))
    return files


def is_tracked(fpath):
    cmd = f"git ls-files --error-unmatch {fpath}"
    o = subprocess.run(cmd, shell=True, stdout=FNULL, stderr=FNULL)
    return o.returncode is 0


def blame(fpath):
    cmd = f"git blame --show-email -w {fpath}"
    o = subprocess.check_output(cmd, shell=True, stderr=FNULL)
    m = email_re.findall(str(o))

    loc = defaultdict(int)
    for email in m:
        loc[email] += 1
    return loc


def cloc(files):
    """
    cloc returns the counted lines of code by author and file type given a set of files

    expect the structure to look like this:
    { git_email: { filetype: loc, ... }, ... }
    """
    m = {}
    for dirpath, filename in files:
        filetype = filename.split(".")[-1]
        fpath = os.path.join(dirpath, filename)
        if not is_tracked(fpath):
            continue

        loc = blame(fpath)
        for user in loc:
            if user not in m:
                m[user] = defaultdict(int)

            m[user][filetype] += loc[user]
    return m


def output(loc):
    table = texttable.Texttable(max_width=120)

    filetypes = set()
    for floc in loc.values():
        for f in floc.keys():
            filetypes.add(f)

    header = ["email"] + list(filetypes)
    table.header(header)

    fheaderindex = {}
    for i in range(1, len(header)):
        fheaderindex[header[i]] = i

    for u in loc:
        uloc = loc[u]
        row = [0 for i in range(len(header))]
        row[0] = u.split("@")[0]
        for ftype in uloc:
            row[fheaderindex[ftype]] = uloc[ftype]
        table.add_row(row)

    print(table.draw())


if __name__ == "__main__":
    f = files("/home/apd/go/src/rabble")
    c = cloc(f)
    output(c)
