# SAS Log Checker CLI (Command line interface [CMD])

Published: January 29, 2026

Check a folder of SAS logs for ERROR, WARNING, and NOTE message prefixes from
Linux, macOS, or Windows. Requires Python 3.8+ and only the standard library.
No SAS installation is required. Files are read locally and are never uploaded.

Download `sas_log_check.py` from this repository using GitHub's **Download raw file** option, or download and extract the repository ZIP. From the folder containing the script:

```sh
python3 sas_log_check.py /path/to/logs
python3 sas_log_check.py "/path/with spaces/logs" --recursive --fail-on warning
python3 sas_log_check.py /path/to/logs -r --format json > report.json
python3 sas_log_check.py /path/to/logs --encoding latin-1
python3 sas_log_check.py --help
```

On Windows, replace `python3` with `py -3`. Omitting the folder scans the current
directory. All `.log` extensions are accepted regardless of case. Subfolders
are included only with `-r` / `--recursive`; directory symlinks are not followed.

Text output includes file paths, line numbers, message severity, and a summary.
JSON includes `files_scanned`, `counts`, `findings`, and `scan_errors`. Reports
include all three message types regardless of the selected failure threshold.

The default encoding is UTF-8 with optional BOM. Choose the log's actual encoding
with `--encoding` if needed. Decoding and file access failures are reported and
produce exit code 2, so an incomplete scan cannot pass silently.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Scan completed, no findings at or above the selected threshold |
| 1 | Findings reached the selected threshold |
| 2 | Usage or scan error, including missing folder, no logs, unreadable files, or decoding failure |

`--fail-on error` (default) fails for errors. `--fail-on warning` fails for
errors or warnings. `--fail-on note` fails for errors, warnings, or notes.
`--fail-on none` reports findings without failing, unless the scan itself fails.
Use the exit code immediately after the command in automation. In Linux shells,
`echo $?` shows the previous command's exit code.

## Scope

Recognizes leading whitespace and case-insensitive `ERROR:`, `WARNING:`,
`NOTE:`, and numbered prefixes such as `ERROR 180-322:`. Source lines such as
`123 put "ERROR: sample";` are excluded. Routine SAS notes are included.
Counts represent matching message header lines, not continuation lines or unique
root causes. The tool expects English SAS prefixes; localized messages and
custom messages without those prefixes are outside its scope. Review the original
logs for full context. This is a log scanner, not a program correctness validator.


## Files in this repository

Only `sas_log_check.py` is required to run the tool. You must also have Python
3.8 or later installed and your own SAS `.log` files to scan. No `pip install`,
`requirements.txt`, SAS software, or internet access is needed to run it.

- `README.md`: setup, usage, options, exit codes, and limitations.
- `examples/logs/sample.log`: synthetic log for trying the tool; no real data.
- `examples/EXPECTED_OUTPUT.txt`: expected result for the sample command.
- `tests/test_sas_log_check.py`: optional automated tests for maintainers.
- `.gitignore`: excludes Python cache files and generated reports.

## Try the included sample

From the repository root:

```sh
python3 sas_log_check.py examples/logs
```

Expected counts: **1 error, 1 warning, 2 notes** from one log file. This example
intentionally returns exit code **1** because it contains an error. See
`examples/EXPECTED_OUTPUT.txt` for the full output. The sample is illustrative
text, not a log from an actual SAS run.

To report the sample without failing for findings:

```sh
python3 sas_log_check.py examples/logs --fail-on none
```

To run the optional tests from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

The tests also use only Python's standard library. On Windows, use `py -3`
instead of `python3` for these commands.
