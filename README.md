# tidycsv

A small command-line tool to inspect, clean, and summarize CSV files.

> Work in progress. Commands are being added one at a time.

## Planned commands

```
tidycsv summary data.csv
tidycsv clean data.csv --drop-duplicates --fill-missing median -o out.csv
tidycsv check data.csv
```

## Development

```
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e ".[dev]"
pytest
```

## License

MIT. See [LICENSE](LICENSE).
