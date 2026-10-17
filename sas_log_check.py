#!/usr/bin/env python3
"""Check SAS logs using Python 3.8+ and the standard library only."""

import argparse
import json
import os
from pathlib import Path
import re
import sys


# Anchor to SAS message prefixes so source statements and quoted text do not match.
MESSAGE = re.compile(r"^\s*(ERROR|WARNING|NOTE)(?:\s+\d+(?:-\d+)?)?\s*:\s*(.*)", re.IGNORECASE)


def scan(folder, recursive=False, encoding="utf-8-sig"):
    findings = []
    failures = []
    files = []

    def walk_error(error):
        failures.append(str(error))

    for root, directories, names in os.walk(folder, onerror=walk_error):
        directories.sort()
        if not recursive:
            directories[:] = []
        for name in sorted(names):
            path = Path(root) / name
            if path.suffix.lower() != ".log":
                continue
            files.append(str(path))
            try:
                with path.open(encoding=encoding, errors="strict") as log:
                    for number, line in enumerate(log, 1):
                        match = MESSAGE.match(line)
                        if match:
                            findings.append({
                                "file": str(path), "line": number,
                                "severity": match[1].upper(), "message": match[2].rstrip(),
                            })
            except (OSError, UnicodeError) as error:
                failures.append("{}: {}".format(path, error))
    return {
        "files_scanned": len(files),
        "counts": {level: sum(f["severity"] == level for f in findings)
                   for level in ("ERROR", "WARNING", "NOTE")},
        "findings": findings,
        "scan_errors": failures,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check a folder of SAS .log files for errors, warnings, and notes.")
    parser.add_argument("folder", nargs="?", default=".", help="Folder to scan (default: current folder)")
    parser.add_argument("-r", "--recursive", action="store_true", help="Include subfolders; do not follow directory symlinks")
    parser.add_argument("--encoding", default="utf-8-sig", help="Log encoding, e.g. utf-8-sig or latin-1")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--fail-on", choices=("error", "warning", "note", "none"), default="error",
                        help="Exit 1 at this severity or higher (default: error)")
    args = parser.parse_args(argv)
    folder = Path(args.folder)
    if not folder.is_dir():
        parser.error("Folder does not exist or is not a directory: {}".format(folder))
    try:
        report = scan(folder, args.recursive, args.encoding)
    except LookupError:
        parser.error("Unknown encoding: {}".format(args.encoding))
    if not report["files_scanned"]:
        report["scan_errors"].append("No .log files found in the selected folder(s).")
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        for finding in report["findings"]:
            print("{file}:{line}: {severity}: {message}".format(**finding))
        print("Scanned {} log file(s): {} error(s), {} warning(s), {} note(s).".format(
            report["files_scanned"], report["counts"]["ERROR"],
            report["counts"]["WARNING"], report["counts"]["NOTE"]))
        for error in report["scan_errors"]:
            print("Scan error: {}".format(error), file=sys.stderr)
    if report["scan_errors"]:
        return 2
    levels = {"error": ("ERROR",), "warning": ("ERROR", "WARNING"),
              "note": ("ERROR", "WARNING", "NOTE"), "none": ()}
    return int(any(report["counts"][level] for level in levels[args.fail_on]))


if __name__ == "__main__":
    sys.exit(main())
