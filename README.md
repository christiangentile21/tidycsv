# tidycsv

[![CI](https://github.com/christiangentile21/tidycsv/actions/workflows/ci.yml/badge.svg)](https://github.com/christiangentile21/tidycsv/actions/workflows/ci.yml)

A small command-line tool to inspect, clean, and summarize CSV files.
Built with Python, pandas, and argparse.

- `summary` shows rows, columns, types, missing values, and numeric stats.
- `clean` writes a copy with duplicates removed and/or missing values filled.
- `check` exits with a non-zero code if the data has quality issues, so it
  can guard a script or CI job.

## Install

Requires Python 3.11+.

```
git clone https://github.com/christiangentile21/tidycsv.git
cd tidycsv
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
pip install -e ".[dev]"
```

This installs a `tidycsv` command. `python -m tidycsv` works the same way,
which is useful if your system blocks newly created executables.

## Usage

```
tidycsv summary FILE [--delimiter CHAR]
tidycsv clean FILE -o OUTPUT [--delimiter CHAR] [--drop-duplicates] [--fill-missing {mean,median,mode,drop}]
tidycsv check FILE [--delimiter CHAR]
```

`--delimiter` sets the column separator (default `,`). It must be a single
character, such as `;` or `|`; use `tab` (or `\t`) for tab-separated files.
`clean` writes its output with the same delimiter as the input.

`clean` needs at least one of `--drop-duplicates` or `--fill-missing`.
When both are given, duplicates are removed first so they don't skew the
fill values.

| `--fill-missing` | What it does |
|---|---|
| `mean` | Fills numeric columns with the column mean. Other columns are left as is. |
| `median` | Same, using the median. |
| `mode` | Fills every column (numeric or text) with its most common value. |
| `drop` | Removes columns that are entirely missing, then every row that still has a missing value. |

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Success (for `check`: no issues found) |
| 1 | `check` found duplicates or missing values |
| 2 | Error: bad arguments, or a file that can't be read or written |

## Examples

All examples use [examples/sample.csv](examples/sample.csv), a four-row
synthetic file with one duplicate row and two missing values.

```
$ tidycsv summary examples/sample.csv
Rows: 4
Columns: 4

Column  Type        Missing
name    str         0
city    str         0
age     float64     1
score   float64     1

Column         Min         Max        Mean
age             30          41       33.67
score           72        88.5          83
```

```
$ tidycsv check examples/sample.csv
Issues found:
  - 1 duplicate row(s)
  - missing values in: age (1), score (1)
$ echo $?
1
```

```
$ tidycsv clean examples/sample.csv --drop-duplicates --fill-missing median -o clean.csv
Removed 1 duplicate row(s).
Filled 2 missing value(s) using median.
Wrote 3 row(s) to clean.csv

$ tidycsv check clean.csv
No issues found.
```

## Running the tests

```
pytest
```

Tests use tiny synthetic CSVs written to pytest's temporary folders.

## Limitations

- Only UTF-8 files are supported, and the delimiter must be one character.
  It isn't detected automatically: with the wrong `--delimiter`, each line
  loads as a single column.
- In a file with only one column, an empty value looks like a blank line,
  and blank lines are skipped. Such a value is not counted as missing.
- The whole file is loaded into memory, so very large files may be slow.
- An integer column with missing values is read as floats, because pandas
  stores missing numbers as NaN (a float). After cleaning, `30` is written
  as `30.0`.
- Duplicates must match exactly in every column. `"Rome"` and `"rome "`
  count as different values.
- `mean` and `median` skip non-numeric columns. Numbers stored as text
  (for example `"1,000"`) count as text.
- With `mean`, `median`, or `mode`, a column that is entirely missing can't
  be filled, so it is left unchanged and `clean` lists it. With `drop`, the
  column is removed instead (and reported), so it can't wipe out every row.
- When `mode` finds a tie, the smallest value is used.
- Text column types show as `str` with pandas 3 and `object` with pandas 2.

## Roadmap

1. Outlier flagging in `summary` and `check` using the IQR rule.
2. Column renaming in `clean` (for example `--rename old=new`).
3. `--json` output for `summary` and `check`, so other tools can read the
   results.

## License

MIT. See [LICENSE](LICENSE).
